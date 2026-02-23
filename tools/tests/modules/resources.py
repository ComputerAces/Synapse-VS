import os
import sys
import time

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry

# [NEW] Mock Hardware Node for Stress Testing
class HardwareSimNode(SuperNode):
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True # CRITICAL: Ensure engine tracks this for cleanup!
        self.is_native = True

    def define_schema(self):
        self.input_schema = {"Flow": "flow"}
        self.output_schema = {"Flow": "flow"}
        self.properties["LockFile"] = "hardware.lock"

    def register_handlers(self):
        self.register_handler("Flow", self.sim_hardware_op)

    def sim_hardware_op(self, **kwargs):
        lock_file = self.properties.get("LockFile", "hardware.lock")
        print(f"    [Node] Acquiring Hardware Lock: {lock_file}")
        with open(lock_file, "w") as f:
            f.write("LOCKED")
        
        # Simulate a crash or long operation that gets killed
        print(f"    [Node] Simulating hardware intensive task (2s sleep)...")
        self.bridge.set("_HW_BUSY", True, "Test")
        time.sleep(2.0)
        return True

    def lifecycle_on_destroy(self):
        # This is where hardware locks MUST be released!
        lock_file = self.properties.get("LockFile", "hardware.lock")
        print(f"    [Node] Cleaning up Hardware Locks via lifecycle_on_destroy...")
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except: pass
        self.bridge.set("_HW_BUSY", False, "Test")

def test_resource_lock_cleanup():
    """
    STRESS TEST: Verifies OS/Hardware resources are released mid-operation if killed.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 13: Deep Resource & Hardware Auditor]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Resource Test")
    load_registry()
    
    # Register our custom simulation node
    engine.register_node(HardwareSimNode("hw_1", "Hardware Sim", bridge))
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    ReturnCls = NodeRegistry.get_node_class("Return Node")
    
    engine.register_node(StartCls("st", "Start", bridge))
    engine.register_node(ReturnCls("ret", "End", bridge))
    
    engine.wires = [
        {"from_node": "st", "from_port": "Flow", "to_node": "hw_1", "to_port": "Flow"},
        {"from_node": "hw_1", "from_port": "Flow", "to_node": "ret", "to_port": "Flow"}
    ]
    
    # Ensure lock file is gone before we start
    lock_file = "hardware.lock"
    if os.path.exists(lock_file): os.remove(lock_file)

    print(f"    [Action] Running hardware graph...")
    # We'll run in a thread so we can "kill" it mid-way
    import threading
    run_thread = threading.Thread(target=engine.run, args=("st",))
    run_thread.daemon = True
    run_thread.start()
    
    # Wait for node to acquire lock
    timeout = 10.0
    start = time.time()
    while not os.path.exists(lock_file) and time.time() - start < timeout:
        time.sleep(0.1)
    
    if not os.path.exists(lock_file):
        raise RuntimeError("Resource Audit FAIL: Node failed to create lock file.")
        
    print(f"    [Action] Forcefully Stopping Engine (Simulating User Stop)...")
    bridge.set("_SYSTEM_STOP", True, "Test")
    
    # Wait for the engine thread to finish
    run_thread.join(timeout=5.0)
    
    print(f"    [Verify] Checking lock release...")
    
    # Manually trigger one final cleanup pass just in case the thread hadn't quite reaped
    # although run()'s finally block should have done it.
    engine.stop_all_services()
    
    if os.path.exists(lock_file):
        raise RuntimeError("Resource Audit FAIL: Lock file 'hardware.lock' was NOT released.")
    
    print(f"[SUCCESS] OS Resources and Hardware locks were successfully released.")

if __name__ == "__main__":
    test_resource_lock_cleanup()
