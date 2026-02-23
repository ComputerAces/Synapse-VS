import sys
import os
import time

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from synapse.core.bridge import SynapseBridge
from synapse.core.engine.execution_engine import ExecutionEngine
from synapse.nodes.registry import NodeRegistry

import multiprocessing

_shared_manager = None

def get_shared_manager():
    global _shared_manager
    if _shared_manager is None:
        _shared_manager = multiprocessing.Manager()
    return _shared_manager

# Named functions for pickling compatibility
def _mock_cleanup_all(): pass
def _mock_save_state(): pass

def setup_engine(test_name):
    print(f"\n{'='*50}")
    print(f"[{test_name}] - Initializing Engine")
    print(f"{'='*50}")
    
    # Prevent the global cleanup manager from nuking our Singleton Manager background process
    from synapse.utils.cleanup import CleanupManager
    CleanupManager.cleanup_all = _mock_cleanup_all
    
    manager = get_shared_manager()
    bridge = SynapseBridge(manager)
    # Suppress verbose trace logs in headless mode
    engine = ExecutionEngine(bridge, headless=True, trace=False)
    bridge.save_state = _mock_save_state
    
    # Inject a progress tracker into the dispatcher
    original_dispatch = engine.dispatcher.dispatch
    def logging_dispatch(node, inputs, stack):
        print(f"    -> Executing Node: '{node.name}' (ID: {node.node_id}) | Type: {type(node).__name__}")
        return original_dispatch(node, inputs, stack)
    engine.dispatcher.dispatch = logging_dispatch
    
    return bridge, engine

def load_registry():
    """Initializes the node backend."""
    import glob
    # We must load python files dynamically since NodeRegistry.load_nodes might not exist universally if not using loader
    nodes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'synapse', 'nodes', 'lib'))
    sys.path.insert(0, os.path.dirname(nodes_dir))
    
    # Find all Python files in the directory
    for filepath in glob.glob(os.path.join(nodes_dir, "*.py")):
        if not os.path.basename(filepath).startswith("__"):
             module_name = f"synapse.nodes.lib.{os.path.basename(filepath)[:-3]}"
             try:
                 __import__(module_name)
             except Exception as e:
                 print(f"Error loading node module {module_name}: {e}")
