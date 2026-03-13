import time
from axonpulse.nodes.decorators import axon_node

@axon_node(category="Test")
def Sleep(seconds: float = 1.0):
    time.sleep(seconds)
    return True

@axon_node(category="Test")
def Result(value: str = "initial"):
    print(f"MOCK_RESULT_NODE: received value={value}")
    return value
