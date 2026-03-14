import time
import random
import threading
from axonpulse.core.bridge import AxonPulseBridge

def stress_test():
    from multiprocessing import Manager
    manager = Manager()
    bridge = AxonPulseBridge(manager)
    keys = [f"test_key_{i}" for i in range(10)]
    stop_event = threading.Event()

    def worker():
        while not stop_event.is_set():
            key = random.choice(keys)
            val = {"data": [1, 2, 3], "time": time.time()}
            try:
                # Test write (which uses _write_shm)
                bridge.set(key, val, "StressTest")
                # Test read (which uses get)
                got = bridge.get(key)
                
                # Test mutation (which uses mutate)
                bridge.mutate(key, "list_append", random.random())
                
            except Exception as e:
                print(f"Error during stress: {e}")
            
    threads = [threading.Thread(target=worker) for i in range(5)]
    for t in threads: t.start()
    
    print("Stress test running for 5 seconds...")
    time.sleep(5)
    stop_event.set()
    for t in threads: t.join()
    print("Stress test finished.")

if __name__ == "__main__":
    stress_test()
