import time
from synapse.core.bridge import SynapseBridge
from synapse.core.engine import ExecutionEngine
from .base import setup_engine, get_shared_manager

def test_scope_bleed():
    print(f"\n{'='*50}")
    print(f"[STAGE 8: Scope Bleed & Isolation]")
    print(f"{'='*50}")
    
    manager = get_shared_manager()
    shared_registry = manager.dict()
    
    # We want to test if two bridges sharing the same registry stay isolated
    # We manually inject the shared registry to simulate a single engine database
    bridgeA = SynapseBridge(manager)
    bridgeA._variables_registry = shared_registry
    bridgeB = SynapseBridge(manager)
    bridgeB._variables_registry = shared_registry
    
    # Initialize Engines with different "Source Files" to trigger automatic scoping
    engineA = ExecutionEngine(bridgeA, headless=True, source_file="Graph_A.syp")
    engineB = ExecutionEngine(bridgeB, headless=True, source_file="Graph_B.syp")
    
    print("    [Action] Setting 'SharedVar' in Engine A (Scope: Graph_A)...")
    bridgeA.set("SharedVar", "Value_From_A")
    
    print("    [Action] Setting 'SharedVar' in Engine B (Scope: Graph_B)...")
    bridgeB.set("SharedVar", "Value_From_B")
    
    print("    [Verify] Checking isolation...")
    valA = bridgeA.get("SharedVar")
    valB = bridgeB.get("SharedVar")
    
    print(f"      - Engine A retrieved: {valA}")
    print(f"      - Engine B retrieved: {valB}")
    
    if valA == "Value_From_A" and valB == "Value_From_B":
        print("      - SUCCESS: Variables are correctly isolated by Scope ID.")
    else:
        error_msg = f"Scope Bleed! Values: A={valA}, B={valB}"
        print(f"      - FAILURE: {error_msg}")
        raise RuntimeError(error_msg)

    # Test Global inheritance
    print("    [Action] Setting 'GlobalVar' in Bridge A explicitly as Global...")
    bridgeA.set("GlobalVar", "CommonValue", scope_id="Global")
    
    print("    [Verify] Checking Global inheritance in Bridge B...")
    valGlobal = bridgeB.get("GlobalVar")
    print(f"      - Bridge B retrieved Global: {valGlobal}")
    
    if valGlobal == "CommonValue":
        print("      - SUCCESS: Global variables are accessible across scopes.")
    else:
        print("      - FAILURE: Global variable not found in sibling scope.")
        raise RuntimeError("Global Inheritance Failure")

    # Final check of the raw registry
    print("    [Verify] Checking raw Registry keys...")
    all_keys = bridgeA.get_all_keys()
    has_A = any(k.startswith("Graph_A:") for k in all_keys)
    has_B = any(k.startswith("Graph_B:") for k in all_keys)
    
    if has_A and has_B:
        print("      - SUCCESS: Registry contains correctly prefixed keys.")
    else:
        print(f"      - FAILURE: Missing prefixed keys. Keys: {all_keys}")
        raise RuntimeError("Registry Prefixing Failure")

    print("[SUCCESS] Scope Isolation maintained. Variable bleed prevented.\n")
    return True
