import time
import concurrent.futures
import random
import os
import sys

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import get_shared_manager, setup_engine
from synapse.core.bridge import SynapseBridge

def test_concurrency_blast():
    """
    STRESS TEST: Simulates 10,000 parallel pulses hitting the bridge at speed.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 9: Concurrency Blast]")
    print(f"{'='*50}")
    
    manager = get_shared_manager()
    bridge = SynapseBridge(manager)
    
    NUM_ITERATIONS = 10000
    CONCURRENT_THREADS = 50 # Simulate high worker pool pressure
    
    print(f"    [Action] Executing {NUM_ITERATIONS} parallel 'set' operations...")
    
    start_time = time.time()
    
    def worker(idx):
        # We use random keys to increase lock contention across hash buckets
        key = f"StressVar_{random.randint(0, 50)}"
        val = f"Value_{idx}"
        bridge.set(key, val, scope_id="StressTest")
        # Immediate read-back to check for corruption
        ret = bridge.get(key, scope_id="StressTest")
        return ret.startswith("Value_")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        futures = [executor.submit(worker, i) for i in range(NUM_ITERATIONS)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    duration = time.time() - start_time
    success_count = sum(results)
    
    print(f"    [Verify] Checking results...")
    print(f"      - OPS: {NUM_ITERATIONS}")
    print(f"      - THREADS: {CONCURRENT_THREADS}")
    print(f"      - SUCCESS: {success_count}/{NUM_ITERATIONS}")
    print(f"      - DURATION: {duration:.3f}s ({(NUM_ITERATIONS/duration):.1f} ops/sec)")
    
    if success_count < NUM_ITERATIONS:
        raise RuntimeError(f"Concurrency Blast FAIL: Only {success_count} ops succeeded.")
    
    print(f"[SUCCESS] IPC Bridge survived the concurrency blast.")

def test_heavy_payload():
    """
    STRESS TEST: Verifies that massive data transit doesn't choke serialization or RAM.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 10: Heavy Payload Test]")
    print(f"{'='*50}")
    
    manager = get_shared_manager()
    bridge = SynapseBridge(manager)
    
    # Create ~20MB of dummy data (Nested dict with strings)
    print(f"    [Action] Generating 20MB payload...")
    payload_size = 20 * 1024 * 1024 # 20MB
    large_string = "X" * 1024
    num_elements = payload_size // 1024
    
    heavy_data = {f"Item_{i}": large_string for i in range(num_elements)}
    
    print(f"    [Action] Transiting payload across bridge...")
    start_time = time.time()
    bridge.set("HeavyData", heavy_data, scope_id="StressTest")
    write_time = time.time() - start_time
    
    print(f"    [Action] Reading back payload...")
    start_time = time.time()
    read_data = bridge.get("HeavyData", scope_id="StressTest")
    read_time = time.time() - start_time
    
    print(f"    [Verify] Validating integrity...")
    is_valid = (len(read_data) == len(heavy_data))
    
    print(f"      - PAYLOAD SIZE: ~{payload_size / (1024*1024):.1f} MB")
    print(f"      - WRITE TIME: {write_time:.3f}s")
    print(f"      - READ TIME: {read_time:.3f}s")
    print(f"      - INTEGRITY: {'PASS' if is_valid else 'FAIL'}")
    
    if not is_valid:
        raise RuntimeError("Heavy Payload FAIL: Data corruption or truncation detected.")
    
    print(f"[SUCCESS] Heavy Payload transit completed successfully.")
