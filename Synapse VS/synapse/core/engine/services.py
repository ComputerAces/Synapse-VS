import os
import time
from synapse.utils.logger import setup_logger

logger = setup_logger("SynapseEngine")

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
                    print(f"[SERVICE_STOP] {node_id}")
                except (BrokenPipeError, EOFError, ConnectionResetError):
                    pass
                except Exception as e:
                    if "pipe is being closed" in str(e).lower():
                        pass
                    else:
                        logger.error(f"Failed to stop service {node.name}: {e}")
            self.service_registry.clear()
