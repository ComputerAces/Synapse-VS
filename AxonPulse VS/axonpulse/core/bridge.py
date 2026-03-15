import multiprocessing
import time
import msgpack
import datetime
import zlib
from enum import Enum
from multiprocessing import shared_memory
from axonpulse.utils.logger import setup_logger
from axonpulse.core.engine.services import ConnectionPoolManager
from axonpulse.utils.shm_tracker import SHMTracker

logger = setup_logger("AxonPulseBridge")

# Performance Cache for msgpack_decode
_types_module = None

def msgpack_encode(obj):
    if isinstance(obj, Enum):
        return {'__enum__': str(obj.__class__.__name__), 'value': obj.value}
    if isinstance(obj, datetime.datetime):
        return {'__datetime__': obj.isoformat()}
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if hasattr(obj, '__dict__'):
        return {'__object__': obj.__class__.__name__, 'state': dict(obj.__dict__)}
    return str(obj)

def msgpack_decode(obj):
    global _types_module
    if '__enum__' in obj:
        enum_name = obj['__enum__']
        if _types_module is None:
            import axonpulse.core.types as types_module
            _types_module = types_module
        
        if hasattr(_types_module, enum_name):
            enum_class = getattr(_types_module, enum_name)
            return enum_class(obj['value'])
        return obj['value']
    if '__datetime__' in obj:
        return datetime.datetime.fromisoformat(obj['__datetime__'])
    if '__object__' in obj:
        return obj['state']
    return obj


class AxonPulseBridge:
    """
    The Bridge acts as the middleware for Inter-Process Communication (IPC).
    It manages shared variables, locks, and Zero-Copy Shared Memory for large data.
    """
    def __init__(self, manager, system_state=None, data_state=None):
        self.manager = manager # Store for reuse by child engines
        
        # 1. System State (Shared across whole process tree for hardware sync)
        if system_state:
            # [RWLock Upgrade] Support both legacy and new lock structures
            self._writer_locks = system_state.get("writer_locks", system_state.get("locks"))
            self._reader_locks = system_state.get("reader_locks")
            self._reader_counts = system_state.get("reader_counts")
            
            self._provider_locks = system_state["provider_locks"]
            self._identities = system_state["identities"]
            self._hijack_registry = system_state["hijack_registry"]
            self.root_registry = system_state.get("root_registry") # Inherit root from parent
        else:
            self._writer_locks = manager.list([manager.RLock() for _ in range(256)])
            self._reader_locks = manager.list([manager.Lock() for _ in range(256)])
            self._reader_counts = manager.list([0 for _ in range(256)])
            
            self._provider_locks = manager.list([manager.RLock() for _ in range(128)])
            self._identities = manager.dict()
            self._hijack_registry = manager.dict()
            self.root_registry = None # Will be set to self._variables_registry below

        # 2. Data State (Usually isolated per SubGraph instance to avoid collisions)
        if data_state:
            self._variables_registry = data_state["variables_registry"]
            self._lock_owners = data_state["lock_owners"]
        else:
            self._variables_registry = manager.dict()
            self._lock_owners = manager.dict()
        
        # If we are the root, our own registry is the root registry
        if self.root_registry is None:
            self.root_registry = self._variables_registry

        # [NEW] Default scoping for collision-safe variable names
        self.default_scope = "Global"
        
        # Local Process State (per-instance, per-process)
        self._local_cache = {} # key -> (obj, version)
        self._local_objects = {} # [NEW] Non-picklable live objects (Browser handles, etc.)
        
        # [NEW] Centralized Connection Pooling for network sockets (Phase 2)
        self.pool_manager = ConnectionPoolManager()
        
        # [WINDOWS PERSISTENCE] Persistent handles to SHM blocks
        # Only the "Master" process (Engine) needs to fill this.
        self._pinned_shm = {} # shm_name -> SharedMemory object
        self._shm_dirty = False # [OPTIMIZATION] Flag to skip pin_all if no new blocks

    def get_system_state(self):
        """Returns only the hardware locks and system registries."""
        return {
            "writer_locks": self._writer_locks,
            "reader_locks": self._reader_locks,
            "reader_counts": self._reader_counts,
            "locks": self._writer_locks, # Legacy alias for backward compatibility
            "provider_locks": self._provider_locks,
            "identities": self._identities,
            "hijack_registry": self._hijack_registry,
            "root_registry": self.root_registry # Ensure children know the root
        }

    def bubble_set(self, key, value, source_node_id="System", scope_id=None):
        """Sets a single value and bubbles it to root."""
        self.bubble_set_batch({key: value}, source_node_id, scope_id)

    def bubble_set_batch(self, data_dict, source_node_id="System", scope_id=None):
        """
        Sets multiple values in the local registry AND bubbles them to the root.
        Optimized for Telemetry debouncing.
        """
        # 1. Update Local Registry in bulk and get the FRESH metadata
        local_updates = self.set_batch(data_dict, source_node_id, scope_id)
        
        # 2. Update Root Registry if different
        if self.root_registry is not self._variables_registry and local_updates:
            try:
                # [FIX] Use local_updates directly instead of re-fetching from proxy
                # This avoids race conditions where the proxy might return stale metadata.
                self.root_registry.update(local_updates)
            except (BrokenPipeError, EOFError, ConnectionResetError):
                pass
            except Exception as e:
                logger.debug(f"Bubble Batch Set failed to reach root: {e}")

    def get_internal_state(self):
        """Returns the full shared registries and locks (deprecated for subgraphs)."""
        state = self.get_system_state()
        state.update({
            "variables_registry": self._variables_registry,
            "lock_owners": self._lock_owners
        })
        return state

    def __getstate__(self):
        """Standard cleanup to allow transfer across processes."""
        state = self.__dict__.copy()
        # AuthenticationString inside manager can't be pickled
        state['manager'] = None 
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # manager remains None in child processes unless re-initialized
        # This is fine as child processes don't typically need to spawn child managers

    def clear(self):
        """
        Safely clears transient variables from the bridge's root and local registries.
        This is primarily used by the GUI to purge stale status flags 
        (like _IsServiceRunning or _SubGraphActivity) when execution fully stops.
        """
        try:
            # Clear local GUI transient state
            if self._variables_registry:
                self._variables_registry.clear()
            
            # Clear the lock owners to avoid stale tracking
            if self._lock_owners:
                self._lock_owners.clear()
                
            logger.debug("[Bridge] Local variable registry and lock owners explicitly cleared.")
        except Exception as e:
            logger.warning(f"[Bridge] Error clearing bridge registry: {e}")



    # --- Identity & Session Manager (ISM) ---

    def register_identity(self, app_id, identity_obj):
        """Registers a new identity for a specific session/app scope."""
        if hasattr(identity_obj, "to_dict"):
            self._identities[app_id] = identity_obj.to_dict()
        else:
            self._identities[app_id] = identity_obj

    def get_identity(self, app_id):
        """Retrieves and reconstructs the IdentityObject for a scope."""
        data = self._identities.get(app_id)
        if data:
            from axonpulse.core.identity import IdentityObject
            return IdentityObject.from_dict(data)
        return None

    def update_identity_auth(self, app_id, auth_payload):
        """Dynamically updates the auth payload for an active identity."""
        identity = self.get_identity(app_id)
        if identity:
            identity.auth_payload.update(auth_payload)
            self.register_identity(app_id, identity)
            return True
        return False

    def request_asset_password(self, zip_path, timeout=60.0):
        """
        Requests a password for an encrypted asset from the UI via the Bridge.
        Blocks until a response is received or timeout occurs.
        """
        import uuid
        request_id = str(uuid.uuid4())[:8]
        zip_name = os.path.basename(zip_path)
        
        # 1. Post Request to Bridge
        request_key = f"AssetPasswordRequest:{request_id}"
        self.bubble_set(request_key, {
            "path": zip_path,
            "filename": zip_name,
            "status": "pending",
            "timestamp": time.time()
        })
        
        logger.info(f"[Bridge] Password request sent for {zip_name} (ID: {request_id})")
        
        # 2. Wait for Response (Polling for now)
        response_key = f"AssetPasswordResponse:{request_id}"
        start = time.time()
        while time.time() - start < timeout:
            response = self.get(response_key)
            if response and response.get("password"):
                # Cleanup request
                self.set(request_key, None)
                self.set(response_key, None) 
                return response["password"]
            
            # Check if user cancelled
            if response and response.get("status") == "cancelled":
                self.set(request_key, None)
                self.set(response_key, None)
                return None

            time.sleep(0.5)
            
        logger.warning(f"[Bridge] Password request timed out for {zip_name}")
        return None

    def request_node_upgrade(self, node_id, latest_version):
        """
        Signs a request for the engine to upgrade a specific node to its latest version.
        """
        self.bubble_set(f"NODE_UPGRADE_REQUEST_{node_id}", {
            "node_id": node_id,
            "latest_version": latest_version,
            "timestamp": time.time()
        })
        logger.info(f"[Bridge] Node upgrade requested for {node_id} to v{latest_version}")

    # --- Provider Hijacking (Middleware Logic) ---

    def register_super_function(self, provider_id, func_name, handler_node_id):
        """Registers a function override for a provider."""
        registry = self._hijack_registry.get(provider_id, {})
        registry[func_name] = handler_node_id
        self._hijack_registry[provider_id] = registry
        logger.info(f"Registered Super-Function: {provider_id} -> {func_name} (Handler: {handler_node_id})")

    def unregister_super_functions(self, provider_id):
        """Removes all function overrides for a provider."""
        if provider_id in self._hijack_registry:
            del self._hijack_registry[provider_id]
            logger.info(f"Unregistered all Super-Functions for provider: {provider_id}")

    def get_hijack_handler(self, context_stack, func_name):
        """
        Looks up the stack to find a provider that overrides the given function.
        Returns handler_node_id if found, else None.
        """
        if not context_stack:
            return None
        
        # Search from innermost (top of stack) to outermost (head of list)
        curr = context_stack
        while curr:
            provider_id = curr[0]
            registry = self._hijack_registry.get(provider_id)
            if registry and func_name in registry:
                return registry[func_name]
            curr = curr[1] # Move to parent
        
        return None

    def get_provider_id(self, context_stack, provider_type):
        """
        Searches the context stack for a provider of a specific type.
        Usage: bridge.get_provider_id(stack, "Database Provider")
        """
        if not context_stack:
            return None
            
        # Search from innermost to outermost
        curr = context_stack
        while curr:
            node_id = curr[0]
            # 1. Check if the Scope Node itself is the provider (Provider IDs are literal node ids)
            if getattr(self, "_provider_types", {}).get(node_id) == provider_type:
                return node_id
            
            # 2. Check if a provider is registered IN this scope
            # Key: "{scope_id}_Provider_{provider_type}" -> provider_node_id
            scoped_provider_id = self.get(f"{node_id}_Provider_{provider_type}")
            if scoped_provider_id:
                return scoped_provider_id
            
            curr = curr[1] # Move to parent
                
        return None

    def invoke_hijack(self, provider_id, func_name, data):
        """
        Synchronously (via IPC bridge) calls a hijack handler on a provider.
        For now, we use a simple variable-based request/response pattern 
        since we're in the same Manager scope.
        """
        request_id = f"hijack_req_{int(time.time()*1000)}"
        self.set(f"{provider_id}_HijackRequest", {"func": func_name, "data": data, "id": request_id}, "HijackInvoker")
        
        # Wait for response (short timeout)
        start = time.time()
        while time.time() - start < 1.0: # 1s timeout
            resp = self.get(f"{provider_id}_HijackResponse")
            if resp and resp.get("id") == request_id:
                return resp.get("result")
            time.sleep(0.01)
        
        logger.warning(f"Hijack timeout for provider {provider_id} on {func_name}")
        return data # Fallback to original data

    def _get_writer_lock(self, key):
        """Hashes the key to one of the 256 writer locks (RLocks) using stable CRC32."""
        idx = zlib.crc32(key.encode()) % 256
        return self._writer_locks[idx]

    def _get_reader_lock(self, key):
        """Hashes the key to one of the 256 reader locks (Locks) using stable CRC32."""
        idx = zlib.crc32(key.encode()) % 256
        return self._reader_locks[idx]

    def _get_reader_count_idx(self, key):
        """Returns the pool index for the reader counter using stable CRC32."""
        return zlib.crc32(key.encode()) % 256

    def get_provider_lock(self, lock_id):
        """
        Returns a Lock object for a specific provider ID.
        Uses a separate pool of 128 locks to avoid contention with variable locks.
        """
        if not hasattr(self, "_provider_locks"):
            # Lazy init (or we can move to __init__ if manager is available there)
            # But since __init__ runs in main process, better to do there.
            # However, for now, let's assume it was init'd.
            # Wait, self._locks were init'd in __init__.
            pass 
            
        # Hash to bucket
        # We need to ensure _provider_locks implementation in __init__ first.
        # But wait, I can edit __init__ in a separate chunk.
        # Here I just implement the getter logic assuming valid list.
        idx = hash(lock_id) % 128
        return self._provider_locks[idx]

    def get_batch(self, keys, scope_id=None):
        """
        Retrieves multiple values at once. Reduces manager.dict access overhead.
        """
        target_scope = scope_id or self.default_scope
        results = {}
        # 1. Gather all metadata in one pass if possible (manager.dict doesn't support bulk get)
        # But we can at least optimize the local cache loop
        for key in keys:
            results[key] = self.get(key, scope_id=target_scope)
        return results

    def get(self, key, default=None, scope_id=None):
        """
        Retrieves a value. Uses local cache if version matches shared registry.
        """
        target_scope = scope_id or self.default_scope
        # 1. Resolve Key Logic (Scoped -> Global -> Legacy)
        keys_to_check = [f"{target_scope}:{key}"]
        if target_scope != "Global":
            keys_to_check.append(f"Global:{key}")
        keys_to_check.append(key)
        
        final_key = None
        metadata = None
        
        for k in keys_to_check:
            if k in self._variables_registry:
                metadata = self._variables_registry[k]
                final_key = k
                break
        
        # [NEW] Fallback to Root Registry for cross-subgraph global access
        if metadata is None and self.root_registry is not self._variables_registry:
            for k in keys_to_check:
                if k in self.root_registry:
                    metadata = self.root_registry[k]
                    final_key = k
                    break

        if metadata is None:
            return default

        # metadata format: (shm_name, version, timestamp, [length])
        shm_name, version = metadata[0], metadata[1]
        payload_len = metadata[3] if len(metadata) > 3 else None
        
        # 2. Check Local Cache (Fast Path - No Lock Needed for Local Memory)
        cached_entry = self._local_cache.get(final_key)
        if cached_entry and cached_entry[1] == version:
            return cached_entry[0] # REUSE LOCAL OBJECT (Zero-Copy win)

        # 3. [RWLock] Reader Acquisition for Shared Memory Access
        # This prevents the SHM block from being unlinked/recreated while we read.
        idx = self._get_reader_count_idx(final_key)
        r_lock = self._reader_locks[idx]
        w_lock = self._writer_locks[idx]
        
        # Increment reader count. If first reader, block writers.
        with r_lock:
            self._reader_counts[idx] += 1
            if self._reader_counts[idx] == 1:
                # We don't use timeout here because readers should wait for 
                # active writes to finish to ensure data consistency.
                w_lock.acquire() 

        try:
            # 4. Cache Miss / Outdated - Read from Shared Memory
            try:
                existing_shm = shared_memory.SharedMemory(name=shm_name)
                try:
                    # [FIX] Explicitly manage memoryview scope to avoid 'cannot close exported pointers' error on Windows
                    buf = existing_shm.buf
                    data_subset = buf[:payload_len] if payload_len else buf[:]
                    try:
                        try:
                            # Try fast path
                            data = msgpack.unpackb(bytes(data_subset), object_hook=msgpack_decode, raw=False)
                        except (msgpack.ExtraData, ValueError):
                            # [ROBUST] Fallback to Unpacker if extra data exists in reused block
                            unpacker = msgpack.Unpacker(object_hook=msgpack_decode, raw=False)
                            unpacker.feed(bytes(data_subset))
                            data = next(unpacker)
                        
                        self._local_cache[final_key] = (data, version)
                        return data
                    finally:
                        # CRITICAL: Release the memoryview exports before closing the shm block
                        if data_subset is not buf:
                            data_subset.release()
                        buf.release()
                finally:
                    existing_shm.close()
            except Exception as e:
                logger.error(f"Failed to read Shared Memory for '{final_key}': {e}")
                return default
        finally:
            # Decrement reader count. If last reader, allow writers.
            with r_lock:
                self._reader_counts[idx] -= 1
                if self._reader_counts[idx] == 0:
                    try:
                        w_lock.release()
                    except: pass # Lock might have been force-broken by watchdog
            
    def set_object(self, key, obj):
        """Sets a live, non-picklable object in the local process registry."""
        self._local_objects[key] = obj
        
    def get_object(self, key, default=None):
        """Retrieves a live object from the local process registry."""
        return self._local_objects.get(key, default)

    def pin_all(self):
        """
        [MASTER ONLY] Ensures this process holds a handle to all registered SHM blocks.
        On Windows, this prevents the OS from destroying blocks when workers exit.
        """
        active_names = set()
        # Registry stores metadata: (shm_name, version, timestamp)
        for key in self._variables_registry.keys():
            metadata = self._variables_registry.get(key)
            if metadata and isinstance(metadata, (list, tuple)):
                active_names.add(metadata[0])
        
        # 1. Pin new ones
        for name in active_names:
            if name not in self._pinned_shm:
                try:
                    self._pinned_shm[name] = shared_memory.SharedMemory(name=name)
                except Exception as e:
                    logger.debug(f"Could not pin {name}: {e}")
        
        # 2. Unpin dead ones
        dead_names = set(self._pinned_shm.keys()) - active_names
        for name in dead_names:
            try:
                shm = self._pinned_shm.pop(name)
                shm.close()
            except: pass
        
        self._shm_dirty = False

    def _write_shm(self, scoped_key, value):
        """
        Private helper to handle the complex logic of writing to Shared Memory.
        Acquires the hashed lock, manages SHM recreation/reuse, and updates local cache.
        Returns metadata tuple: (shm_name, version, timestamp, length)
        """
        import hashlib
        try:
            # 1. Serialize
            data_bytes = msgpack.packb(value, default=msgpack_encode, use_bin_type=True)
            
            # [TIMEOUT LOCK] Wait up to 2.0 seconds for the writer lock
            lock = self._get_writer_lock(scoped_key)
            acquired = lock.acquire(timeout=2.0)
            if not acquired:
                logger.error(f"[TIMEOUT] Failed to acquire lock for '{scoped_key}' after 2s. Forcing overlap.")
            
            try:
                # 2. Manage Versioning and Naming
                old_metadata = self._variables_registry.get(scoped_key)
                new_version = (old_metadata[1] + 1) if old_metadata else 1
                
                if old_metadata:
                    shm_name = old_metadata[0]
                else:
                    shm_name = f"syn_{hashlib.md5(scoped_key.encode()).hexdigest()[:16]}"
                
                shm = None
                try:
                    # Try to reuse existing shm if possible
                    shm = shared_memory.SharedMemory(name=shm_name)
                    if shm.size < len(data_bytes):
                        # Too small, must recreate
                        shm.close()
                        try:
                            shm.unlink()
                            SHMTracker.unregister(shm_name)
                        except: pass
                        shm_name = f"syn_{hashlib.md5(scoped_key.encode()).hexdigest()[:10]}_{new_version}"
                        shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                        SHMTracker.register(shm_name)
                except (FileNotFoundError, Exception):
                    # Doesn't exist or failed to open, try to create
                    try:
                        shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                        SHMTracker.register(shm_name)
                    except (FileExistsError, Exception):
                        # Race condition: someone created it between the try and here
                        try:
                            shm = shared_memory.SharedMemory(name=shm_name)
                        except:
                            # If still failing, recreate with epoch for uniqueness
                            shm_name = f"syn_{hashlib.md5(scoped_key.encode()).hexdigest()[:10]}_{int(time.time()*1000)}"
                            shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                            SHMTracker.register(shm_name)

                try:
                    # [FIX] Explicitly manage memoryview scope
                    buf = shm.buf
                    try:
                        buf[:len(data_bytes)] = data_bytes
                    finally:
                        buf.release()
                    
                    # 3. PIN handle to prevent Windows garbage collection
                    self._pinned_shm[shm_name] = shm 
                except Exception as b_err:
                    try:
                        shm.close()
                        shm.unlink()
                        SHMTracker.unregister(shm_name)
                    except: pass
                    raise b_err
                
                # 4. Update local cache (Zero-Copy win for this process)
                self._local_cache[scoped_key] = (value, new_version)
                
                return (shm_name, new_version, time.time(), len(data_bytes))
                
            finally:
                if acquired:
                    try: lock.release()
                    except: pass
        except Exception as e:
             if "pipe is being closed" not in str(e).lower():
                logger.error(f"Internal SHM write failed for '{scoped_key}': {e}")
             raise e

    def set_batch(self, data_dict, source_node_id="System", scope_id=None):
        """
        Writes multiple values. Atomic registry update for performance.
        Returns the registry_update dict (scoped_key -> metadata_tuple).
        """
        target_scope = scope_id or self.default_scope
        registry_update = {}
        for key, value in data_dict.items():
            scoped_key = f"{target_scope}:{key}"
            try:
                metadata = self._write_shm(scoped_key, value)
                registry_update[scoped_key] = metadata
            except (BrokenPipeError, EOFError, ConnectionResetError):
                pass
            except Exception as e:
                logger.error(f"Batch Set failed for '{scoped_key}': {e}")
        
        if registry_update:
            self._variables_registry.update(registry_update)
            self._shm_dirty = True
        return registry_update

    def mutate(self, key, action, payload, scope_id=None):
        """
        [Phase 3] IPC Delta Updates (The "Change Request" Architecture)
        Targeted in-place modifications to large Shared Memory collections (Lists/Dicts)
        without requiring the logic node to transmit the entire object back and forth.
        
        Args:
            action (str): e.g., 'list_append', 'list_remove', 'dict_update', 'dict_pop'
        Returns:
            bool: True if successful, False if the object couldn't be mutated.
        """
        target_scope = scope_id or self.default_scope
        scoped_key = f"{target_scope}:{key}"
        
        lock = self._get_writer_lock(scoped_key)
        acquired = lock.acquire(timeout=2.0)
        if not acquired:
            logger.error(f"[TIMEOUT] Failed to acquire lock for mutating '{scoped_key}' after 2s. Forcing overlap.")
            
        try:
            # 1. Read Current Data
            metadata = self._variables_registry.get(scoped_key)
            if not metadata:
                logger.error(f"Cannot mutate '{scoped_key}': Variable does not exist.")
                return False
            shm_name, version = metadata[0], metadata[1]
            payload_len = metadata[3] if len(metadata) > 3 else None
            
            try:
                existing_shm = shared_memory.SharedMemory(name=shm_name)
                try:
                    # [FIX] Explicitly manage memoryview scope
                    buf = existing_shm.buf
                    data_subset = buf[:payload_len] if payload_len else buf[:]
                    try:
                        try:
                            # Try fast path
                            current_data = msgpack.unpackb(bytes(data_subset), object_hook=msgpack_decode, raw=False)
                        except (msgpack.ExtraData, ValueError):
                            # [ROBUST] Fallback to Unpacker if extra data exists in reused block
                            unpacker = msgpack.Unpacker(object_hook=msgpack_decode, raw=False)
                            unpacker.feed(bytes(data_subset))
                            current_data = next(unpacker)
                    finally:
                        if data_subset is not buf:
                            data_subset.release()
                        buf.release()
                finally:
                    existing_shm.close()
            except Exception as e:
                logger.error(f"Cannot mutate '{scoped_key}': Failed to read existing SHM: {e}")
                return False

            # 2. Apply In-Place Mutation
            try:
                if action == "list_append" and isinstance(current_data, list):
                    current_data.append(payload)
                elif action == "list_remove" and isinstance(current_data, list):
                    if payload in current_data:
                        current_data.remove(payload)
                elif action == "dict_update" and isinstance(current_data, dict):
                    if isinstance(payload, dict):
                        current_data.update(payload)
                elif action == "dict_pop" and isinstance(current_data, dict):
                    current_data.pop(payload, None)
                else:
                    logger.error(f"Mutation failed: Action '{action}' invalid for type {type(current_data)}")
                    return False
            except Exception as e:
                logger.error(f"Mutation logic failed on '{scoped_key}': {e}")
                return False
                
            # 3. Serialize and Write Back using unified helper
            try:
                metadata = self._write_shm(scoped_key, current_data)
                self._variables_registry[scoped_key] = metadata
                self._shm_dirty = True
                
                # 4. Optional: Cleanup old block if it changed
                # Since _write_shm might have reused the block, we only unlink if name changed
                if metadata[0] != shm_name:
                    try:
                        if shm_name in self._pinned_shm:
                            old_shm = self._pinned_shm.pop(shm_name)
                            old_shm.close()
                            old_shm.unlink()
                            SHMTracker.unregister(shm_name)
                    except: pass
            except Exception as e:
                logger.error(f"Failed to write back mutated SHM for '{scoped_key}': {e}")
                return False
            
            return True

        except (BrokenPipeError, EOFError, ConnectionResetError):
            pass
        except Exception as e:
            if "pipe is being closed" not in str(e).lower():
                logger.error(f"Failed to mutate Shared Memory for '{scoped_key}': {e}")
            return False
        finally:
            if acquired:
                try: lock.release()
                except: pass

    def set(self, key, value, source_node_id="System", scope_id=None):
        """
        Writes a value to Shared Memory and updates the Registry.
        """
        target_scope = scope_id or self.default_scope
        scoped_key = f"{target_scope}:{key}"
        
        try:
            metadata = self._write_shm(scoped_key, value)
            self._variables_registry[scoped_key] = metadata
            self._shm_dirty = True
        except (BrokenPipeError, EOFError, ConnectionResetError) as e:
            # Silent during shutdown
            pass
        except Exception as e:
            if "pipe is being closed" in str(e).lower():
                pass
            else:
                logger.error(f"Failed to set Shared Memory for '{scoped_key}': {e}")
                    
        except (BrokenPipeError, EOFError, ConnectionResetError) as e:
            # Silent during shutdown
            pass
        except Exception as e:
            if "pipe is being closed" in str(e).lower():
                pass
            else:
                logger.error(f"Failed to set Shared Memory for '{scoped_key}': {e}")

    def increment(self, key, amount=1, scope_id=None):
        """Atomsically increments a numeric variable in the bridge."""
        target_scope = scope_id or self.default_scope
        scoped_key = f"{target_scope}:{key}"
        
        lock = self._get_writer_lock(scoped_key)
        acquired = lock.acquire(timeout=2.0)
        if not acquired:
            logger.error(f"[TIMEOUT] Failed to acquire lock for incrementing '{scoped_key}' after 2s. Forcing overlap.")
            
        try:
            val = self.get(key, 0, scope_id=target_scope)
            try:
                new_val = val + amount
                self.set(key, new_val, "BridgeAtomic", scope_id=target_scope)
                return new_val
            except:
                return val
        finally:
            if acquired:
                try: lock.release()
                except: pass

    def decrement(self, key, amount=1, scope_id=None):
        """Atomsically decrements a numeric variable in the bridge."""
        return self.increment(key, -amount, scope_id=scope_id)

    def get_scoped(self, key, scope_id):
        """Force retrieval from specific scope, no fallback."""
        return self.get(key, scope_id=scope_id)

    def clear(self):
        """Resets all variables and unlinks Shared Memory blocks."""
        # This should ideally only be called by the Master Process
        for key in list(self._variables_registry.keys()):
            metadata = self._variables_registry.get(key)
            if metadata:
                try:
                    shm = shared_memory.SharedMemory(name=metadata[0])
                    shm.close()
                    shm.unlink()
                    SHMTracker.unregister(metadata[0])
                except: pass
        
        # Cleanup pins
        for name in list(self._pinned_shm.keys()):
            try:
                shm = self._pinned_shm.pop(name)
                shm.close()
            except: pass

        self._variables_registry.clear()
        self._local_cache.clear()
        self._lock_owners.clear()
        
        # Shutdown connection pool on clear to avoid leak
        if hasattr(self, 'pool_manager'):
            self.pool_manager.shutdown()

    def _is_process_alive(self, pid):
        """Cross-platform check to see if a PID is still actively running in the OS."""
        if pid is None:
            return False
            
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fallback if psutil is unavailable (less reliable on Windows with PID reuse)
            if os.name == 'nt':
                # Windows fallback (hacky, but works without psutil)
                try:
                    import ctypes
                    # PROCESS_QUERY_INFORMATION (0x0400)
                    handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
                    if not handle:
                        return False
                    
                    exit_code = ctypes.c_ulong()
                    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    ctypes.windll.kernel32.CloseHandle(handle)
                    
                    # 259 (STILL_ACTIVE)
                    return exit_code.value == 259
                except:
                    return True # Fail safe
            else:
                # Unix fallback
                import sys
                try:
                    import os
                    os.kill(pid, 0)
                    return True
                except OSError:
                    return False

    def lock(self, key, node_id, timeout=2.0):
        """
        Attempts to conceptually 'lock' a variable key for exclusive access by a node.
        Includes a Watchdog that verifies if the lock owner's OS Process ID is still alive.
        """
        start_time = time.time()
        import os
        current_pid = os.getpid()
        
        while time.time() - start_time < timeout:
            with self._get_writer_lock(key):
                current_owner_data = self._lock_owners.get(key)
                
                # 1. Lock is Free
                if current_owner_data is None:
                    self._lock_owners[key] = (node_id, current_pid)
                    return True
                    
                # 2. Lock is Owned by US
                owner_id = current_owner_data[0] if isinstance(current_owner_data, tuple) else current_owner_data
                if owner_id == node_id:
                    # Update our PID just in case we inherited/restarted
                    self._lock_owners[key] = (node_id, current_pid)
                    return True
                    
                # 3. Lock is Owned by Someone Else... Are they dead?
                owner_pid = current_owner_data[1] if isinstance(current_owner_data, tuple) else None
                if owner_pid is not None:
                    if not self._is_process_alive(owner_pid):
                        logger.warning(f"[WATCHDOG] Force Breaking Lock on '{key}'. Owner Node '{owner_id}' (PID: {owner_pid}) is DEAD in the OS.")
                        # Steal the lock immediately
                        self._lock_owners[key] = (node_id, current_pid)
                        return True
            
            time.sleep(0.05) # Wait before retrying
        
        # If we reach here, we hit the timeout and the owner is supposedly still alive
        owner_data = self._lock_owners.get(key)
        owner_str = f"{owner_data[0]} (PID: {owner_data[1]})" if isinstance(owner_data, tuple) else str(owner_data)
        logger.warning(f"Node {node_id} TIMED OUT after {timeout}s trying to acquire lock for '{key}' (Held by {owner_str})")
        return False

    def unlock(self, key, node_id):
        """Releases a lock on a variable."""
        with self._get_lock(key):
            current_owner_data = self._lock_owners.get(key)
            if current_owner_data is None:
                return
                
            owner_id = current_owner_data[0] if isinstance(current_owner_data, tuple) else current_owner_data
            if owner_id == node_id:
                del self._lock_owners[key]
            else:
                logger.error(f"Node {node_id} tried to unlock '{key}' but it is owned by {owner_id}")

    def dump_state(self):
        """Returns a snapshot of the current state for debugging."""
        # We need to resolve all SHM blocks for the UI to see them
        snapshot = {}
        for key in self.get_all_keys():
            snapshot[key] = self.get(key)
        return snapshot

    def get_all_keys(self):
        """Returns a list of all keys in the variable store."""
        return list(self._variables_registry.keys())

    def export_state(self):
        """
        Exports the current variable state (Registry metadata).
        Used for Time-Travel Debugging. Note: Actual SHM blocks stay in OS.
        """
        return {
            "registry": dict(self._variables_registry)
        }

    def import_state(self, state_snapshot):
        """
        Restores the variable registry from a snapshot.
        """
        if not state_snapshot: return
        registry_data = state_snapshot.get("registry", {})
        self._variables_registry.clear()
        self._variables_registry.update(registry_data)
        self._local_cache.clear() # Invalidate local cache
