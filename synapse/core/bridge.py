import multiprocessing
import time
import pickle
from multiprocessing import shared_memory
from synapse.utils.logger import setup_logger

logger = setup_logger("SynapseBridge")

class SynapseBridge:
    """
    The Bridge acts as the middleware for Inter-Process Communication (IPC).
    It manages shared variables, locks, and Zero-Copy Shared Memory for large data.
    """
    def __init__(self, manager, system_state=None, data_state=None):
        self.manager = manager # Store for reuse by child engines
        
        # 1. System State (Shared across whole process tree for hardware sync)
        if system_state:
            self._locks = system_state["locks"]
            self._provider_locks = system_state["provider_locks"]
            self._identities = system_state["identities"]
            self._hijack_registry = system_state["hijack_registry"]
            self.root_registry = system_state.get("root_registry") # Inherit root from parent
        else:
            self._locks = manager.list([manager.RLock() for _ in range(32)])
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
        
        # [WINDOWS PERSISTENCE] Persistent handles to SHM blocks
        # Only the "Master" process (Engine) needs to fill this.
        self._pinned_shm = {} # shm_name -> SharedMemory object
        self._shm_dirty = False # [OPTIMIZATION] Flag to skip pin_all if no new blocks

    def get_system_state(self):
        """Returns only the hardware locks and system registries."""
        return {
            "locks": self._locks,
            "provider_locks": self._provider_locks,
            "identities": self._identities,
            "hijack_registry": self._hijack_registry,
            "root_registry": self.root_registry # Ensure children know the root
        }

    def bubble_set(self, key, value, source_node_id="System", scope_id=None):
        """
        Sets a value in the local registry AND bubbles it up to the root registry.
        Used for status updates (highlights, error states) that must reach the GUI.
        """
        # 1. Update Local Registry (Standard set)
        self.set(key, value, source_node_id, scope_id)
        
        # 2. Update Root Registry if it's different (Cross-SubGraph propagation)
        if self.root_registry is not self._variables_registry:
            target_scope = scope_id or self.default_scope
            scoped_key = f"{target_scope}:{key}"
            
            # Note: We reuse the SAME SHM block created by self.set()
            # We just need to inject the metadata into the root registry.
            metadata = self._variables_registry.get(scoped_key)
            if metadata:
                try:
                    self.root_registry[scoped_key] = metadata
                except (BrokenPipeError, EOFError, ConnectionResetError):
                    pass
                except Exception as e:
                    logger.debug(f"Bubble Set failed to reach root: {e}")

    def get_internal_state(self):
        """Returns the full shared registries and locks (deprecated for subgraphs)."""
        state = self.get_system_state()
        state.update({
            "variables_registry": self._variables_registry,
            "lock_owners": self._lock_owners
        })
        return state

    def __getstate__(self):
        """Standard pickle cleanup to allow transfer across processes."""
        state = self.__dict__.copy()
        # AuthenticationString inside manager can't be pickled
        state['manager'] = None 
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # manager remains None in child processes unless re-initialized
        # This is fine as child processes don't typically need to spawn child managers


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
            from synapse.core.identity import IdentityObject
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
        
        # Search from innermost (end of stack) to outermost
        for provider_id in reversed(context_stack):
            registry = self._hijack_registry.get(provider_id)
            if registry and func_name in registry:
                return registry[func_name]
        
        return None

    def get_provider_id(self, context_stack, provider_type):
        """
        Searches the context stack for a provider of a specific type.
        Usage: bridge.get_provider_id(stack, "Database Provider")
        """
        if not context_stack:
            return None
            
        for node_id in reversed(context_stack):
            # 1. Check if the Scope Node itself is the provider
            ptype = self.get(f"{node_id}_Provider Type")
            if ptype == provider_type:
                return node_id
            
            # 2. [NEW] Check if a provider is registered IN this scope
            # Key: "{scope_id}_Provider_{provider_type}" -> provider_node_id
            scoped_provider_id = self.get(f"{node_id}_Provider_{provider_type}")
            if scoped_provider_id:
                return scoped_provider_id
                
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

    def _get_lock(self, key):
        """Hashes the key to one of the 32 locks."""
        idx = hash(key) % 32
        return self._locks[idx]

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

        # metadata format: (shm_name, version, timestamp)
        shm_name, version = metadata[0], metadata[1]
        
        # 2. Check Local Cache
        cached_entry = self._local_cache.get(final_key)
        if cached_entry and cached_entry[1] == version:
            return cached_entry[0] # REUSE LOCAL OBJECT (Zero-Copy win)

        # 3. Cache Miss / Outdated - Read from Shared Memory
        try:
            existing_shm = shared_memory.SharedMemory(name=shm_name)
            try:
                data = pickle.loads(existing_shm.buf[:])
                self._local_cache[final_key] = (data, version)
                return data
            finally:
                existing_shm.close()
        except Exception as e:
            logger.error(f"Failed to read Shared Memory for '{final_key}': {e}")
            return default
            
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

    def set_batch(self, data_dict, source_node_id="System", scope_id=None):
        """
        Writes multiple values. Atomic registry update for performance.
        """
        target_scope = scope_id or self.default_scope
        registry_update = {}
        for key, value in data_dict.items():
            scoped_key = f"{target_scope}:{key}"
            try:
                # 1. Serialize
                data_bytes = pickle.dumps(value)
                
                # 2. Get Deterministic SHM Name (Reuse block)
                import hashlib
                shm_name = f"syn_{hashlib.md5(scoped_key.encode()).hexdigest()[:16]}"
                
                # 3. Manage SHM
                old_metadata = self._variables_registry.get(scoped_key)
                new_version = (old_metadata[1] + 1) if old_metadata else 1
                
                # Try to reuse existing shm if possible
                shm = None
                try:
                    shm = shared_memory.SharedMemory(name=shm_name)
                    if shm.size < len(data_bytes):
                        # Too small, must recreate
                        shm.close()
                        shm.unlink()
                        shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                except:
                    # Doesn't exist, create
                    shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                
                try:
                    shm.buf[:len(data_bytes)] = data_bytes
                    self._pinned_shm[shm_name] = shm 
                except Exception as b_err:
                    shm.close()
                    shm.unlink()
                    raise b_err
                
                registry_update[scoped_key] = (shm_name, new_version, time.time())
                self._local_cache[scoped_key] = (value, new_version)
                
            except (BrokenPipeError, EOFError, ConnectionResetError) as e:
                # Silent during shutdown
                pass
            except Exception as e:
                if "pipe is being closed" in str(e).lower():
                    pass
                else:
                    logger.error(f"Batch Set failed for '{scoped_key}': {e}")
        
        if registry_update:
            self._variables_registry.update(registry_update)
            self._shm_dirty = True

    def set(self, key, value, source_node_id="System", scope_id=None):
        """
        Writes a value to Shared Memory and updates the Registry.
        """
        target_scope = scope_id or self.default_scope
        scoped_key = f"{target_scope}:{key}"
        
        try:
            # 1. Serialize
            data_bytes = pickle.dumps(value)
            
            with self._get_lock(scoped_key):
                # 2. Get Deterministic SHM Name (Reuse block)
                import hashlib
                shm_name = f"syn_{hashlib.md5(scoped_key.encode()).hexdigest()[:16]}"
                
                # 3. Manage SHM
                old_metadata = self._variables_registry.get(scoped_key)
                new_version = (old_metadata[1] + 1) if old_metadata else 1
                
                try:
                    # Try to reuse existing shm if possible
                    shm = shared_memory.SharedMemory(name=shm_name)
                    if shm.size < len(data_bytes):
                        # Too small, must recreate
                        shm.close()
                        try: shm.unlink()
                        except: pass
                        shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                except (FileNotFoundError, Exception):
                    # Doesn't exist or failed to open, try to create
                    try:
                        shm = shared_memory.SharedMemory(create=True, size=len(data_bytes), name=shm_name)
                    except (FileExistsError, Exception):
                        # Race condition: someone created it between the try and here
                        shm = shared_memory.SharedMemory(name=shm_name)
                        # If the one someone else created is too small, we have a problem, 
                        # but usually keys have consistent types/sizes per pulse.
                
                try:
                    shm.buf[:len(data_bytes)] = data_bytes
                    # 4. PIN IMMEDIATELY (Keep handle alive)
                    self._pinned_shm[shm_name] = shm 
                except Exception as b_err:
                    shm.close()
                    try: shm.unlink()
                    except: pass
                    raise b_err
                
                # 5. Update Registry (Atomic)
                # metadata format: (shm_name, version, timestamp)
                self._variables_registry[scoped_key] = (shm_name, new_version, time.time())
                
                # Update local cache immediately
                self._local_cache[scoped_key] = (value, new_version)
                self._shm_dirty = True
                
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
        with self._get_lock(scoped_key):
            val = self.get(key, 0, scope_id=target_scope)
            try:
                new_val = val + amount
                self.set(key, new_val, "BridgeAtomic", scope_id=target_scope)
                return new_val
            except:
                return val

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

    def lock(self, key, node_id, timeout=5.0):
        """
        Attempts to conceptually 'lock' a variable key for exclusive access by a node.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._get_lock(key):
                current_owner = self._lock_owners.get(key)
                if current_owner is None:
                    self._lock_owners[key] = node_id
                    return True
                elif current_owner == node_id:
                    return True
            
            time.sleep(0.05) # Wait before retrying
        
        logger.warning(f"Node {node_id} TIMED OUT trying to acquire lock for '{key}' (Held by {self._lock_owners.get(key)})")
        return False

    def unlock(self, key, node_id):
        """Releases a lock on a variable."""
        with self._get_lock(key):
            current_owner = self._lock_owners.get(key)
            if current_owner == node_id:
                del self._lock_owners[key]
            else:
                logger.error(f"Node {node_id} tried to unlock '{key}' but it is owned by {current_owner}")

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
