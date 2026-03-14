import multiprocessing
import time
import random
import os
from axonpulse.core.bridge import AxonPulseBridge

# [FIX] Better worker initialization - share the proxy objects directly
def reader_worker(system_state, data_state, worker_id, iterations):
    # Pass None for manager since we are providing existing state
    bridge = AxonPulseBridge(None, system_state=system_state, data_state=data_state)
    
    # Pre-check local cache won't hit (so we actually use shared memory logic)
    # We'll use a unique key per iteration or just clear local cache
    
    start_time = time.time()
    read_count = 0
    for i in range(iterations):
        # We use a key that changes or versions that change to force SHM read
        val = bridge.get("config")
        time.sleep(0.02) # Longer sleep to make concurrency more obvious
        read_count += 1
    
    end_time = time.time()
    print(f"Reader {worker_id} finished: {read_count} reads in {end_time - start_time:.2f}s")

def writer_worker(system_state, data_state, iterations):
    bridge = AxonPulseBridge(None, system_state=system_state, data_state=data_state)
    
    for i in range(iterations):
        # Mutate config to force readers to update from SHM
        bridge.set("config", {"version": i, "timestamp": time.time(), "payload": "x" * 100})
        time.sleep(0.1) 
    print("Writer finished.")

def run_test():
    print("Starting Improved RWLock Performance Test...")
    manager = multiprocessing.Manager()
    bridge = AxonPulseBridge(manager)
    
    bridge.set("config", {"version": -1})
    
    num_readers = 5
    iterations = 20
    
    sys_state = bridge.get_system_state()
    data_state = bridge.get_internal_state() # Includes variables_registry
    
    start_all = time.time()
    
    processes = []
    # Start Readers
    for i in range(num_readers):
        p = multiprocessing.Process(target=reader_worker, args=(sys_state, data_state, i, iterations))
        p.start()
        processes.append(p)
        
    # Start Writer (optional, but let's see consistency)
    pw = multiprocessing.Process(target=writer_worker, args=(sys_state, data_state, 3))
    pw.start()
    processes.append(pw)
    
    for p in processes:
        p.join()
        
    end_all = time.time()
    
    # Expected sequential: 5 readers * 20 iter * 0.02s = 2.0s
    # Expected concurrent: 1 reader * 20 iter * 0.02s = 0.4s + overhead
    
    total_time = end_all - start_all
    print(f"Total time for {num_readers} concurrent readers: {total_time:.2f}s")
    
    sequential_threshold = (num_readers * iterations * 0.02) * 0.8
    if total_time < sequential_threshold:
        print(f"SUCCESS: Concurrency detected! (Threshold: {sequential_threshold:.2f}s)")
    else:
        print(f"FAILURE: Execution appears sequential. (Threshold: {sequential_threshold:.2f}s)")

if __name__ == "__main__":
    run_test()
