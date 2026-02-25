import sys
import os
import multiprocessing
import json

from PyQt6.QtWidgets import QApplication

# Import the new MainWindow from the package
from synapse.gui.main_window_pkg import MainWindow

# Import Headless dependencies only if needed
from synapse.utils.logger import main_logger as logger

def run_headless(file_path):
    """Runs a graph in headless mode (CLI)."""
    if not os.path.exists(file_path):
        print(f"Error: Graph file not found: {file_path}")
        return

    print(f"Synapse VS - Headless Mode")
    print(f"Loading: {file_path}")
    
    # 1. Setup Infrastructure
    from multiprocessing import Manager
    manager = Manager()
    from synapse.core.bridge import SynapseBridge
    bridge = SynapseBridge(manager)
    
    from synapse.core.engine import ExecutionEngine
    engine = ExecutionEngine(bridge, headless=True)
    
    # 2. Load Graph
    from synapse.core.loader import load_graph_from_json
    try:
        node_map, _ = load_graph_from_json(file_path, bridge, engine)
    except Exception as e:
        print(f"Failed to load graph: {e}")
        return

    # 3. Find Start Node
    start_node_id = None
    for node_id, node in node_map.items():
        if node.__class__.__name__ == "StartNode":
            start_node_id = node_id
            break
            
    if not start_node_id:
        print("Error: No 'Start Node' found in graph.")
        return

    # 4. Run Request
    print("Graph loaded. Executing...")
    try:
        engine.run(start_node_id)
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
    except Exception as e:
        print(f"Runtime Error: {e}")
    finally:
        print("Shutting down...")

def main():
    multiprocessing.freeze_support() # Ensure this is first
    
    # [HEADLESS CHECK]
    if "--headless" in sys.argv:
        try:
            idx = sys.argv.index("--headless")
            if idx + 1 < len(sys.argv):
                file_path = sys.argv[idx + 1]
                run_headless(file_path)
            else:
                print("Usage: synapse/gui/main_window.py --headless <path_to_graph.syp>")
        except Exception as e:
            print(f"Headless Error: {e}")
        return

    app = QApplication(sys.argv)
    
    # ─── Global Signal & Exception Handlers ──────────────────────────
    from synapse.utils.cleanup import init_global_handlers
    init_global_handlers()
    
    window = MainWindow()
    window.show()
    
    # Allow Python to process signals during Qt event loop
    from PyQt6.QtCore import QTimer
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)  # Let Python run signal handlers
    signal_timer.start(200)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

