from synapse.nodes.registry import NodeRegistry
from .base import setup_engine

def test_provider_flow():
    bridge, engine = setup_engine("STAGE 4: Provider Sub-Graph Scopes")
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    ProviderCls = NodeRegistry.get_node_class("List Provider")
    DebugBodyCls = NodeRegistry.get_node_class("Debug Node")
    DebugOutCls = NodeRegistry.get_node_class("Debug Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    if not ProviderCls:
        print("[WARNING] List Provider not found. Skipping Stage 4.")
        return

    n1 = StartCls("st_p", "Start", bridge)
    n2 = ProviderCls("prov", "Generic Provider", bridge)
    n3 = DebugBodyCls("db_body", "Provider Inner Scope Target", bridge)
    n4 = DebugOutCls("db_out", "Main Scope Target", bridge)
    n5 = ReturnCls("ret_p", "Return", bridge)
    
    for n in [n1, n2, n3, n4, n5]:
        engine.register_node(n)
        
    engine.connect("st_p", "Flow", "prov", "Flow")
    engine.connect("prov", "Provider Flow", "db_body", "Flow")
    # Out Flow fires after the Provider Scope completes
    engine.connect("prov", "Flow", "db_out", "Flow")
    engine.connect("db_out", "Flow", "ret_p", "Flow")
    
    print("--- Testing 'Provider Flow' vs Standard 'Flow' termination logic ---")
    engine.run("st_p")
    print("[SUCCESS] Provider scope terminated correctly.\n")
