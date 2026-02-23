import time
import threading
from synapse.nodes.registry import NodeRegistry
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.types import DataType
from .base import setup_engine

class TestWorkerProvider(ProviderNode):
    """Mock Provider that spawns a background thread to verify cleanup."""
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "TestWorker"
        self._running = False
        self._thread = None
        self.cleanup_called = False

    def start_scope(self, **kwargs):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        return super().start_scope(**kwargs)

    def _worker(self):
        while self._running:
            time.sleep(0.1)

    def cleanup_provider_context(self):
        self._running = False
        self.cleanup_called = True
        if self._thread:
            self._thread.join(timeout=1.0)
        super().cleanup_provider_context()

def test_orphan_cleanup():
    bridge, engine = setup_engine("STAGE 7: Orphan Thread & Lifecycle Cleanup")
    
    # 1. Register Mock Provider
    provider_id = "lifecycle_prov"
    n_prov = TestWorkerProvider(provider_id, "Test Provider", bridge)
    engine.register_node(n_prov)
    
    # 2. Get Standard Nodes
    StartCls = NodeRegistry.get_node_class("Start Node")
    TryCls = NodeRegistry.get_node_class("Try Node")
    DivideCls = NodeRegistry.get_node_class("Divide")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    n_start = StartCls("l_start", "Start", bridge)
    n_try = TryCls("l_try", "Try", bridge)
    n_div = DivideCls("l_div", "Crasher", bridge)
    n_ret = ReturnCls("l_ret", "Recovery", bridge)
    
    # Configure Crasher (1 / 0)
    n_div.properties["A"] = 1
    n_div.properties["B"] = 0
    
    for n in [n_start, n_try, n_div, n_ret]:
        engine.register_node(n)
        
    # 3. Wire Graph
    # Start -> Try -> Provider -> Divide (Crash)
    # Try.Catch -> Return
    engine.connect("l_start", "Flow", "l_try", "Flow")
    engine.connect("l_try", "Flow", "lifecycle_prov", "Flow")
    engine.connect("lifecycle_prov", "Provider Flow", "l_div", "Flow")
    engine.connect("l_try", "Catch", "l_ret", "Flow")
    
    print("    [Action] Running graph with intentional crash inside Provider Scope...")
    engine.run("l_start")
    
    # Give engine a moment to process cleanup
    time.sleep(0.5)
    
    # 4. Verify Cleanup
    print("    [Verify] Checking if Provider thread was successfully reaped...")
    if n_prov.cleanup_called and not n_prov._running:
        print("      - SUCCESS: Provider.cleanup_provider_context() was executed.")
    else:
        error_msg = f"Orphan Thread Detected! Provider cleanup was NOT called. Running={n_prov._running}"
        print(f"      - FAILURE: {error_msg}")
        raise RuntimeError(error_msg)
        
    # Check if recovery path worked too
    if bridge.get("l_ret_Flow") is not None:
         print("      - SUCCESS: Recovery path (Try/Catch) completed.")
    else:
         print("      - WARNING: Recovery path did not fire, but cleanup might have still succeeded.")

    print("[SUCCESS] Context Manager successfully tore down background threads after scope crash.\n")
    return True
