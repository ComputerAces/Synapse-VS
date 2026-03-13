import os
import time
import threading
from typing import Callable, Any, Dict, List
from axonpulse.utils.logger import setup_logger

logger = setup_logger("AxonPulseEngine")

class ConnectionPoolManager:
    """
    Manages centralized connection pooling for expensive network sockets
    (Database connections, HTTP sessions, etc.) across parallel workers.
    """
    def __init__(self, cleanup_interval: int = 60, idle_timeout: int = 300):
        self.pools: Dict[str, Dict] = {}
        self.cleanup_interval = cleanup_interval
        self.idle_timeout = idle_timeout
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        
    def _create_pool(self, pool_id: str, max_concurrency: int):
        if pool_id not in self.pools:
            self.pools[pool_id] = {
                "connections": [], # List of (connection, last_used_time)
                "in_use": [],      # List of active connections
                "lock": threading.Lock(),
                "max_concurrency": max_concurrency
            }
            
    def acquire_connection(self, pool_id: str, creator_func: Callable[[], Any], max_concurrency: int = 10, timeout: float = 10.0):
        """
        Leases a connection. Waits if pool is full.
        If empty and below max_concurrency, spins up a new connection.
        """
        self._create_pool(pool_id, max_concurrency)
        pool = self.pools[pool_id]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with pool["lock"]:
                if pool["connections"]:
                    # Reuse idle connection
                    conn, _ = pool["connections"].pop()
                    pool["in_use"].append(conn)
                    return conn
                elif len(pool["in_use"]) < pool["max_concurrency"]:
                    # Create new connection
                    conn = creator_func()
                    if conn:
                        pool["in_use"].append(conn)
                    return conn
                    
            time.sleep(0.05)
            
        logger.error(f"[TIMEOUT] Failed to acquire connection from pool '{pool_id}' after {timeout}s.")
        return None

    def release_connection(self, pool_id: str, conn: Any):
        """Returns the connection back to the pool."""
        if pool_id not in self.pools or not conn:
            return
            
        pool = self.pools[pool_id]
        with pool["lock"]:
            if conn in pool["in_use"]:
                pool["in_use"].remove(conn)
                pool["connections"].append((conn, time.time()))
                
    def _cleanup_worker(self):
        """Background thread that quietly pings idle connections and closes dead ones."""
        while self._running:
            for _ in range(self.cleanup_interval):
                if not self._running:
                    return
                time.sleep(1)
                
            now = time.time()
            for pool_id, pool in self.pools.items():
                with pool["lock"]:
                    active_conns = []
                    for conn, last_used in pool["connections"]:
                        if now - last_used > self.idle_timeout:
                            # Close dead/idle connections
                            try:
                                if hasattr(conn, "close"):
                                    conn.close()
                                elif hasattr(conn, "disconnect"):
                                    conn.disconnect()
                            except Exception as e:
                                logger.debug(f"Error closing idle connection in pool {pool_id}: {e}")
                        else:
                            active_conns.append((conn, last_used))
                    pool["connections"] = active_conns
                    
    def shutdown(self):
        """Stops the cleanup thread and forcibly closes all connections."""
        self._running = False
        for pool_id, pool in self.pools.items():
            with pool["lock"]:
                for conn, _ in pool["connections"]:
                    try:
                        if hasattr(conn, "close"):
                            conn.close()
                        elif hasattr(conn, "disconnect"):
                            conn.disconnect()
                    except: pass
                pool["connections"].clear()
                for conn in pool["in_use"]:
                    try:
                        if hasattr(conn, "close"):
                            conn.close()
                        elif hasattr(conn, "disconnect"):
                            conn.disconnect()
                    except: pass
                pool["in_use"].clear()
        self.pools.clear()

class ServiceMixin:
    """
    Handles background services and hot-reload checks.
    """
    def _check_hot_reload(self):
        """Checks if the source file has been modified. Returns True if modified."""
        if not self.source_file or not os.path.exists(self.source_file):
            return False

        try:
            current_mtime = os.path.getmtime(self.source_file)
            if current_mtime > self._last_mtime:
                logger.info(f"Hot Reload Detected: {self.source_file}")
                self._last_mtime = current_mtime
                return True
        except Exception:
            pass
        return False

    def stop_all_services(self):
        """Cleans up any long-running nodes."""
        
        if self.service_registry:
            logger.info(f"Stopping {len(self.service_registry)} background services...")
            for node_id, node in self.service_registry.items():
                try:
                    node.terminate()
                    self.bridge.set(f"{node_id}_IsServiceRunning", False, "Engine")
                    self.bridge.set(f"{node_id}_ActivePorts", None, "Engine_Cleanup")
                    print(f"[SERVICE_STOP] {node_id}")
                except (BrokenPipeError, EOFError, ConnectionResetError):
                    pass
                except Exception as e:
                    if "pipe is being closed" in str(e).lower():
                        pass
                    else:
                        logger.error(f"Failed to stop service {node.name}: {e}")
            self.service_registry.clear()
