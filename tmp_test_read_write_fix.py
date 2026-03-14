import multiprocessing
import os
from axonpulse.core.bridge import AxonPulseBridge
from axonpulse.nodes.filesystem.read_node import ReadNode
from axonpulse.nodes.filesystem.write_node import WriteNode

def test_file_nodes():
    print("Testing Decorated File Nodes (Fix Verification)...")
    manager = multiprocessing.Manager()
    bridge = AxonPulseBridge(manager)
    
    # Mocking _node and _bridge as passed by the engine
    test_path = "tmp_fix_test.txt"
    test_data = "Hello from decorated node fix!"
    
    # Mock node object
    class MockNode:
        def __init__(self):
            self.name = "TestNode"
            self.node_id = "test_id"
            self.properties = {}
            from axonpulse.utils.logger import setup_logger
            self.logger = setup_logger("TestNode")
            self.is_hijacked = False
        def get_provider_id(self, provider): return None

    mock_node = MockNode()

    try:
        # 1. Test WriteNode
        print("Executing WriteNode...")
        res_write = WriteNode(
            Data=test_data, 
            Path=test_path, 
            Mode='Overwrite', 
            _bridge=bridge, 
            _node=mock_node, 
            _node_id=mock_node.node_id
        )
        print(f"WriteNode Result: {res_write}")
        
        if not os.path.exists(test_path):
            print("FAILURE: File not written.")
            return

        # 2. Test ReadNode
        print("Executing ReadNode...")
        res_read = ReadNode(
            Path=test_path, 
            _bridge=bridge, 
            _node=mock_node, 
            _node_id=mock_node.node_id
        )
        print(f"ReadNode Result: {res_read}")
        
        if res_read.get('Data') == test_data:
            print("SUCCESS: Decorated nodes functional without 'self'.")
        else:
            print(f"FAILURE: Data mismatch. Expected '{test_data}', got '{res_read.get('Data')}'")

    finally:
        if os.path.exists(test_path):
            os.remove(test_path)
        manager.shutdown()

if __name__ == "__main__":
    test_file_nodes()
