import os
import sys
import re
import inspect

# Reuse category map from audit script
CATEGORY_MAP = {
    "AI": "AI.md",
    "System/Debug": "System.md",
    "System/Files": "System.md",
    "System/Process": "System.md",
    "File System": "System.md",
    "System/Hardware": "Hardware.md",
    "System/Automation": "Desktop.md",
    "System/Security": "Security.md",
    "Media/Vision": "Media.md",
    "Media/Audio": "Media.md",
    "Media/Graphics": "Media.md",
    "Network/Requests": "Web.md",
    "Network/Ingress": "Web.md",
    "Network/SSH": "Network.md",
    "Network/Email": "Network.md",
    "Network/Providers": "Network.md",
    "Math/Arithmetic": "Data_Math.md",
    "Math/Advanced": "Data_Math.md",
    "Math/Rounding": "Data_Math.md",
    "Math/Trig": "Data_Math.md",
    "Data": "Data_Math.md",
    "Utility/Data/Text": "Data_Math.md",
    "Utility/Data/List": "Data_Math.md",
    "Utility/Data/Dict": "Data_Math.md",
    "Utility/Data/JSON": "Formats.md",
    "Utility/Data/CSV": "Formats.md",
    "Utility/Office": "Formats.md",
    "Utility/Date": "Data_Math.md",
    "Utility/Dialogs": "UI.md",
    "Utility/Toasts": "UI.md",
    "UI": "UI.md",
    "Security/Providers": "Security.md",
    "Security/Actions": "Security.md",
    "Security": "Security.md",
    "Search/Analytics": "Analytics.md",
    "Vector/DB": "RAG.md",
    "System/Plugin": "Advanced.md",
    "Connectivity/Providers": "Network.md",
    "Database": "Database.md"
}

def get_doc_file(category):
    # Try exact match first
    if category in CATEGORY_MAP:
        return CATEGORY_MAP[category]
    
    # Try substring match for hierarchical categories
    for key, doc in CATEGORY_MAP.items():
        if key in category:
            return doc
    return "Advanced.md"

def get_node_metadata(search_dir):
    """
    Scans python files for registered nodes and extracts docstrings/versions.
    """
    nodes = {}
    # Matches @NodeRegistry.register("Label", "Category")
    register_pattern = re.compile(r'@NodeRegistry\.register\("([^"]+)",\s*"([^"]+)"\)')
    # Matches class Header(BaseNode):\n    """docstring"""\n    version = "1.0.1"
    # Or class Header(BaseNode):\n    version = "1.0.1"\n    """docstring""" (handled by cleandoc logic)
    
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
    # Group nodes by target doc file
    files_to_rebuild = {}
    for nid, info in nodes.items():
        doc_file = get_doc_file(info['category'])
        if target_file and doc_file != target_file:
            continue
        if doc_file not in files_to_rebuild:
            files_to_rebuild[doc_file] = []
        files_to_rebuild[doc_file].append(info)

    for doc_file, node_list in files_to_rebuild.items():
        doc_path = os.path.join(docs_dir, doc_file)
        header = ""
        
        # 1. Try to read existing header (everything before "## Nodes" or first ###)
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find the split point
                split_point = content.find("## Nodes")
                if split_point == -1:
                    # Fallback to first ###
                    split_point = content.find("### ")
                
                if split_point != -1:
                    header = content[:split_point].strip() + "\n\n## Nodes\n\n"
                else:
                    # Generic header
                    title = doc_file.replace(".md", "")
                    header = f"# {title}\n\n## Nodes\n\n"
        else:
            title = doc_file.replace(".md", "")
            header = f"# {title}\n\n## Nodes\n\n"

        # 2. Build Nodes Section
        # Sort nodes by name
        node_list.sort(key=lambda x: x['name'])
        
        node_content = ""
        for info in node_list:
            node_content += f"### {info['name']}\n\n"
            node_content += f"**Version**: {info['version']}\n"
            node_content += f"**Description**: {info['description']}\n\n"

        # 3. Add Footer
        footer = "---\n[Back to Nodes Index](Index.md)\n"

        # 4. Write File
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(node_content)
            f.write(footer)
        
        print(f"Rebuilt: {doc_file} ({len(node_list)} nodes)")

def generate_index(docs_dir, template_path):
    """
    Builds Index.md from a template in doc_base.
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
            # Peek at the first line for the title
            title = file.replace(".md", "")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("# "):
                        title = first_line[2:].strip()
            except:
                pass
            categories.append(f"- [{title}]({file})")

    # Sort categories alphabetical (ignoring emojis)
    def clean_name(s):
        return re.sub(r'[^\w\s]', '', s).strip()
    
    categories.sort(key=lambda x: clean_name(x))
    
    category_list = "\n".join(categories)
    new_index = template.replace("[replace_with_Categories]", category_list)

    index_path = os.path.join(docs_dir, "Index.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_index)
    
    print(f"Generated Index.md with {len(categories)} categories.")

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
