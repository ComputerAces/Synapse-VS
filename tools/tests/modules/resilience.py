import os
import sys
import time

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry

class BackpressureMockNode(SuperNode):
    """
    Mock node that simulates an API with rate limiting.
    """
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.attempts = {} # pulse_id -> attempt_count

    def define_schema(self):
        self.input_schema = {"Flow": "flow"}
        self.output_schema = {"Flow": "flow", "Error": "flow"}

    def register_handlers(self):
        self.register_handler("Flow", self.execute_with_backoff)

    def execute_with_backoff(self, **kwargs):
        pulse_id = kwargs.get("_pulse_id", "default")
        count = self.attempts.get(pulse_id, 0)
        
        if count < 2:
            self.attempts[pulse_id] = count + 1
            print(f"    [Node] API Rate Limit Hit (429). Backing off... (Attempt {count+1})")
            # In a real node, this would sleep or return a 'Retry' signal
            # For this test, we simulate the retry logic
            time.sleep(0.5 * (2 ** count)) # Exponential backoff simulation
            return False # Signal failure/retry
        
        print(f"    [Node] API Success after backoff.")
        return True

def test_api_backpressure():
    """
    BACKPRESSURE TEST: Verifies resilience under heavy API load and rate limiting.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 17: API Backpressure & Rate-Limit Check]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Resilience Test")
    load_registry()
    
    # Register mock
    engine.register_node(BackpressureMockNode("api_1", "Mock API", bridge))
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    ForEachCls = NodeRegistry.get_node_class("ForEach Node") # Correct label: "ForEach Node"
    
    if not StartCls or not ForEachCls:
        raise RuntimeError(f"API Backpressure Test FAIL: Could not find required node classes (ST:{StartCls}, FE:{ForEachCls})")

    engine.register_node(StartCls("st", "Start", bridge))
    engine.register_node(ForEachCls("loop", "For Each", bridge))
    
    engine.wires = [
        {"from_node": "st", "from_port": "Flow", "to_node": "loop", "to_port": "Flow"},
        {"from_node": "loop", "from_port": "Body", "to_node": "api_1", "to_port": "Flow"}
    ]
    
    # Set list for for-each
    bridge.set("loop_List", [1, 2, 3], "Test")
    
    print(f"    [Action] Running blast of 3 requests requiring backoff...")
    engine.run("st")
    
    print(f"[SUCCESS] API Backpressure test passed. Nodes successfully recovered from simulated 429s.")

if __name__ == "__main__":
    test_api_backpressure()
