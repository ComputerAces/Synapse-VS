import os
import ast
import re

def sanitize_name(name):
    """Replaces spaces and invalid characters with underscores."""
    if not name: return "param"
    return name.replace(" ", "_").replace("-", "_").replace(".", "_")

class SmartRefactor(ast.NodeTransformer):
    def __init__(self, out_ports):
        self.out_ports = out_ports
        self.return_dict_items = []

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            call = node.value
            if getattr(call.func, 'attr', '') == 'set' and getattr(call.func.value, 'attr', '') == 'bridge':
                key_arg = call.args[0]
                val_arg = call.args[1]
                port_name = None
                if isinstance(key_arg, ast.JoinedStr):
                    for part in key_arg.values:
                        if isinstance(part, ast.Constant) and part.value.startswith("_"):
                            port_name = part.value[1:]
                elif isinstance(key_arg, ast.Constant) and isinstance(key_arg.value, str) and "_" in key_arg.value:
                    port_name = key_arg.value.split("_")[-1]
                
                if port_name in self.out_ports:
                    self.return_dict_items.append((port_name, val_arg))
                    return None
        return self.generic_visit(node)

    def _ensure_block(self, body):
        new_body = []
        for s in body:
            res = self.visit(s)
            if res:
                new_body.append(res)
        if not new_body:
            return [ast.Pass()]
        return new_body

    def visit_If(self, node):
        node.body = self._ensure_block(node.body)
        node.orelse = self._ensure_block(node.orelse)
        return node

    def visit_For(self, node):
        node.body = self._ensure_block(node.body)
        return node

    def visit_While(self, node):
        node.body = self._ensure_block(node.body)
        return node

    def visit_Try(self, node):
        node.body = self._ensure_block(node.body)
        for handler in node.handlers:
            handler.body = self._ensure_block(handler.body)
        node.finalbody = self._ensure_block(node.finalbody)
        return node

def migrate_file(filepath, output_ver="2.3.0"):
    if any(x in filepath for x in ["registry.py", "decorators.py", "__init__.py", "base.py", "super_node.py"]):
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content.strip(): return None
        try:
            tree = ast.parse(content)
        except Exception as e:
            print(f"  [ERROR] {filepath}: Parse Error: {e}")
            return None

    classes_to_migrate = []
    other_nodes = []
    original_imports = []
    
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            original_imports.append(node)
            continue

        if not isinstance(node, ast.ClassDef):
            other_nodes.append(node)
            continue
            
        registration = None
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and getattr(decorator.func, 'attr', '') == 'register':
                registration = decorator
                break
        
        if not registration:
            other_nodes.append(node)
            continue

        # Check inheritance - Smart Check
        is_simple_inheritance = len(node.bases) == 1 and isinstance(node.bases[0], ast.Name) and node.bases[0].id == "SuperNode"
        if not is_simple_inheritance:
            other_nodes.append(node)
            continue

        # Check methods
        methods = [item for item in node.body if isinstance(item, ast.FunctionDef)]
        essential_methods = {'__init__', 'define_schema', 'register_handlers'}
        logic_methods = [m for m in methods if m.name not in essential_methods]
        
        if len(logic_methods) != 1:
            other_nodes.append(node)
            continue

        handler_node = logic_methods[0]
        classes_to_migrate.append((node, registration, handler_node))

    if not classes_to_migrate:
        return None

    migrated_content = []
    
    # 1. Preserve Original Imports
    for imp in original_imports:
        migrated_content.append(ast.unparse(imp))

    # 2. Add Required Imports if missing
    required_imports = [
        "from typing import Any, List, Dict, Optional",
        "from axonpulse.core.types import DataType, TypeCaster",
        "from axonpulse.nodes.decorators import axon_node"
    ]
    for ri in required_imports:
        imp_str = ri
        has_it = False
        for imp in original_imports:
            if imp_str in ast.unparse(imp):
                has_it = True
                break
        if not has_it:
            migrated_content.append(imp_str)

    # 3. Other non-migrated content
    for node in other_nodes:
        migrated_content.append(ast.unparse(node))

    # 4. Migrated Nodes
    for cls_node, reg, handler in classes_to_migrate:
        label = reg.args[0].value if isinstance(reg.args[0], ast.Constant) else "Unknown"
        category = reg.args[1].value if isinstance(reg.args[1], ast.Constant) else "General"
        
        # PRESERVE ORIGINAL CLASS NAME FOR THE FUNCTION
        func_name = cls_node.name
        
        docstring = ast.get_docstring(cls_node) or ""
        
        input_schema = {}
        output_schema = {}
        properties = {}
        
        for item in cls_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Subscript):
                        target = stmt.targets[0]
                        if getattr(target.value, 'attr', '') == 'properties':
                            prop_name = target.slice.value if isinstance(target.slice, ast.Constant) else None
                            if prop_name: properties[prop_name] = stmt.value
            
            if isinstance(item, ast.FunctionDef) and item.name == 'define_schema':
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Attribute):
                        attr = stmt.targets[0].attr
                        if attr == 'input_schema' and isinstance(stmt.value, ast.Dict):
                            for k, v in zip(stmt.value.keys, stmt.value.values):
                                if k: input_schema[k.value] = v
                        if attr == 'output_schema' and isinstance(stmt.value, ast.Dict):
                            for k, v in zip(stmt.value.keys, stmt.value.values):
                                if k: output_schema[k.value] = v

        non_default_args = []
        default_args = []
        for port_name, dtype in input_schema.items():
            if port_name == "Flow": continue
            sanitized = sanitize_name(port_name)
            default_val = properties.get(port_name)
            hint = "Any"
            if isinstance(dtype, ast.Attribute) and dtype.value.id == "DataType":
                d_attr = dtype.attr
                if d_attr in ["NUMBER", "INTEGER"]: hint = "float"
                elif d_attr == "STRING": hint = "str"
                elif d_attr == "BOOLEAN": hint = "bool"
                elif d_attr == "LIST": hint = "list"
                elif d_attr == "DICT": hint = "dict"
            if default_val:
                default_args.append(f"{sanitized}: {hint} = {ast.unparse(default_val).strip()}")
            else:
                non_default_args.append(f"{sanitized}: {hint}")
            
        out_ports = [k for k in output_schema.keys() if k != "Flow"]
        
        refactor = SmartRefactor(out_ports)
        handler = refactor.visit(handler)
        
        logic_code = ast.unparse(handler.body).strip()
        logic_code = logic_code.replace("self.bridge", "_bridge")
        logic_code = logic_code.replace("self.node_id", "_node_id")
        logic_code = logic_code.replace("self.name", "_node.name")
        logic_code = logic_code.replace("self.properties", "_node.properties")
        logic_code = logic_code.replace("self.logger", "_node.logger")
        logic_code = logic_code.replace("self.set_output", "_node.set_output")
        
        for port_name in input_schema.keys():
            if port_name == "Flow": continue
            sanitized = sanitize_name(port_name)
            if sanitized != port_name:
                logic_code = logic_code.replace(f"self.{port_name}", sanitized)
        
        orig_has_kwargs = any(p.arg == 'kwargs' for p in handler.args.kwonlyargs + [handler.args.kwarg] if p)
        f_str = f"@axon_node(category=\"{category}\", version=\"{output_ver}\", node_label=\"{label}\""
        if out_ports and out_ports != ["Result"]:
            f_str += f", outputs={out_ports}"
        f_str += ")\n"
        
        sig_args = non_default_args + default_args + ["_bridge: Any = None", "_node: Any = None", "_node_id: str = None"]
        if orig_has_kwargs: sig_args.append("**kwargs")
            
        f_str += f"def {func_name}({', '.join(sig_args)}) -> Any:\n"
        f_str += f"    \"\"\"{docstring}\"\"\"\n"
        
        for line in logic_code.split('\n'):
            if line.strip() == "return True" and (refactor.return_dict_items): continue
            f_str += f"    {line}\n"
            
        if refactor.return_dict_items:
            unique_ports = {item[0] for item in refactor.return_dict_items}
            if len(unique_ports) == 1 and len(out_ports) == 1:
                f_str += f"    return {ast.unparse(refactor.return_dict_items[-1][1]).strip()}\n"
            else:
                f_str += "    return {"
                f_str += ", ".join([f"'{k}': {ast.unparse(v).strip()}" for k, v in refactor.return_dict_items])
                f_str += "}\n"
        elif not any("return " in l for l in logic_code.split('\n')):
             f_str += "    return True\n"
             
        migrated_content.append(f_str)

    return "\n\n".join(migrated_content)

def process_directory(dir_path):
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                path = os.path.join(root, file)
                try:
                    new_code = migrate_file(path)
                    if new_code:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_code)
                        print(f"  [HARDENED DONE] {file}")
                except Exception as e:
                    print(f"  [ERROR] {file}: {e}")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "axonpulse/nodes"
    if os.path.isfile(target):
        new_code = migrate_file(target)
        if new_code:
            with open(target, 'w', encoding='utf-8') as f:
                f.write(new_code)
            print("  [HARDENED DONE]")
    elif os.path.isdir(target):
        process_directory(target)
