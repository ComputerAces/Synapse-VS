import os
import sys
import re
import inspect
from collections import defaultdict

def get_node_metadata(search_dir):
    """
    Scans python files for registered nodes and extracts docstrings/versions.
    """
    nodes = {}
    # Matches @NodeRegistry.register("Label", "Category")
    register_pattern = re.compile(r'@NodeRegistry\.register\("([^"]+)",\s*"([^"]+)"\)')
    version_pattern = re.compile(r'version\s*=\s*["\']([^"\']+)["\']')
    docstring_pattern = re.compile(r'"""([\s\S]*?)"""')

    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for match in register_pattern.finditer(content):
                        name = match.group(1)
                        category = match.group(2)
                        
                        # Find the class block following the decorator
                        search_block = content[match.end():match.end() + 10000]
                        
                        ver_match = version_pattern.search(search_block)
                        version = ver_match.group(1) if ver_match else "1.0.0"
                        
                        doc_match = docstring_pattern.search(search_block)
                        raw_doc = doc_match.group(1) if doc_match else "Documentation pending."
                        
                        # Clean up docstring indentation
                        doc = inspect.cleandoc(raw_doc).strip()
                        
                        namespaced_id = f"{category}.{name}"
                        nodes[namespaced_id] = {
                            'name': name,
                            'category': category,
                            'version': version,
                            'description': doc
                        }
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return nodes

def build_docs(nodes, docs_dir, target_file=None):
    """
    Groups nodes by Category Root and then by Sub-Category.
    Generates hierarchical markdown documents.
    """
    # 0. Clean the directory if building everything
    if not target_file and os.path.exists(docs_dir):
        for file in os.listdir(docs_dir):
            if file.endswith(".md") and file != "Index.md":
                os.remove(os.path.join(docs_dir, file))
        print(f"Cleaned {docs_dir}")

    # 1. Group by [RootCategory][SubCategory] = [NodeList]
    hierarchy = defaultdict(lambda: defaultdict(list))
    
    for nid, info in nodes.items():
        parts = info['category'].split('/')
        root = parts[0]
        # Everything after root is the sub-category
        sub = "/".join(parts[1:]) if len(parts) > 1 else "General"
        
        doc_file = f"{root}.md"
        if target_file and doc_file != target_file:
            continue
            
        hierarchy[root][sub].append(info)

    # 2. Iterate and generate files
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    for root, sub_map in hierarchy.items():
        doc_file = f"{root}.md"
        doc_path = os.path.join(docs_dir, doc_file)
        
        output = f"# 🧩 {root} Nodes\n\n"
        output += f"This document covers nodes within the **{root}** core category.\n\n"
        
        # Sort sub-categories alphabetically
        for sub in sorted(sub_map.keys()):
            output += f"## 📂 {sub}\n\n"
            
            # Sort nodes within sub-category
            node_list = sorted(sub_map[sub], key=lambda x: x['name'])
            for info in node_list:
                output += f"### {info['name']}\n\n"
                output += f"**Version**: `{info['version']}`\n\n"
                output += f"{info['description']}\n\n"
                output += "---\n\n"

        output += "[Back to Node Index](Index.md)\n"

        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"Rebuilt: {doc_file} ({sum(len(v) for v in sub_map.values())} nodes)")

def generate_index(docs_dir, template_path):
    """
    Builds Index.md from a template, mapping all generated category files.
    """
    if not os.path.exists(template_path):
        print(f"Skipping index generation: Template not found at {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Find all .md files in the docs dir (excluding Index.md)
    categories = []
    for file in os.listdir(docs_dir):
        if file.endswith(".md") and file != "Index.md":
            path = os.path.join(docs_dir, file)
            # Use the basename for the title
            title = file.replace(".md", "")
            categories.append(f"- [{title}]({file})")

    # Sort categories alphabetical
    categories.sort()
    
    category_list = "\n".join(categories)
    new_index = template.replace("[replace_with_Categories]", category_list)

    index_path = os.path.join(docs_dir, "Index.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_index)
    
    print(f"Generated Index.md with {len(categories)} root categories.")

if __name__ == "__main__":
    node_lib = "synapse/nodes"
    docs_nodes = "docs/nodes"
    template = "doc_base/index.md"
    
    target = None
    if "--target" in sys.argv:
        idx = sys.argv.index("--target")
        if idx + 1 < len(sys.argv):
            target = sys.argv[idx + 1]

    print("Gathering node metadata from source...")
    nodes = get_node_metadata(node_lib)
    print(f"Extracted {len(nodes)} nodes.\n")
    
    build_docs(nodes, docs_nodes, target_file=target)
    
    # Only generate index if we built everything or if explicitly requested
    if not target:
        generate_index(docs_nodes, template)
