import time
import threading
from axonpulse.utils.logger import setup_logger

logger = setup_logger("Telemetry")

class TelemetryDebouncer:
    """
    Buffers visual state updates (highlights, conditions, active ports) 
    and flushes them to the Bridge at a fixed interval (e.g., 30Hz).
    Decouples execution speed from Bridge/UI synchronization overhead.
    """
    def __init__(self, bridge, flush_interval=0.033): # ~30Hz default
        self.bridge = bridge
        self.flush_interval = flush_interval
        self._buffer = {} # key -> value
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="TelemetryFlush")
        self._thread.start()

    def update(self, key, value):
        """Adds or updates a visual state in the buffer."""
        with self._lock:
            self._buffer[key] = value

    def _run(self):
        """Background loop to flush telemetry at the set interval."""
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            self.flush()

    def flush(self):
        """Sends all buffered updates to the bridge in an atomic batch."""
        with self._lock:
            if not self._buffer:
                return
            batch = self._buffer.copy()
            self._buffer.clear()

        try:
            # Use bubble_set_batch for efficiency across SubGraphs
            if hasattr(self.bridge, "bubble_set_batch"):
                try:
                    self.bridge.bubble_set_batch(batch)
                except Exception as b_err:
                    # If it fails (likely due to lock timeout or pipe closure), 
                    # put it back in the buffer for the next cycle
                    with self._lock:
                        for k, v in batch.items():
                            if k not in self._buffer:
                                self._buffer[k] = v
                    logger.debug(f"Telemetry batch flush failed (retrying in next cycle): {b_err}")
                    time.sleep(0.01) # Tiny sleep to yield
            else:
                # Fallback if bridge is not yet upgraded
                for k, v in batch.items():
                    self.bridge.bubble_set(k, v, "Telemetry")
        except Exception as e:
            logger.debug(f"Telemetry flush failed: {e}")

    def stop(self):
        """Signals the flush thread to stop and performs a final flush."""
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.flush()
