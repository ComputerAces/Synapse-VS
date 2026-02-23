import os
import sys
import time

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry

def test_ghost_state_isolation():
    """
    STRESS TEST: Ensures the bridge is perfectly flushed between graph restarts.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 14: Ghost State & Teardown Checker]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Teardown Test")
    
    print(f"    [Action] Populating bridge with dynamic 'ghost' state...")
    for i in range(50):
        bridge.set(f"GhostVar_{i}", f"Value_{i}", "Run_1")
    
    initial_key_count = len(bridge.get_all_keys())
    print(f"    [Verify] Run 1 Key Count: {initial_key_count}")
    
    print(f"    [Action] Halting execution and flushing bridge...")
    # The 'clear()' method should be the one responsible for this
    bridge.clear()
    
    post_clear_count = len(bridge.get_all_keys())
    print(f"    [Verify] Post-Clear Key Count: {post_clear_count}")
    
    if post_clear_count > 0:
         # Some hidden system keys might exist depending on bridge init, 
         # but our GhostVar_ keys must be gone.
         keys = bridge.get_all_keys()
         ghosts = [k for k in keys if "GhostVar" in k]
         if ghosts:
             raise RuntimeError(f"Ghost State FAIL: Found {len(ghosts)} surviving variables from Run 1.")

    print(f"    [Action] Starting Run 2...")
    bridge.set("FreshVar", "Clean", "Run_2")
    
    if bridge.get("GhostVar_0") is not None:
        raise RuntimeError("Ghost State FAIL: Variable 'GhostVar_0' leaked into Run 2.")
    
    print(f"[SUCCESS] Execution isolation guaranteed. No ghost state detected across restarts.")

if __name__ == "__main__":
    test_ghost_state_isolation()
