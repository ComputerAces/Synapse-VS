import time
import heapq
from collections import deque
from axonpulse.core.flow_controller import FlowController

def benchmark_queuing():
    print("\n--- FlowController Hybrid Queue Benchmark ---")
    
    # 1. Benchmark Default Priority (Deque O(1))
    fc_hybrid = FlowController("start")
    # Clear initial push
    fc_hybrid.pop()
    
    count = 100000
    
    start_time = time.time()
    for i in range(count):
        fc_hybrid.push(f"node_{i}", [], "Flow", priority=0)
    push_time = time.time() - start_time
    
    start_time = time.time()
    for _ in range(count):
        fc_hybrid.pop()
    pop_time = time.time() - start_time
    
    print(f"Hybrid (P=0): Push {count} items in {push_time:.4f}s")
    print(f"Hybrid (P=0): Pop  {count} items in {pop_time:.4f}s")
    print(f"Total Hybrid Time: {push_time + pop_time:.4f}s")

    # 2. Benchmark Elevated Priority (HeapQ O(log N))
    fc_legacy = FlowController("start")
    fc_legacy.pop()
    
    start_time = time.time()
    for i in range(count):
        fc_legacy.push(f"node_{i}", [], "Flow", priority=1) # Forced to legacy heap
    push_time_leg = time.time() - start_time
    
    start_time = time.time()
    for _ in range(count):
        fc_legacy.pop()
    pop_time_leg = time.time() - start_time
    
    print(f"\nLegacy (P=1): Push {count} items in {push_time_leg:.4f}s")
    print(f"Legacy (P=1): Pop  {count} items in {pop_time_leg:.4f}s")
    print(f"Total Legacy Time: {push_time_leg + pop_time_leg:.4f}s")
    
    improvement = ( (push_time_leg + pop_time_leg) / (push_time + pop_time) )
    print(f"\nSpeed Improvement: {improvement:.2f}x faster for default tasks!")

def test_ordering():
    print("\n--- Testing Priority Ordering ---")
    fc = FlowController("start")
    fc.pop() # Clear start
    
    # Push mixed priorities
    fc.push("low", [], "Flow", priority=-5)
    fc.push("high", [], "Flow", priority=10)
    fc.push("default", [], "Flow", priority=0)
    fc.push("higher", [], "Flow", priority=20)
    
    results = []
    while fc.has_next():
        node_id, _, _ = fc.pop()
        results.append(node_id)
        
    print(f"Ordering: {results}")
    expected = ["higher", "high", "default", "low"]
    if results == expected:
        print("PASS: Priority ordering is correct (High -> Default -> Low)")
    else:
        print(f"FAIL: Expected {expected}")

if __name__ == "__main__":
    test_ordering()
    benchmark_queuing()
