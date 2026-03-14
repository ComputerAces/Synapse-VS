import time
import unittest
from unittest.mock import MagicMock
from axonpulse.core.engine.telemetry import TelemetryDebouncer

class TestTelemetryDebouncing(unittest.TestCase):
    def test_debouncer_buffers_and_flushes(self):
        # Setup mock bridge
        bridge = MagicMock()
        # Ensure it has bubble_set_batch
        bridge.bubble_set_batch = MagicMock()
        
        # Initialize debouncer with a small interval for testing
        debouncer = TelemetryDebouncer(bridge, flush_interval=0.1)
        
        try:
            # 1. Update multiple keys rapidly
            debouncer.update("node1_ActivePorts", ["Flow"])
            debouncer.update("node2_ActivePorts", ["In"])
            debouncer.update("node1_ActivePorts", ["True"]) # node1 should be overwritten
            
            # Wait for flush
            time.sleep(0.2)
            
            # Verify bubble_set_batch was called
            self.assertTrue(bridge.bubble_set_batch.called)
            
            # Check the content of the last call
            last_batch = bridge.bubble_set_batch.call_args[0][0]
            self.assertEqual(last_batch["node1_ActivePorts"], ["True"])
            self.assertEqual(last_batch["node2_ActivePorts"], ["In"])
            
            # 2. Verify subsequent flush clears buffer
            bridge.bubble_set_batch.reset_mock()
            time.sleep(0.2)
            # Should NOT be called if buffer is empty
            self.assertFalse(bridge.bubble_set_batch.called)
            
        finally:
            debouncer.stop()

    def test_bubble_set_fallback(self):
        # Setup mock bridge WITHOUT bubble_set_batch
        bridge = MagicMock()
        del bridge.bubble_set_batch
        bridge.bubble_set = MagicMock()
        
        debouncer = TelemetryDebouncer(bridge, flush_interval=0.1)
        
        try:
            debouncer.update("key1", "val1")
            time.sleep(0.2)
            
            # Should fallback to individual bubble_set calls
            self.assertTrue(bridge.bubble_set.called)
            bridge.bubble_set.assert_any_call("key1", "val1", "Telemetry")
            
        finally:
            debouncer.stop()

if __name__ == "__main__":
    unittest.main()
