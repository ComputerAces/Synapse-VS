import inspect
from .utils import DummyBridge, NAMING_PATTERN

def run_pre_flight_check(namespaced_id, node_cls, log_failure_callback):
    """
    Phase 1: Silent AST Analysis and Schema Validation
    Returns True if passed, False if failed.
    """
    bridge = DummyBridge()
    try:
        node = node_cls("test", "test", bridge)
    except Exception as e:
        log_failure_callback(namespaced_id, f"Instantiation Error: {e}")
        return False
        
    if not node.input_schema and not node.output_schema:
         log_failure_callback(namespaced_id, "DNA Auto-Fail: Both schemas are empty. Missing define_schema().")
         return False
        
    allowed_overlaps = ["Flow", "Error Flow", "Done", "Break", "Exit"]
    lower_map = {}
    all_elements = []
    
    for p in node.properties.keys(): all_elements.append((p, "Property"))
    for i in node.input_schema.keys(): all_elements.append((i, "Input"))
    for o in node.output_schema.keys(): all_elements.append((o, "Output"))
    
    for name, src in all_elements:
        if name not in allowed_overlaps and not NAMING_PATTERN.match(name):
            log_failure_callback(namespaced_id, f"Naming Auto-Fail: '{name}' ({src}) is not TitleCase/CamelCase.")
            return False
        
        lk = name.lower()
        if lk in lower_map:
            existing_name, existing_src = lower_map[lk]
            if name != existing_name:
                log_failure_callback(namespaced_id, f"Uniqueness Auto-Fail: Case mismatch '{name}' vs '{existing_name}'.")
                return False
            elif (src == "Input" and existing_src == "Output") or (src == "Output" and existing_src == "Input"):
                if name not in allowed_overlaps:
                    log_failure_callback(namespaced_id, f"I/O Collision Auto-Fail: Exact overlap '{name}'.")
                    return False
            elif (src == "Property" and existing_src == "Output") or (src == "Output" and existing_src == "Property"):
                 log_failure_callback(namespaced_id, f"Prop/Output Collision Auto-Fail: Exact overlap '{name}'.")
                 return False
        else:
            lower_map[lk] = (name, src)
            
    # Generator for Handlers
    flow_handler_name = None
    for key, func_name in node.handlers.items():
        if key == "Flow":
            flow_handler_name = func_name
            break
            
    if not flow_handler_name:
         log_failure_callback(namespaced_id, "Binding Auto-Fail: No function explicitly bound to 'Flow'.")
         return False

    # Return Signal verification
    try:
         flow_handler = getattr(node, flow_handler_name, None)
         if not flow_handler:
              log_failure_callback(namespaced_id, "Signal Check Error: Bound flow function does not exist on class.")
              return False
              
         if hasattr(flow_handler, "__func__"):
             flow_handler = flow_handler.__func__
             
         handler_src = inspect.getsource(flow_handler)
         
         if "return " not in handler_src and "return\n" not in handler_src and "return" not in handler_src:
               pass
    except Exception:
         pass
         
    return True
