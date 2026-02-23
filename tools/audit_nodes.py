import sys
import os
import argparse
import multiprocessing

# Ensures we can import tools.auditor seamlessly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.auditor.core import NodeAuditor

if __name__ == "__main__":
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(
        description="Interactive Sandbox Validator & CLI Test Engine for Synapse VS Node Library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive Full Audit Loop:
    python tools/audit_nodes.py -v 2.0.2

  One-Shot Isolated Node Test (Bypasses state saving and interactive prompts):
    python tools/audit_nodes.py -n "While Node" 
    python tools/audit_nodes.py -n "Ollama Provider"

  View Library Dictionary (Paused every 15 entries):
    python tools/audit_nodes.py -l

  Start Clean LEDGER state (Wipes bad_node.log / audit_state.json record):
    python tools/audit_nodes.py -v 2.0.2 -f
"""
    )
    
    # Version Thresholds
    ver_group = parser.add_argument_group("Version Filtering")
    ver_group.add_argument("-v", "--version", type=str, help="Minimum target version string (e.g. 2.0.1). Skips nodes with lower versions.")
    ver_group.add_argument("-vx", "--version_exact", type=str, help="Exact target version string. Skips ALL nodes that do not perfectly match this version.")
    
    # Specific Node Targeting
    run_group = parser.add_argument_group("Execution Modes")
    run_group.add_argument("-n", "--node", type=str, help="Specific node name/ID to filter (substring match). NOTE: Triggers 'One-Shot' testing mode (Instantly boots sandbox for node without interactive y/n/t checking, and avoids logging).")
    run_group.add_argument("-l", "--list", action="store_true", help="Lists all registered node names/categories 15 at a time in the terminal.")
    run_group.add_argument("-vi", "--view", action="store_true", help="Loops through the nodes that have failed or were skipped so you can view the errors assigned to them without touching passed nodes.")
    
    # File Management
    file_group = parser.add_argument_group("Audit File Management")
    file_group.add_argument("-o", "--output", type=str, default="bad_node.log", help="Path to write failing node reports. (Default: bad_node.log)")
    file_group.add_argument("-f", "--from_start", action="store_true", help="Wipes the current run state (audit_state.json) completely clean to perform a fresh audit run.")
    
    args = parser.parse_args()
    
    auditor = NodeAuditor(
        target_version=args.version,
        target_exact=args.version_exact,
        target_node=args.node,
        show_list=args.list,
        view_mode=args.view,
        log_file=args.output,
        from_start=args.from_start
    )
    
    auditor.run()
