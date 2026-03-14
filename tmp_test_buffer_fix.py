import multiprocessing
import time
from multiprocessing import shared_memory
from axonpulse.core.bridge import AxonPulseBridge

def worker(bridge_state):
    # Re-init bridge in child process
    manager = multiprocessing.Manager()
    bridge = AxonPulseBridge(manager)
    bridge.__dict__.update(bridge_state)
    
    for _ in range(100):
        # Repeatedly read data to trigger the previous BufferError
        data = bridge.get("test_key")
        if data is None:
            print("Worker: Read None")
        time.sleep(0.001)

def run_test():
    print("Starting BufferError verification test...")
    manager = multiprocessing.Manager()
    bridge = AxonPulseBridge(manager)
    
    # Large data to ensure buffer logic is hit
    large_data = {"data": "x" * 1024 * 10, "list": list(range(1000))}
    bridge.set("test_key", large_data)
    
    # Start worker processes
    processes = []
    for _ in range(5):
        p = multiprocessing.Process(target=worker, args=(bridge.get_internal_state(),))
        p.start()
        processes.append(p)
    
    # Mutate data while worker is reading
    for i in range(50):
        bridge.set("test_key", {"update": i, "content": "y" * 1000})
        time.sleep(0.01)
        
    for p in processes:
        p.join()
        
    print("Test Completed without crashes.")

if __name__ == "__main__":
    run_test()
