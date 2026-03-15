import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

import axonpulse.nodes # Triggers auto-discovery
from axonpulse.nodes.registry import NodeRegistry

print("--- Comprehensive Node Registry Audit ---")
labels = NodeRegistry.get_all_labels()
print(f"Total Labels: {len(labels)}")

string_nodes = [l for l in labels if "String" in l or "string" in l]
print(f"\nString-related nodes ({len(string_nodes)}):")
for l in sorted(string_nodes):
    print(f"  - '{l}'")

# Check for the specific mangled names from the screenshot
mangled_targets = ["Stringlowercasenode", "Stringfindnode", "Stringreplace", "stringreplace"]
print("\nChecking for specific mangled targets:")
for t in mangled_targets:
    if t in labels:
        print(f"  [FOUND] '{t}'")
    else:
        # Check case-insensitive
        matches = [l for l in labels if t.lower() == l.split('.')[-1].lower()]
        if matches:
            print(f"  [MATCH] '{t}' matches registry entries: {matches}")
        else:
            print(f"  [NOT FOUND] '{t}'")

# Check if there are duplicate classes registered under different labels
class_map = {}
for label in labels:
    cls = NodeRegistry.get_node_class(label)
    cls_name = f"{cls.__module__}.{cls.__name__}"
    if cls_name not in class_map:
        class_map[cls_name] = []
    class_map[cls_name].append(label)

print("\nDuplicate Class Registrations:")
for cls_id, labels_list in class_map.items():
    if len(labels_list) > 1:
        print(f"  - {cls_id}: {labels_list}")

# Inspect the decorator fallback logic results
# Find a node that was likely auto-labeled
auto_labeled = [l for l in labels if l.endswith("Node") or l.endswith("node")]
if auto_labeled:
    print(f"\nPotential Auto-Labeled Nodes ({len(auto_labeled)}):")
    for l in sorted(auto_labeled)[:10]:
        print(f"  - '{l}'")
