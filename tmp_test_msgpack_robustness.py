import time
from multiprocessing import Manager
from multiprocessing import shared_memory
import msgpack
from axonpulse.core.bridge import AxonPulseBridge

def test_robustness():
    manager = Manager()
    bridge = AxonPulseBridge(manager)
    
    key = "robustness_test"
    val = {"a": 1, "b": 2}
    
    # 1. Write normally
    bridge.set(key, val)
    
    # Get metadata
    metadata = bridge._variables_registry.get(f"Global:{key}")
    shm_name = metadata[0]
    
    # 2. Corrupt SHM with extra data manually
    # We open the SHM and write the valid object + garbage
    shm = shared_memory.SharedMemory(name=shm_name)
    try:
        data_bytes = msgpack.packb(val)
        garbage = b"EXTRADATA" * 10
        total_data = data_bytes + garbage
        
        # If the shm is too small for our corruption, we'll just skip that part
        # but bridge.set should have created enough space or we can use a smaller corridor
        shm.buf[:len(total_data)] = total_data
        
        print(f"Injected {len(garbage)} bytes of garbage into SHM.")
    finally:
        shm.buf.release()
        shm.close()
    
    # 3. Try to read back with different payload_len scenarios
    
    # A) With CORRECT length (should use unpackb fast path)
    # We manually update registry to have the correct length of valid data
    bridge._variables_registry[f"Global:{key}"] = (shm_name, metadata[1], metadata[2], len(data_bytes))
    read_a = bridge.get(key)
    print(f"Read A (Correct Len): {read_a} - {'PASS' if read_a == val else 'FAIL'}")
    
    # B) With WRONG (larger) length (should trigger Unpacker fallback)
    bridge._variables_registry[f"Global:{key}"] = (shm_name, metadata[1], metadata[2], len(total_data))
    read_b = bridge.get(key)
    print(f"Read B (Extra Data): {read_b} - {'PASS' if read_b == val else 'FAIL'}")

    # C) With NONE length (should also trigger Unpacker or read whole buf)
    bridge._variables_registry[f"Global:{key}"] = (shm_name, metadata[1], metadata[2])
    read_c = bridge.get(key)
    print(f"Read C (No Len): {read_c} - {'PASS' if read_c == val else 'FAIL'}")

if __name__ == "__main__":
    test_robustness()
