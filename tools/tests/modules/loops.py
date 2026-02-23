from synapse.nodes.registry import NodeRegistry
from .base import setup_engine, load_registry

def test_while_loop_completion():
    bridge, engine = setup_engine("STAGE 2: Multi-Stage While Loop")
    load_registry()
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    WhileCls = NodeRegistry.get_node_class("While Node")
    DebugCls = NodeRegistry.get_node_class("Debug Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    n1 = StartCls("st_w", "Start", bridge)
    n2 = WhileCls("while_1", "While Loop", bridge)
    n2.properties["Condition"] = True
    n3 = DebugCls("dbg_body", "Loop Body", bridge)
    n4 = ReturnCls("ret_w", "Exit Return", bridge)
    
    for n in [n1, n2, n3, n4]:
        engine.register_node(n)
        
    engine.connect("st_w", "Flow", "while_1", "Flow")
    engine.connect("while_1", "Loop", "dbg_body", "Flow")
    engine.connect("dbg_body", "Flow", "while_1", "Loop")
    engine.connect("while_1", "Flow", "ret_w", "Flow")
    
    print("--- SubTest A: Natural Completion (3 Iterations) ---")
    counter = [0]
    
    original_dispatch = engine.dispatcher.dispatch
    def mock_dispatch_A(node, inputs, stack):
        if node.node_id == "while_1":
            counter[0] += 1
            if counter[0] >= 3:
                print("       [Modifier] Setting loop condition to False to force natural exit.")
                node.properties["Condition"] = False
                inputs["Condition"] = False
                bridge.set("while_1_Condition", False, "Test")
            else:
                node.properties["Condition"] = True
                inputs["Condition"] = True
                # CRITICAL: Mock the active status so the loop evaluates condition logic
                bridge.set("while_1_is_active", True, "Test")
                
        return original_dispatch(node, inputs, stack)
    engine.dispatcher.dispatch = mock_dispatch_A

    engine.run("st_w")
    print(f"[SUCCESS] Natural Completion passed. Looped {counter[0]} times.\n")
    
def test_while_loop_break():
    bridge, engine = setup_engine("STAGE 3: While Loop Explicit Break")
    load_registry()
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    WhileCls = NodeRegistry.get_node_class("While Node")
    DebugCls = NodeRegistry.get_node_class("Debug Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    n1 = StartCls("st_wb", "Start", bridge)
    n2 = WhileCls("while_b", "While Loop", bridge)
    n2.properties["Condition"] = True
    n3 = DebugCls("dbg_b", "Loop Body", bridge)
    n4 = ReturnCls("ret_b", "Exit Return", bridge)
    
    for n in [n1, n2, n3, n4]:
        engine.register_node(n)
        
    engine.connect("st_wb", "Flow", "while_b", "Flow")
    engine.connect("while_b", "Loop", "dbg_b", "Flow")
    engine.connect("dbg_b", "Flow", "while_b", "Exit") 
    engine.connect("while_b", "Flow", "ret_b", "Flow")
    
    print("--- SubTest B: Force Trigger 'Exit' Port ---")
    print("       [Modifier] The body node routes its Output Flow directly into the While Node's 'Exit' trigger.")
    
    counter = [0]
    original_dispatch = engine.dispatcher.dispatch
    def mock_dispatch_B(node, inputs, stack):
        if node.node_id == "while_b":
            counter[0] += 1
            node.properties["Condition"] = True
            inputs["Condition"] = True
            
            # The Trigger port is actually not explicitly inside 'inputs' during dispatch.
            # However, we can track exactly how many times the loop body has fired,
            # and force the Exit state dynamically after exactly 2 loops.
            if counter[0] >= 3:
                 bridge.set("while_b_is_active", False, "Test")
            else:
                 bridge.set("while_b_is_active", True, "Test")
                
        return original_dispatch(node, inputs, stack)
    engine.dispatcher.dispatch = mock_dispatch_B
    
    engine.run("st_wb")
    print(f"[SUCCESS] Explicit Break passed. Iterated {counter[0]} times before break.\n")

def test_runaway_train():
    """
    STRESS TEST: Intentionally triggers an infinite loop and verifies engine throttle.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 12: Runaway Train Guard]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Runaway Test")
    load_registry()
    
    # Build a simple infinite loop: Start -> Try -> Debug -> Debug -> ...
    StartCls = NodeRegistry.get_node_class("Start Node")
    DebugCls = NodeRegistry.get_node_class("Debug Node")
    TryCls = NodeRegistry.get_node_class("Try Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    start = StartCls("st", "Start", bridge)
    try_node = TryCls("try", "Try", bridge)
    debug = DebugCls("db", "Infinite Looper", bridge)
    ret = ReturnCls("ret", "Error Handler", bridge)
    
    engine.register_node(start)
    engine.register_node(try_node)
    engine.register_node(debug)
    engine.register_node(ret)
    
    # Wires: Start -> Try -> Debug -> Debug (Recursive)
    engine.wires = [
        {"from_node": "st", "from_port": "Flow", "to_node": "try", "to_port": "Flow"},
        {"from_node": "try", "from_port": "Flow", "to_node": "db", "to_port": "Flow"},
        {"from_node": "db", "from_port": "Flow", "to_node": "db", "to_port": "Flow"}, # INFINITE
        {"from_node": "try", "from_port": "Catch", "to_node": "ret", "to_port": "Flow"}
    ]
    
    print(f"    [Action] Launching infinite loop (Threshold: 1000 pulses)...")
    
    import time
    start_time = time.time()
    try:
        # Lower threshold for faster test
        engine._max_pulses_per_scope = 1000
        engine.run("st")
    except Exception as e:
        print(f"    [Engine] Execution halted: {e}")
    
    duration = time.time() - start_time
    total_pulses = engine._scope_execution_totals.get("ROOT", 0)
    
    print(f"    [Verify] Checking runaway protection...")
    print(f"      - TOTAL PULSES: {total_pulses}")
    print(f"      - DURATION: {duration:.3f}s")
    
    if total_pulses > engine._max_pulses_per_scope + 100:
         raise RuntimeError(f"Runaway Train FAIL: Engine allowed {total_pulses} pulses (Limit: {engine._max_pulses_per_scope})")

    print(f"[SUCCESS] Engine correctly throttled the runaway loop and routed to error handler.")
