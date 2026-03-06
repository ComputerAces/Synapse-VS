import multiprocessing
import time
import os
import shutil
from axonpulse.core.bridge import AxonPulseBridge
from axonpulse.nodes import discover_plugins
from axonpulse.nodes.registry import NodeRegistry

def test_zip_ecosystem():
    print("\n--- AxonPulse Zip Ecosystem Verification ---\n")
    
    # 1. Setup Bridge
    manager = multiprocessing.Manager()
    bridge = AxonPulseBridge(manager)
    
    # 2. Cleanup old extractions to force new ones
    extract_base = os.path.join("plugins", "extracted")
    if os.path.exists(extract_base):
        shutil.rmtree(extract_base)
    
    # 3. Simulate UI password response for the locked zip
    # We need to wait for the request to appear, then provide the password.
    # In a real system, the UI does this. Here we'll use a background thread or just pre-empt it.
    
    def mock_ui_response():
        time.sleep(2) # Wait for discover_plugins to hit the encrypted zip
        keys = bridge.get_all_keys()
        for key in keys:
            if "AssetPasswordRequest" in key:
                req_id = key.split(":")[-1]
                print(f"[Mock UI] Found password request (ID: {req_id}). Providing password...")
                bridge.bubble_set(f"AssetPasswordResponse:{req_id}", {
                    "path": "plugins/test_pkg_locked.zip",
                    "password": "secret123"
                })
                return
        print("[Mock UI] No password request found!")

    import threading
    threading.Thread(target=mock_ui_response, daemon=True).start()

    # 4. Run Discovery
    print("[Test] Running discover_plugins with bridge...")
    discover_plugins(bridge)
    
    # 5. Verify Registration
    time.sleep(1) # Wait for possible async registry updates
    all_nodes = NodeRegistry._nodes.keys()
    
    print("\n[Test] Verification Results:")
    print(f" - Zip Test Node (Open): {'FOUND' if 'Zip Test Node' in all_nodes else 'MISSING'}")
    print(f" - Zip Locked Node: {'FOUND' if 'Zip Locked Node' in all_nodes else 'MISSING'}")
    
    # Check if files were extracted
    open_extracted = os.path.join(extract_base, "test_pkg_open", "test_node_open.spy")
    locked_extracted = os.path.join(extract_base, "test_pkg_locked", "test_node_locked.spy")
    
    print(f" - Open Extraction: {'OK' if os.path.exists(open_extracted) else 'FAILED'}")
    print(f" - Locked Extraction: {'OK' if os.path.exists(locked_extracted) else 'FAILED'}")

    if 'Zip Test Node' in all_nodes and 'Zip Locked Node' in all_nodes:
        print("\n[SUCCESS] Password Zip Ecosystem is fully functional! 🏆")
    else:
        print("\n[FAILURE] One or more components failed discovery.")

if __name__ == "__main__":
    test_zip_ecosystem()
