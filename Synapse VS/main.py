import multiprocessing
import sys
import json
from synapse.core.bridge import SynapseBridge
from synapse.core.engine import ExecutionEngine
import synapse.nodes # Triggers auto-discovery
from synapse.nodes.registry import NodeRegistry
from synapse.core.loader import load_graph_from_json, load_favorites_into_registry
from synapse.utils.logger import main_logger as logger

def main():
    logger.info("Initializing Synapse VS (SVS) - Production Mode...")
    
    # 0. Global Signal & Exception Handlers
    from synapse.utils.cleanup import init_global_handlers
    init_global_handlers()

    # 1. Setup Bridge
    manager = multiprocessing.Manager()
    bridge = SynapseBridge(manager)

    # 2. Parse Args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="JSON graph file")
    parser.add_argument("--speed", type=float, default=0.0, help="Execution delay in seconds")
    parser.add_argument("--pause-file", type=str, default=None, help="Path to pause flag file")
    parser.add_argument("--speed-file", type=str, default=None, help="Path to speed control file")
    parser.add_argument("--stop-file", type=str, default=None, help="Path to stop signal file")
    parser.add_argument("--no-trace", action="store_true", help="Disable execution trace logging")
    parser.add_argument("--headless", action="store_true", help="Automatic repair/migration without prompting")
    args = parser.parse_args()

    # 3. Setup Engine
    engine = ExecutionEngine(
        bridge, 
        delay=args.speed, 
        pause_file=getattr(args, 'pause_file', None),
        speed_file=getattr(args, 'speed_file', None),
        stop_file=getattr(args, 'stop_file', None),
        trace=not args.no_trace,
        source_file=getattr(args, 'file', None)
    )

    # 4. Load Graph
    load_favorites_into_registry()
    
    if args.file:
        json_path = args.file
        logger.info(f"Loading graph from {json_path} (Delay: {args.speed}s)")
        node_map, was_modified, data = load_graph_from_json(json_path, bridge, engine)
        
        if was_modified:
            logger.info("Graph was modified during loading (migrations or dead property cleanup).")
            
            # [REPAIR LOGIC] Determine if we should prompt or auto-save
            is_interactive = sys.stdin.isatty() and not getattr(args, 'headless', False)
            
            should_save = False
            if is_interactive:
                from synapse.core.cli_forms import render_form_cli
                schema = [{"label": "Save Changes", "type": "boolean", "default": "y"}]
                result = render_form_cli("Repair & Migration", schema)
                should_save = result.get("Save Changes")
            else:
                logger.info("Non-interactive or Headless mode detected. Automatically applying repairs.")
                should_save = True

            if should_save:
                from synapse.utils.file_utils import safe_save_graph
                if safe_save_graph(json_path, data):
                    logger.info(f"Successfully saved fixed graph to {json_path}")
                else:
                    logger.error(f"Failed to save fixed graph to {json_path}")

        
        # Validation Logic
        start_nodes = []
        return_nodes = []
        
        for nid, node in node_map.items():
            # Check by Class Name to avoid imports
            cname = node.__class__.__name__
            if cname == "StartNode":
                start_nodes.append(node)
            elif cname == "ReturnNode":
                return_nodes.append(node)
                
        # Rule 1: Exactly One Start Node
        if len(start_nodes) != 1:
            logger.error(f"Graph Validation Failed: Found {len(start_nodes)} Start Nodes. Exactly one 'Start Node' is required.")
            return # Exit (or sys.exit(1))

        # Rule 2: At Least One Return Node
        if len(return_nodes) < 1:
            logger.error(f"Graph Validation Failed: Found {len(return_nodes)} Return Nodes. At least one 'Return Node' is required.")
            return # Exit
            
        start_node_id = start_nodes[0].node_id
            
        if start_node_id:
            logger.info(f"Graph loaded. Validation Passed. Starting execution at {start_node_id}...")
            try:
                engine.run(start_node_id)
            except Exception as e:
                import traceback
                logger.critical(f"FATAL GRAPH ERROR: {e}")
                logger.debug(traceback.format_exc())
                sys.exit(1)
        else:
            logger.error("No Start Node found in graph.")
        
    else:
        logger.info("No input file provided. Running Default Test Graph...")
        # ... (Old hardcoded test graph logic if desired, or just exit)
        pass
    
    logger.info("Main Process Finished.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
