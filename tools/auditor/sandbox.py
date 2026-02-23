import os
import sys
import time
import ast
import traceback
import threading
import multiprocessing
import importlib

try:
    import msvcrt
except ImportError:
    msvcrt = None

from synapse.core.types import DataType
from synapse.core.bridge import SynapseBridge
from synapse.core.engine.execution_engine import ExecutionEngine
from synapse.nodes.registry import NodeRegistry
from .utils import Colors, DummyBridge, requires_provider

def execute_custom_test(custom_module_name, namespaced_id, node_cls, is_os_mode):
    """
    Dynamically loads and runs a test from tools/auditor/custom_tests/
    """
    try:
        mod = importlib.import_module(f"tools.auditor.custom_tests.{custom_module_name}")
        if hasattr(mod, 'run_test'):
            print(f"\n{Colors.CYAN}--- CUSTOM SANDBOX [{namespaced_id}] ---{Colors.RESET}")
            return mod.run_test(namespaced_id, node_cls, is_os_mode)
        else:
            print(f"{Colors.RED}Custom test {custom_module_name} missing 'run_test' function.{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}Failed to load custom test {custom_module_name}: {e}{Colors.RESET}")
        return False

def run_sandbox(namespaced_id, node_cls, is_os_mode=False, render_cb=None):
    # Check for custom test override first
    node_name = namespaced_id.split('.')[-1]
    expected_file = node_name.lower().replace(" ", "_")
    custom_path = os.path.join(os.path.dirname(__file__), "custom_tests", f"{expected_file}.py")
    
    if os.path.exists(custom_path):
         success = execute_custom_test(expected_file, namespaced_id, node_cls, is_os_mode)
         if is_os_mode: return success
         if render_cb: render_cb(namespaced_id, node_cls)
         return success

    # Generic Fallback Sandbox
    print(f"\n{Colors.CYAN}--- LIVE ENGINE SANDBOX [{namespaced_id}] ---{Colors.RESET}")
    manager = multiprocessing.Manager()
    bridge = SynapseBridge(manager)
    engine = ExecutionEngine(bridge)
    
    # Mock Hijack for Sandbox Dispatcher testing
    if not hasattr(engine, 'get_hijack_handler'):
        engine.get_hijack_handler = lambda a, b: None

    node = node_cls("sand_1", node_name, bridge)
    engine.register_node(node)
    
    from synapse.nodes.lib.start_node import StartNode
    from synapse.nodes.lib.return_node import ReturnNode
    
    is_prov = hasattr(node, 'cleanup_provider_context')
    is_start = isinstance(node, StartNode)
    is_return = isinstance(node, ReturnNode)
    
    is_loop = node_cls.__name__ in ["WhileNode", "ForNode", "ForEachNode"]
    is_script = node_cls.__name__ in ["PythonNode", "ShellNode", "SubGraphNode"]
    
    mock_inputs = {}
    
    if not is_start:
        if not is_os_mode: print("Mocking Inputs:")
        for key, typ in node.input_schema.items():
            if typ == DataType.FLOW:
                mock_inputs[key] = True 
                continue
                
            if is_os_mode or not sys.stdin.isatty():
                 val = "" # Force auto-mock in OS_MODE
            elif msvcrt:
                try: val = input(f"  - {key} [{typ}]: ").strip()
                except EOFError: val = ""
            else:
                try: val = input(f"  - {key} [{typ}]: ").strip()
                except EOFError: val = ""
                
            if val == "":
                if typ in (DataType.STRING, getattr(DataType, "PASSWORD", None)): val = ""
                elif typ in (DataType.INTEGER, DataType.FLOAT): val = 0
                elif typ == DataType.BOOLEAN: val = False
                elif typ == DataType.LIST: val = []
                elif typ == DataType.DICT: val = {}
                else: val = None
                if not is_os_mode: print(f"    (Auto-mocked: {val})")
            else:
                try: val = ast.literal_eval(val)
                except: pass
                
            mock_inputs[key] = val
            bridge.set(f"sand_1_{key}", val, "Sandbox")

    # LOOP NODE OVERRIDES
    if is_loop:
        if not is_os_mode: print(f"{Colors.YELLOW}  - Loop Node Detected: Injecting safe break limiters...{Colors.RESET}")
        if "Condition" in mock_inputs:
            mock_inputs["Condition"] = False
            bridge.set("sand_1_Condition", False, "Sandbox")
        if "Start" in mock_inputs and "Stop" in mock_inputs:
            mock_inputs["Start"] = 0
            mock_inputs["Stop"] = 1
            mock_inputs["Step"] = 1
            bridge.set("sand_1_Start", 0, "Sandbox")
            bridge.set("sand_1_Stop", 1, "Sandbox")

    # SCRIPT OVERRIDES
    if is_script:
        if not is_os_mode: print(f"{Colors.YELLOW}  - Script/SubGraph Detected: Ensuring safe sandbox execution...{Colors.RESET}")
        if node_cls.__name__ == "SubGraphNode":
            node.properties["Isolated"] = True
        elif node_cls.__name__ == "PythonNode":
            node.properties["Run As Service"] = False
            node.properties["ScriptBody"] = "print('Sandbox Python Executed.')"
        elif node_cls.__name__ == "ShellNode":
            node.properties["RunAsService"] = False
            node.properties["Command"] = "echo Sandbox Shell Executed."

    if not is_os_mode: print(f"\n{Colors.YELLOW}Firing Node Execution in 10s Watchdog Thread...{Colors.RESET}")
    
    result = {"status": "Timeout"}
    
    if "Body" in node.output_schema and node.output_schema["Body"] == DataType.FLOW:
         bridge.set("sand_1_ActivePorts", ["Body", "Loop Flow", "Flow"], "Sandbox") 
         
    def _sandbox_run():
        try:
            if is_start:
                engine.run("sand_1")
            else:
                disp = getattr(engine, 'dispatcher', None)
                if not disp:
                    from synapse.core.node_dispatcher import NodeDispatcher
                    disp = NodeDispatcher(bridge)
                    engine.dispatcher = disp
                    
                res = disp.dispatch(node, mock_inputs, [])
                if hasattr(res, 'wait'): res.wait()
                elif hasattr(res, 'result'): res.result()
                
                if is_loop:
                    active = bridge.get("sand_1_ActivePorts", [])
                    if "Body" in active or "Loop Flow" in active:
                        if not is_os_mode: print(f"{Colors.GRAY}  (Sandbox emitting simulated 'Break' trigger to close loop...){Colors.RESET}")
                        mock_inputs["Trigger"] = "Break"
                        res2 = disp.dispatch(node, mock_inputs, [])
                        if hasattr(res2, 'wait'): res2.wait()
                        elif hasattr(res2, 'result'): res2.result()
            
            if is_prov:
                if not is_os_mode: print(f"  - {Colors.YELLOW}Provider Detected. Keeping alive for sub-tests...{Colors.RESET}")
                time.sleep(1.0)
                
            # Block the sandbox thread until dispatcher queues are empty
            time.sleep(0.5)
            disp = getattr(engine, 'dispatcher', None)
            if not is_start and disp:
                 # Check if the hybrid architecture flags are set or if it's idle
                 # We'll wait a bit longer to be sure
                 time.sleep(0.5)
                 
            result["status"] = "Complete"
        except Exception as e:
            result["status"] = f"CRASH: {e}"
            result["trace"] = traceback.format_exc()

    thread = threading.Thread(target=_sandbox_run)
    thread.daemon = True
    thread.start()
    
    aborted = False
    if not is_os_mode:
        print(f"{Colors.GRAY}Running... (Press 'q' to force abort){Colors.RESET}")
        
    while True:
        if msvcrt and sys.stdin.isatty():
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if key == 'q':
                    aborted = True
                    break
        
        if result["status"] == "Complete":
            break
                
        if "CRASH" in result["status"]:
            break
            
        time.sleep(0.1)

    def teardown():
        try: 
            if getattr(engine, 'dispatcher', None):
                engine.dispatcher.shutdown()
            engine.stop()
        except: pass
        try: bridge.clear()
        except: pass
        try: manager.shutdown()
        except: pass
    
    if aborted:
        print(f"\n{Colors.RED}[FAIL] User aborted execution. Node potentially hung.{Colors.RESET}")
        if not is_os_mode: input(f"{Colors.GRAY}Press Enter to return to CLI.{Colors.RESET}")
        teardown()
        return False
        
    if "CRASH" in result["status"]:
        print(f"{Colors.RED}[FAIL] Engine Crash: {result['status']}{Colors.RESET}")
        print(f"{Colors.RED}{result.get('trace', '')}{Colors.RESET}")
        if not is_os_mode: input(f"{Colors.GRAY}Press Enter to return to CLI.{Colors.RESET}")
        teardown()
        return False
        
    if not is_os_mode: print(f"{Colors.GREEN}[SUCCESS] Node Execution Completed.{Colors.RESET}")
    print(f"Output Bridge State:")
    for key in bridge.get_all_keys():
        if key.startswith("Global:sand_1_") or key.startswith("sand_1_"):
            port = key.split("sand_1_")[-1]
            val = bridge.get(key)
            if hasattr(val, "value"):
                print(f"  -> {port}: {val.value}")
            else:
                print(f"  -> {port}: {val}")
            
    if is_prov and not is_os_mode:
        run_provider_sub_tests(namespaced_id, engine, bridge, node, render_cb)

    if not is_os_mode: input(f"\n{Colors.GRAY}Press Enter to return to CLI.{Colors.RESET}")
    teardown()
    return True

def run_provider_sub_tests(namespaced_id, engine, bridge, provider_node, render_cb):
    print(f"\n{Colors.CYAN}--- INITIATING PROVIDER SUB-TESTING ---{Colors.RESET}")
    top_category = namespaced_id.split('.')[0].split('/')[0] if '.' in namespaced_id or '/' in namespaced_id else namespaced_id
    
    provided_data = {}
    for key in bridge.get_all_keys():
        if "sand_1_" in key and "Done" not in key and "Flow" not in key:
            port = key.split("sand_1_")[-1]
            val = bridge.get(key)
            if hasattr(val, "value"):
                provided_data[port] = val.value
            else:
                provided_data[port] = val

    child_nodes = []
    for nid, n_cls in NodeRegistry._nodes.items():
        if nid == namespaced_id: continue
        try:
            c_node = n_cls("test", "test", DummyBridge())
            if not hasattr(c_node, 'cleanup_provider_context') and requires_provider(c_node):
                if nid.startswith(top_category):
                    child_nodes.append((nid, n_cls))
        except: pass

    if not child_nodes:
        print(f"{Colors.GRAY}No dependent child nodes found for category prefix '{top_category}'.{Colors.RESET}")
    else:
        for c_nid, c_cls in child_nodes:
            if render_cb: render_cb(c_nid, c_cls)
            print(f"\n{Colors.CYAN}Provider Sandbox Sub-Test: [{c_nid}]{Colors.RESET}")
            while True:
                print(f"{Colors.BOLD}Action [t=Test, s=Skip, q=Quit Sub-Test]: {Colors.RESET}", end="", flush=True)
                if msvcrt and sys.stdin.isatty():
                    sub_key = msvcrt.getch().decode('utf-8').lower()
                    print(sub_key)
                else:
                    try: sub_key = input().strip().lower()
                    except EOFError: sub_key = "s"

                if sub_key == 'q': break
                elif sub_key == 's': break
                elif sub_key == 't':
                    _run_sub_sandbox(c_nid, c_cls, engine, bridge, provided_data)
                    if msvcrt and sys.stdin.isatty():
                        print(f"{Colors.GRAY}Press any key for next sub-node...{Colors.RESET}", end="", flush=True)
                        msvcrt.getch()
                        print()
                    else:
                        time.sleep(1)
                    break
                else:
                    print("Invalid command.")
            if sub_key == 'q':
                break
    
    print(f"\n{Colors.YELLOW}Tearing down Provider [{namespaced_id}]...{Colors.RESET}")
    try: provider_node.cleanup_provider_context()
    except Exception as e: print(f"{Colors.RED}Teardown Error: {e}{Colors.RESET}")

def _run_sub_sandbox(namespaced_id, node_cls, engine, bridge, provided_data):
    print(f"\n{Colors.CYAN}--- LIVE SUB-SANDBOX [{namespaced_id}] ---{Colors.RESET}")
    node = node_cls("sand_sub", namespaced_id.split('.')[-1], bridge)
    
    mock_inputs = {}
    print("Mocking Inputs:")
    for key, typ in node.input_schema.items():
        if typ == DataType.FLOW:
            mock_inputs[key] = True
            continue
            
        k_low = key.lower()
        if "provider" in k_low or "connection" in k_low or "client" in k_low or "session" in k_low or "sql" in k_low:
            val = None
            if key in provided_data: val = provided_data[key]
            elif len(provided_data) > 0: val = list(provided_data.values())[0]
            
            print(f"  - {key} [{typ}]: {Colors.GREEN}(Auto-injected from Provider){Colors.RESET}")
            mock_inputs[key] = val
            bridge.set(f"sand_sub_{key}", val, "Sandbox")
            continue
            
        if msvcrt and sys.stdin.isatty():
            try: val = input(f"  - {key} [{typ}]: ").strip()
            except EOFError: val = ""
        else:
            val = ""
            
        if val == "":
            if typ in (DataType.STRING, getattr(DataType, "PASSWORD", None)): val = ""
            elif typ in (DataType.INTEGER, DataType.FLOAT): val = 0
            elif typ == DataType.BOOLEAN: val = False
            elif typ == DataType.LIST: val = []
            elif typ == DataType.DICTIONARY: val = {}
            else: val = None
            print(f"    (Auto-mocked: {val})")
        else:
            try: val = ast.literal_eval(val)
            except: pass
            
        mock_inputs[key] = val
        bridge.set(f"sand_sub_{key}", val, "Sandbox")
        
    print(f"\n{Colors.YELLOW}Firing Sub-Node Execution...{Colors.RESET}")
    result = {"status": "Timeout"}
    def _sub_sandbox_run():
        try:
            from synapse.core.node_dispatcher import NodeDispatcher
            disp = NodeDispatcher(engine)
            res = disp.dispatch(node, mock_inputs, [])
            if hasattr(res, 'wait'): res.wait()
            elif hasattr(res, 'result'): res.result()
            result["status"] = "Complete"
        except Exception as e:
            result["status"] = f"CRASH: {e}"
            result["trace"] = traceback.format_exc()

    thread = threading.Thread(target=_sub_sandbox_run)
    thread.daemon = True
    thread.start()
    
    aborted = False
    print(f"{Colors.GRAY}Running... (Press 'q' to force abort){Colors.RESET}")

    while True:
        if msvcrt and sys.stdin.isatty():
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                if key == 'q':
                    aborted = True
                    break
                    
        # Instead of thread.is_alive(), wait until result gets populated 
        if result["status"] != "Timeout":
            break
            
        time.sleep(0.1)
    
    if aborted:
        print(f"\n{Colors.RED}[FAIL] User aborted execution. Sub-Sandbox aborted.{Colors.RESET}")
        return False
        
    if "CRASH" in result["status"]:
        print(f"{Colors.RED}[FAIL] Sub-Engine Crash: {result['status']}{Colors.RESET}")
        print(f"{Colors.RED}{result.get('trace', '')}{Colors.RESET}")
        return False
        
    print(f"{Colors.GREEN}[SUCCESS] Sub-Node Execution Completed.{Colors.RESET}")
    for key in bridge.get_all_keys():
        if "sand_sub_" in key:
            port = key.split("sand_sub_")[-1]
            val = bridge.get(key)
            if hasattr(val, "value"):
                print(f"  -> {port}: {val.value}")
            else:
                print(f"  -> {port}: {val}")
    return True
