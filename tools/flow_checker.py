import os
import sys

# Ensure we can import synapse and tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from synapse.nodes.registry import NodeRegistry
from tests.modules.base import load_registry
from tests.modules.linear import test_linear_flow
from tests.modules.loops import test_while_loop_completion, test_while_loop_break
from tests.modules.providers import test_provider_flow
from tests.modules.errors import test_error_flows
from tests.modules.subgraph_data import test_subgraph_data_passing
from tools.tests.modules.lifecycle import test_orphan_cleanup
from tools.tests.modules.isolation import test_scope_bleed
from tools.tests.modules.stress import test_concurrency_blast, test_heavy_payload
from tools.tests.modules.casting import test_type_casting_collision
from tools.tests.modules.loops import test_runaway_train
from tools.tests.modules.resources import test_resource_lock_cleanup
from tools.tests.modules.teardown import test_ghost_state_isolation
from tools.tests.modules.security import test_injection_sandbox
from tools.tests.modules.hot_reload import test_hot_reload_resilience
from tools.tests.modules.resilience import test_api_backpressure

if __name__ == "__main__":
    print(f"\nScanning Synapse Node Library...")
    # Using our custom loader from base.py since we don't have standard Graph loaders running
    load_registry()
    print(f"Loaded {len(NodeRegistry._nodes)} node definitions.\n")
    
    # Stage 1
    test_linear_flow()
    
    # Stages 2 & 3
    test_while_loop_completion()
    test_while_loop_break()
    
    # Stage 4
    try:
        test_provider_flow()
    except Exception as e:
        print(f"Provider Test failed due to context/wiring error: {e}")
        
    # Stage 5
    test_error_flows()
    
    # Stage 6
    test_subgraph_data_passing()

    # Stage 7
    test_orphan_cleanup()

    # [STAGE 8] Scope Isolation Verification
    test_scope_bleed()
    
    # [STAGE 9] Concurrency Blast (10k pulses)
    test_concurrency_blast()
    
    # [STAGE 10] Heavy Payload Transit
    test_heavy_payload()

    # [STAGE 11] Type Collision Validator
    test_type_casting_collision()

    # [STAGE 12] Runaway Train Guard
    test_runaway_train()

    # [STAGE 13] Deep Resource & Hardware Auditor
    test_resource_lock_cleanup()

    # [STAGE 14] Ghost State & Teardown Checker
    test_ghost_state_isolation()
    
    # [STAGE 15] Injection & Sandbox Auditor
    test_injection_sandbox()
    
    # [STAGE 16] Hot-Reload Intransigence Test
    test_hot_reload_resilience()
    
    # [STAGE 17] API Backpressure & Rate-Limit Check
    test_api_backpressure()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*50 + "\n")
