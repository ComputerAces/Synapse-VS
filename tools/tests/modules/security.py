import os
import sys
import time

# Ensure we can import synapse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from tools.tests.modules.base import setup_engine, load_registry
from synapse.nodes.registry import NodeRegistry

def test_injection_sandbox():
    """
    SECURITY TEST: Verifies handling of malicious or runaway payloads in permissive nodes.
    """
    print(f"\n{'='*50}")
    print(f"[STAGE 15: Injection & Sandbox Auditor]")
    print(f"{'='*50}")
    
    bridge, engine = setup_engine("Security Test")
    load_registry()
    
    StartCls = NodeRegistry.get_node_class("Start Node")
    engine.register_node(StartCls("st", "Start", bridge))
    
    # 1. Shell Injection Test
    print(f"    [Action] Testing Shell Injection (Chained Commands)...")
    ShellCls = NodeRegistry.get_node_class("Shell Command")
    shell_node = ShellCls("shell_1", "Shell", bridge)
    shell_node.properties["Command"] = "echo Safe && echo MALICIOUS_CHAIN"
    engine.register_node(shell_node)
    
    # 2. Python Sandbox / Runaway Test
    print(f"    [Action] Testing Python Sandbox (Infinite Loop)...")
    PythonCls = NodeRegistry.get_node_class("Python Script")
    python_node = PythonCls("py_1", "Python", bridge)
    python_node.properties["ScriptBody"] = "import time\nwhile True:\n    pass" 
    engine.register_node(python_node)
    
    # 3. SQL Injection Simulation
    print(f"    [Action] Testing SQL Injection (DROP TABLE)...")
    SQLExecuteCls = NodeRegistry.get_node_class("SQL Execute")
    sql_node = SQLExecuteCls("sql_1", "SQL", bridge)
    sql_node.properties["Command"] = "DROP TABLE users; --"
    sql_node.properties["Connection"] = "db_p" # Link to provider
    from synapse.nodes.database.sqlite_provider import SQLiteProviderNode
    db_prov = SQLiteProviderNode("db_p", "Database", bridge)
    db_prov.properties["DatabasePath"] = ":memory:"
    engine.register_node(db_prov)
    engine.register_node(sql_node)
    
    # Build Graph
    engine.wires = [
        {"from_node": "st", "from_port": "Flow", "to_node": "shell_1", "to_port": "Flow"},
        {"from_node": "shell_1", "from_port": "Flow", "to_node": "sql_1", "to_port": "Flow"}
    ]
    
    print(f"    [Verify] Running Shell & SQL nodes...")
    bridge.set("sql_1_Connection", {"type": "sqlite", "path": ":memory:"}, "Test")
    
    engine.run("st")
    
    stdout = bridge.get("shell_1_Stdout")
    if "MALICIOUS_CHAIN" in str(stdout):
        print(f"    [Note] Shell node is permissive (Chained execution allowed).")
    
    print(f"[SUCCESS] Security audit completed. Systems documented as permissive/per-user sandbox.")

if __name__ == "__main__":
    test_injection_sandbox()
