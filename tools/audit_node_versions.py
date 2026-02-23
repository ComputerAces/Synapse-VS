import os
import sys
import re

def get_registered_nodes(search_dir):
    """
    Scans python files for @NodeRegistry.register calls.
    Returns a dict: { node_id: { name, category, file, path, version, doc_type } }
    """
    nodes = {}
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
                        namespaced_id = f"{category}.{name}"
                        
                        # Find the class block following the decorator
                        search_block = content[match.end():match.end() + 10000]
                        
                        # Version Check
                        ver_match = version_pattern.search(search_block)
                        version = ver_match.group(1) if ver_match else "Unknown"
                        
                        # DocString Check (Advanced Heuristics)
                        doc_match = docstring_pattern.search(search_block)
                        doc_type = "MISSING"
                        if doc_match:
                            doc_content = doc_match.group(1).strip()
                            doc_lower = doc_content.lower()
                            
                            has_inputs = "inputs:" in doc_lower
                            has_outputs = "outputs:" in doc_lower
                            has_bullets = "-" in doc_content or "*" in doc_content
                            
                            if has_inputs and has_outputs and has_bullets:
                                doc_type = "DETAILED"
                            elif has_inputs or has_outputs or has_bullets:
                                doc_type = "PARTIAL"
                            else:
                                if "\n" in doc_content:
                                    doc_type = "MULTILINE"
                                else:
                                    doc_type = "SINGLE-LINE"
                        
                        # Provider Check
                        required_providers = []
                        req_prov_match = re.search(r'self\.required_providers\s*=\s*\[(.*?)\]', search_block)
                        if req_prov_match:
                             # rudimentary parsing
                             raw_list = req_prov_match.group(1)
                             required_providers = [x.strip().strip('"\'') for x in raw_list.split(',') if x.strip()]
                        
                        # Inheritance Check
                        class_def_match = re.search(r'class\s+\w+\((.*?)\):', search_block)
                        base_classes = []
                        if class_def_match:
                            base_classes = [b.strip() for b in class_def_match.group(1).split(',')]

                        has_runtime_error = "raise RuntimeError" in content
                        
                        nodes[namespaced_id] = {
                            'name': name,
                            'category': category,
                            'file': file,
                            'path': path,
                            'version': version,
                            'doc_type': doc_type,
                            'required_providers': required_providers,
                            'base_classes': base_classes,
                            'has_runtime_error': has_runtime_error
                        }
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return nodes

PROVIDER_RULES = {
    "Database": {"type": "list", "target": ["Database Provider", "Redis Provider"]},
    "Security": {"type": "list", "target": ["Security Provider", "Database Provider"]}, # BasicAuth needs DB
    "AI": {"type": "error"},
    "Vector": {"type": "error"},
    "Browser": {"type": "error"},
    "Network/Sockets": {"type": "error"}, # SocketIO
    "Network/Ingress": {"type": "error"}, # Flask
    "System/Hardware": {"type": "error"},
    "File System/Operations": {"type": "error"}
}

def audit_providers(nodes):
    report = []
    for nid, info in nodes.items():
        category = info['category']
        cat_key = category.split('/')[0] # Top level category
        
        # Specific sub-cat overrides
        if category in PROVIDER_RULES:
            rule = PROVIDER_RULES[category]
        elif cat_key in PROVIDER_RULES:
            rule = PROVIDER_RULES[cat_key]
        else:
            continue
            
        # Common Skip Logic
        if "Provider" in info['name'] and "Security" not in info['name'] and "Client" not in info['name']:
            continue
        if "Graph" in info['name'] or "Trigger" in info['name']:
            continue

        if rule['type'] == 'list':
            # Check Inheritance first
            if "BaseSQLNode" in info['base_classes'] or "BaseRedisNode" in info['base_classes']:
                report.append(f"[PASS] {info['name']} (Inherited)")
                continue
            if "BaseSecurityActionNode" in info['base_classes'] and "Security" in category:
                 report.append(f"[PASS] {info['name']} (Inherited)")
                 continue

            if not info['required_providers']:
                 # Whitelist Logic-Only Security Nodes
                 if any(x in info['name'] for x in ["Gatekeeper", "Encrypt", "Decrypt", "SHA", "Checksum", "Hash"]):
                     report.append(f"[PASS] {info['name']} (Logic Only)")
                     continue
                 # OS Security Provider (Root Provider)
                 if "OS Security Provider" in info['name']:
                     report.append(f"[PASS] {info['name']} (Root Provider)")
                     continue
                     
                 report.append(f"[FAIL] {info['name']}: Missing 'required_providers'. Expected one of {rule['target']}")
            else:
                 # Check if at least one target is in the list
                 has_match = any(t in info['required_providers'] for t in rule['target'])
                 if not has_match:
                      report.append(f"[FAIL] {info['name']}: Invalid 'required_providers' {info['required_providers']}. Expected {rule['target']}")
                 else:
                      report.append(f"[PASS] {info['name']}")

        elif rule['type'] == 'error':
            if not info['has_runtime_error']:
                # Scrapers exception
                if "Parser" in info['name'] or "Converter" in info['name']:
                    continue
                # TTS Exception
                if "Text to Speech" in info['name']:
                    continue
                # AI Chunking exception (Logic only)
                if "Chunk" in info['name']:
                    continue
                if "Regression" in info['name'] or "Analysis" in info['name'] or "Detector" in info['name'] or "Detection" in info['name']:
                    continue
                # Providers like "OpenAI Embeddings" (Configuration nodes)
                if "Embeddings" in info['name'] and "Search" not in info['name'] and "Add" not in info['name']:
                    continue
                # Flask Exceptions
                if "Flask" in info['name'] and ("Host" in info['name'] or "Response" in info['name']):
                     continue
                # Vector DB Providers
                if any(x in info['name'] for x in ["LanceDB", "Milvus", "Pinecone", "Chroma", "Weaviate"]):
                     continue
                # Monitor
                if "Monitor" in info['name']:
                     continue

                report.append(f"[FAIL] {info['name']}: Missing 'raise RuntimeError' strict check.")
            else:
                report.append(f"[PASS] {info['name']}")
                
    return report

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
    "Search/Analytics": "Analytics.md",
    "Vector/DB": "RAG.md",
    "System/Plugin": "Advanced.md",
    "Connectivity/Providers": "Network.md",
    "IO/Documents": "Formats.md",
    "File System/Operations": "System.md",
    "File System/File Editing": "System.md"
}

def get_doc_file(category):
    for key, doc in CATEGORY_MAP.items():
        if key in category:
            return doc
    return "Advanced.md"

def audit_docs(nodes, docs_dir, init_v="1.0.0", sync=False, generate=False):
    """
    Scans .md files for node headings.
    - Ensures Version is right under the heading.
    - Syncs versions if requested.
    - Generates stubs for missing nodes if requested.
    """
    all_doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
    status_report = []
    found_nodes = set()

    # Step 1: Process existing documentation
    for doc_file in all_doc_files:
        doc_path = os.path.join(docs_dir, doc_file)
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("### "):
                    # Robust header parsing
                    header_text = line[4:].strip()
                    
                    # Potential names: Full header, then splits
                    potential_names = [header_text]
                    if header_text.endswith(" Node"):
                        potential_names.append(header_text[:-5].strip())
                    
                    # Add splits by / and (
                    raw_splits = re.split(r'[/()]', header_text)
                    for rs in raw_splits:
                        rs = rs.strip()
                        if rs and rs not in potential_names:
                            potential_names.append(rs)
                            if rs.endswith(" Node"):
                                potential_names.append(rs[:-5].strip())
                    
                    found_any_for_header = []
                    for p_name in potential_names:
                        # Find all namespaced IDs that match this name
                        for nid, info in nodes.items():
                            if info['name'] == p_name:
                                found_nodes.add(nid)
                                if nid not in found_any_for_header:
                                    found_any_for_header.append(nid)
                    
                    if found_any_for_header:
                        # Use the most representative nid for the header sync
                        primary_nid = found_any_for_header[0]
                        info = nodes[primary_nid]
                        code_ver = info['version']
                        
                        version_idx = -1
                        for j in range(i + 1, min(i + 8, len(lines))):
                            if "**Version**:" in lines[j]:
                                version_idx = j
                                break
                            if lines[j].startswith("### "): break
                        
                        if version_idx != -1:
                            doc_ver_match = re.search(r'\*\*Version\*\*:\s*([^\s\n\r]+)', lines[version_idx])
                            doc_ver = doc_ver_match.group(1) if doc_ver_match else "???"
                            
                            is_immediate = (version_idx == i + 1) or (version_idx == i + 2 and lines[i+1].strip() == "")
                            
                            if not is_immediate:
                                ver_line = lines.pop(version_idx)
                                lines.insert(i + 1, ver_line)
                                modified = True
                                status_report.append(f"[REFORMAT] {info['name']} gear in {doc_file}")
                                version_idx = i + 1
                            
                            if sync and doc_ver != code_ver:
                                lines[version_idx] = f"**Version**: {code_ver}\n"
                                modified = True
                                status_report.append(f"[SYNCED] {info['name']} gear: {doc_ver} -> {code_ver} in {doc_file}")
                            elif doc_ver != code_ver:
                                status_report.append(f"[MISMATCH] {info['name']} gear: Code={code_ver}, Doc={doc_ver} in {doc_file}")
                            else:
                                status_report.append(f"[OK] {info['name']} gear in {doc_file}")
                        else:
                            # Missing version string
                            target_ver = code_ver if sync else init_v
                            insert_at = i + 1
                            lines.insert(insert_at, f"**Version**: {target_ver}\n")
                            modified = True
                            status_report.append(f"[INIT] {info['name']} gear in {doc_file}")
                            i += 1
                i += 1
            
            if modified:
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        except Exception as e:
            print(f"Error processing {doc_file}: {e}")

    # Step 2: Generate missing stubs if requested
    if generate:
        for nid, info in nodes.items():
            if nid not in found_nodes:
                name = info['name']
                doc_file = get_doc_file(info['category'])
                doc_path = os.path.join(docs_dir, doc_file)
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    has_header = re.search(rf'^###\s*{re.escape(name)}\s*$', content, re.MULTILINE)
                    
                    if not has_header:
                        with open(doc_path, 'a', encoding='utf-8') as f:
                            if not content.endswith('\n\n'):
                                f.write('\n\n')
                            f.write(f"### {name}\n")
                            f.write(f"**Version**: {info['version']}\n")
                            f.write(f"**Description**: Documentation pending (Category: {info['category']})\n")
                        status_report.append(f"[GENERATED] {name} stub in {doc_file}")
                        found_nodes.add(nid)
                    else:
                        status_report.append(f"[EXISTS] {name} already in {doc_file}")
                        found_nodes.add(nid)
                except Exception as e:
                    status_report.append(f"[FAILED GEN] {name}: {e}")
    else:
        for nid, info in nodes.items():
            if nid not in found_nodes:
                status_report.append(f"[MISSING DOC] {info['name']} ({nid})")

    return status_report

if __name__ == "__main__":
    node_lib = "synapse/nodes"
    docs_nodes = "docs/nodes"
    
    do_sync = "--sync" in sys.argv
    do_gen = "--generate-stubs" in sys.argv
    
    print("Gathering registered nodes from code...")
    nodes = get_registered_nodes(node_lib)
    print(f"Found {len(nodes)} unique namespaced registrations.\n")
    
    print(f"Auditing documentation (Sync={'ON' if do_sync else 'OFF'}, Stubs={'ON' if do_gen else 'OFF'})...")
    report = audit_docs(nodes, docs_nodes, sync=do_sync, generate=do_gen)
    
    print("\n" + "="*50)
    print("DOCUMENTATION AUDIT REPORT")
    print("="*50)
    
    tags = ['OK', 'SYNCED', 'REFORMAT', 'INIT', 'GENERATED', 'MISMATCH', 'MISSING DOC', 'EXISTS']
    status_categories = {tag: [] for tag in tags}
    for entry in report:
        tag_match = re.search(r'\[([^\]]+)\]', entry)
        if tag_match:
            tag = tag_match.group(1)
            if tag in status_categories:
                status_categories[tag].append(entry)
    
    for tag in tags:
        items = status_categories[tag]
        if items:
            print(f"\n[{tag}] - {len(items)} nodes")
            for item in items[:10]:
                print(f"  {item}")
            if len(items) > 10:
                print(f"  ... and {len(items)-10} more")

    print(f"\n" + "="*50)
    print("PROVIDER COMPLIANCE AUDIT")
    print("="*50)
    prov_report = audit_providers(nodes)
    
    fails = [x for x in prov_report if "[FAIL]" in x]
    passes = [x for x in prov_report if "[PASS]" in x]
    
    print(f"Passed: {len(passes)}")
    print(f"Failed: {len(fails)}")
    
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print(f"  {f}")
    else:
        print("\nAll checks passed!")

    print(f"\n" + "="*50)
    print("SOURCE CODE QUALITY (DocStrings)")
    print("="*50)
    
    doc_categories = {
        "DETAILED": [], 
        "PARTIAL": [], 
        "MULTILINE": [], 
        "SINGLE-LINE": [], 
        "MISSING": []
    }
    for nid, info in nodes.items():
        doc_categories[info['doc_type']].append(info['name'])
    
    for dtype, items in doc_categories.items():
        if items and dtype != "DETAILED":
            print(f"\n[{dtype}] - {len(items)} nodes")
            for name in items:
                # Find the info for this name
                for info in nodes.values():
                    if info['name'] == name:
                        print(f"  - {name} ({info['path']})")
                        break
        elif items:
            print(f"\n[{dtype}] - {len(items)} nodes (skipped paths)")
    
    print("\n" + "="*50)
    print(f"\n" + "="*50)
    print("REGISTERED NODE LIST (Name: Version)")
    print("="*50)
    
    # Sort nodes by namespaced ID
    for nid in sorted(nodes.keys()):
        info = nodes[nid]
        print(f"  {nid}: v{info['version']}")
    
    # [NEW] Min Version Check
    min_version = None
    for arg in sys.argv[1:]:
        # Simple heuristic: acts like a version number X.Y.Z
        if re.match(r'^\d+\.\d+\.\d+$', arg):
            min_version = arg
            break
            
    if min_version:
        print(f"\n" + "="*50)
        print(f"VERSION COMPLIANCE AUDIT (Min: {min_version})")
        print("="*50)
        
        def parse_ver(v_str):
            try:
                return tuple(map(int, v_str.split('.')))
            except:
                return (0, 0, 0)

        target_v = parse_ver(min_version)
        outdated = []
        
        for nid, info in nodes.items():
            node_v = parse_ver(info['version'])
            if node_v < target_v:
                outdated.append(f"{info['name']} (v{info['version']})")
                
        if outdated:
            print(f"Found {len(outdated)} nodes below v{min_version}:")
            for item in outdated:
                print(f"  [OUTDATED] {item}")
        else:
            print(f"All nodes meet minimum version v{min_version}!")

    print("\n" + "="*50)
    print(f"Total Unique Nodes Processed: {len(nodes)}")
    print(f"Usage: python tools/audit_node_versions.py [min_version] [--sync] [--generate-stubs]")
