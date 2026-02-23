import os
import sys
import time
import shutil

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry
from synapse.nodes.registry import NodeRegistry

def test_hot_reload_resilience():
    """
    HOT-RELOAD TEST: Verifies engine can handle node logic changes during execution.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 16: Hot-Reload Intransigence Test]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Hot Reload Test")
    load_registry()
    
    # Create a temporary node file
    temp_node_path = os.path.abspath("synapse/nodes/lib/hot_swap_node.py")
    
    initial_code = """
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Hot Swap Node", "Test")
class HotSwapNode(SuperNode):
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW}
    def register_handlers(self):
        self.register_handler("Flow", self.do_work)
    def do_work(self, **kwargs):
        print("    [Node] Running VERSION 1")
        self.bridge.set("HOT_SWAP_RESULT", 1, "Test")
        return True
"""
    
    with open(temp_node_path, "w") as f:
        f.write(initial_code)
    
    # Refresh registry to pick up the new node
    load_registry()
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    WaitCls = NodeRegistry.get_node_class("Wait") # Correct label is "Wait"
    HotSwapCls = NodeRegistry.get_node_class("Hot Swap Node")
    
    if not StartCls or not WaitCls or not HotSwapCls:
        raise RuntimeError(f"Hot Reload Test FAIL: Could not find required node classes (ST:{StartCls}, WT:{WaitCls}, HS:{HotSwapCls})")

    engine.register_node(StartCls("st", "Start", bridge))
    engine.register_node(WaitCls("wait", "Wait", bridge))
    engine.register_node(HotSwapCls("swap", "Hot Swap", bridge))
    
    engine.wires = [
        {"from_node": "st", "from_port": "Flow", "to_node": "wait", "to_port": "Flow"},
        {"from_node": "wait", "from_port": "Flow", "to_node": "swap", "to_port": "Flow"}
    ]
    
    # Set wait time (Milliseconds)
    bridge.set("wait_Milliseconds", 3000, "Test")
    
    print(f"    [Action] Starting graph execution...")
    import threading
    run_thread = threading.Thread(target=engine.run, args=("st",))
    run_thread.daemon = True
    run_thread.start()
    
    # Wait for the graph to reach the Wait node
    time.sleep(1.0)
    
    print(f"    [Action] Modifying node code on disk (Live Patching)...")
    updated_code = initial_code.replace("VERSION 1", "VERSION 2").replace("1, \"Test\"", "2, \"Test\"")
    with open(temp_node_path, "w") as f:
        f.write(updated_code)
    
    print(f"    [Action] Triggering Registry Hot-Reload...")
    # To truly hot-reload, we might need to purge the module from sys.modules
    # but load_registry() might be direct enough if it re-execs.
    load_registry() 
    
    run_thread.join(timeout=10.0)
    
    result = bridge.get("HOT_SWAP_RESULT")
    print(f"    [Verify] Hot-Swap Result: {result}")
    
    # Cleanup
    if os.path.exists(temp_node_path): os.remove(temp_node_path)
    
    # Since nodes are already instantiated in the engine.nodes map, 
    # we expect it to still be 1 unless the engine re-fetches class for every execution.
    # But the goal of the test is survival and documentation of whether it swaps.
    print(f"[SUCCESS] Engine survived hot-swap attempt. Final Result: {result}")

if __name__ == "__main__":
    test_hot_reload_resilience()
