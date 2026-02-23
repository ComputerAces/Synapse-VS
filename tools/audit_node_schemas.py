import os
import sys
import multiprocessing

import inspect
import re

# Setup paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from synapse.nodes.registry import NodeRegistry
from synapse.core.bridge import SynapseBridge
from synapse.utils.cleanup import CleanupManager

# Prevent cleanup manager from closing our process
CleanupManager.cleanup_all = lambda: None

# Regex for TitleCase / CamelCase naming enforcement
# - Must start with Uppercase
# - No underscores allowed
# - Spaces allowed if following title case (allow numbers and common UI symbols like () % in following words)
NAMING_PATTERN = re.compile(r'^[A-Z][a-zA-Z0-9]*(\s+[A-Z0-9][a-zA-Z0-9\(\)%]*)*$')

def audit_node_schemas():
    manager = multiprocessing.Manager()
    bridge = SynapseBridge(manager)
    
    # Dynamically load all node classes
    nodes_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synapse', 'nodes'))
    for root, _, files in os.walk(nodes_dir):
        for f in files:
             if f.endswith('.py') and not f.startswith('__'):
                 rel_path = os.path.relpath(os.path.join(root, f), os.path.join(nodes_dir, "..", ".."))
                 mod_name = rel_path.replace(os.sep, '.')[:-3]
                 try:
                     __import__(mod_name)
                 except Exception as e:
                     # Silently ignore import errors for now (could be test stubs, etc)
                     pass

    print(f"Scanning {len(NodeRegistry._nodes)} registry entries for schema collisions...\n")
    
    fails = 0
    processed_classes = set()
    
    # Exceptions that are allowed to overlap between Inputs and Outputs
    ALLOWED_IO_OVERLAPS = ["Flow", "Error Flow", "Done", "Break", "Exit"]
    
    for namespaced_id, node_cls in sorted(NodeRegistry._nodes.items()):
        # De-duplicate by class to avoid auditing both 'Label' and 'Category.Label' legacy entries
        if node_cls in processed_classes:
            continue
        processed_classes.add(node_cls)
        
        try:
            node = node_cls("test_node", namespaced_id.split('.')[-1], bridge)
        except Exception as e:
             # Some nodes might fail instantiation without specific arguments or environment
             continue
             
        inputs = list(node.input_schema.keys())
        outputs = list(node.output_schema.keys())
        props = list(node.properties.keys())
        
        violations = []
        
        # 1. Initialization Check (DNA Assert)
        if not inputs and not outputs:
            violations.append("DNA Violation: Both Input and Output schemas are empty. Is define_schema() called?")

        # 2. Naming Convention Enforcer & Uniqueness Lower Map
        all_elements = []
        for p in props: all_elements.append((p, "Property"))
        for i in inputs: all_elements.append((i, "Input"))
        for o in outputs: all_elements.append((o, "Output"))
        
        lower_map = {}
        for k, src in all_elements:
            # check naming convention
            if k not in ALLOWED_IO_OVERLAPS:
                if not NAMING_PATTERN.match(k):
                    violations.append(f"Naming violation: '{k}' ({src}) is not TitleCase/CamelCase.")
            
            # check uniqueness
            lk = k.lower()
            if lk in lower_map:
                existing_k, existing_src = lower_map[lk]
                
                # Rule 1: Case-insensitivity mismatch is ALWAYS a violation
                if k != existing_k:
                    violations.append(f"Uniqueness collision: '{k}' ({src}) vs '{existing_k}' ({existing_src})")
                
                # Rule 2: Exact overlap between Input and Output is a violation
                elif (src == "Input" and existing_src == "Output") or (src == "Output" and existing_src == "Input"):
                    if k not in ALLOWED_IO_OVERLAPS:
                        violations.append(f"Input/Output collision: '{k}' exists in both input and output schemas.")
                
                # Rule 3: Exact overlap between Property and Output is a violation
                elif (src == "Property" and existing_src == "Output") or (src == "Output" and existing_src == "Property"):
                    violations.append(f"Property/Output collision: '{k}' exists in both properties and output schema.")
                
                # Note: Input and Property sharing an exact name is ALLOWED (they are functionally linked).
            else:
                lower_map[lk] = (k, src)
                
        # 3. Check for Exact Match overlaps between Inputs and Outputs (already covered above, but for clarity)
        # (Covered by 'Exact collision' logic in uniqueness check)

        # 4. Pickling Validator (Module level inspection)
        try:
            mod = inspect.getmodule(node_cls)
            if mod:
                classes = inspect.getmembers(mod, inspect.isclass)
                for name, obj in classes:
                    if obj.__module__ == mod.__name__:
                        # Check if this class is allowed
                        # Allowed: The node class itself, or another registered Node class in the same file.
                        if obj != node_cls:
                            # Use string comparison to avoid issues with imported base classes if necessary,
                            # but direct class check is safer.
                            try:
                                from synapse.nodes.base_node import BaseNode
                                if not issubclass(obj, BaseNode):
                                    if not name.startswith("_"):
                                        violations.append(f"Pickling Risk: Local class '{name}' defined in module. Use core types or external utilities.")
                            except Exception:
                                pass
        except Exception:
            pass
                
        # Final reporting
        violations = list(set(violations))
        
        if violations:
            print(f"[FAIL] {namespaced_id}")
            for v in sorted(violations):
                print(f"       -> {v}")
            fails += 1
            
    print(f"\nAudit complete. Found {fails} violations across {len(processed_classes)} unique nodes.")

if __name__ == "__main__":
    audit_node_schemas()
