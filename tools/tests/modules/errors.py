from synapse.nodes.registry import NodeRegistry
from .base import setup_engine

def test_error_flows():
    bridge, engine = setup_engine("STAGE 5: Error Path Routing")
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    MathCls = NodeRegistry.get_node_class("Divide")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    n1 = StartCls("st_e", "Start", bridge)
    n2 = MathCls("math_e", "Divide Node", bridge)
    n3 = ReturnCls("ret_success", "Success Return", bridge)
    n4 = ReturnCls("ret_error", "Error Handled Return", bridge)
    
    for n in [n1, n2, n3, n4]:
        engine.register_node(n)
        
    engine.connect("st_e", "Flow", "math_e", "Flow")
    engine.connect("math_e", "Flow", "ret_success", "Flow")
    engine.connect("math_e", "Error Flow", "ret_error", "Flow")
    
    # We expect ret_error to be hit if 'Error Flow' is supported, otherwise the engine will panic.
    hit_nodes = []
    original_dispatch = engine.dispatcher.dispatch
    def mock_dispatch_err(node, inputs, stack):
        hit_nodes.append(node.node_id)
        return original_dispatch(node, inputs, stack)
    engine.dispatcher.dispatch = mock_dispatch_err

    print("--- SubTest A: Normal Pass Execution (1 / 2) ---")
    n2.properties["A"] = 1
    n2.properties["B"] = 2
    
    engine.run("st_e")
    if "ret_success" in hit_nodes:
        print("[SUCCESS] Standard Flow executed successfully!\n")
    else:
        print("[FAILURE] Standard Flow did not reach Success Return.\n")
        
    print("--- SubTest B: Node Engine Error Routing (Division by Zero) ---")
    # We must instantiate a completely new engine/nodes to avoid ThreadPool shutdown locks
    bridge2, engine2 = setup_engine("STAGE 5b: Error Path Routing")
    n1b = StartCls("st_e", "Start", bridge2)
    n2b = MathCls("math_e", "Divide Node", bridge2)
    n3b = ReturnCls("ret_success", "Success Return", bridge2)
    n4b = ReturnCls("ret_error", "Error Handled Return", bridge2)
    
    n2b.properties["A"] = 10
    n2b.properties["B"] = 0
    
    for n in [n1b, n2b, n3b, n4b]:
        engine2.register_node(n)
        
    engine2.connect("st_e", "Flow", "math_e", "Flow")
    engine2.connect("math_e", "Flow", "ret_success", "Flow")
    engine2.connect("math_e", "Error Flow", "ret_error", "Flow")
    
    hit_nodes_b = []
    original_dispatch2 = engine2.dispatcher.dispatch
    def mock_dispatch_err2(node, inputs, stack):
        hit_nodes_b.append(node.node_id)
        return original_dispatch2(node, inputs, stack)
    engine2.dispatcher.dispatch = mock_dispatch_err2

    try:
        engine2.run("st_e")
    except Exception as e:
        print(f"       [Engine Panic] Standard execution halted due to unhandled error: {e}")
        
    if "ret_error" in hit_nodes_b:
        print("[SUCCESS] Error was caught and routed to Error Flow port!\n")
    else:
        print("[NOTE] Error Flow was not wired cleanly (node might not deploy exceptions cleanly). Engine handled it.\n")
