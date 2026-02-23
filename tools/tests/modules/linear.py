import time
from synapse.nodes.registry import NodeRegistry
from .base import setup_engine

def test_linear_flow():
    bridge, engine = setup_engine("STAGE 1: Linear Flow Test")
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    DebugCls = NodeRegistry.get_node_class("Debug Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    n1 = StartCls("start_1", "Main Start", bridge)
    n2 = DebugCls("debug_1", "Log Something", bridge)
    n3 = ReturnCls("ret_1", "Function Return", bridge)
    
    for n in [n1, n2, n3]:
        engine.register_node(n)
        
    engine.connect("start_1", "Flow", "debug_1", "Flow")
    engine.connect("debug_1", "Flow", "ret_1", "Flow")
    
    print("[RUNNING] Injecting Pulse into Start Node...")
    st = time.time()
    engine.run("start_1")
    print(f"[SUCCESS] Linear flow completed in {time.time() - st:.3f}s\n")
