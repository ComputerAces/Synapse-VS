import time
from synapse.utils.logger import setup_logger

logger = setup_logger("SynapseEngine")

class DataMixin:
    """
    Handles data gathering, validation, and casting for the Execution Engine.
    """
    def _gather_inputs(self, node_id, trigger_port):
        node_inputs = {}
        incoming_wires = [w for w in self.wires if w["to_node"] == node_id]
        flow_ports = ["Flow", "True", "False", "Loop", "In", "Exec", "Then", "Else", "Try", "Catch", "Error Flow"]
        
        node = self.nodes.get(node_id)
        
        # [IPC OPTIMIZATION] Gather all keys across wires first
        keys_to_pull = []
        wire_map = {} # bridge_key -> (port_name, source_id, source_port)
        for wire in incoming_wires:
            port_name = wire["to_port"]
            if port_name not in flow_ports:
                 source_id = wire["from_node"]
                 source_port = wire["from_port"]
                 bridge_key = f"{source_id}_{source_port}"
                 keys_to_pull.append(bridge_key)
                 wire_map[bridge_key] = (port_name, source_id, source_port)

        # Bulk Get
        bridge_values = self.bridge.get_batch(keys_to_pull)
        mirror_updates = {}

        for bridge_key, val in bridge_values.items():
            port_name, source_id, source_port = wire_map[bridge_key]
            
            if val is not None:
                mirror_updates[f"{node_id}_{port_name}"] = val
                node_inputs[port_name] = val
            else:
                # [NEW] Source Property Fallback
                # For nodes without Flow (Constant/Memo), we pull directly from their properties
                source_node = self.nodes.get(source_id)
                if source_node:
                    pull_val = None
                    search_key = source_port.lower()
                    for p_key, p_val in source_node.properties.items():
                        if p_key.lower() == search_key:
                            pull_val = p_val
                            break
                    
                    if pull_val is not None:
                        mirror_updates[f"{node_id}_{port_name}"] = pull_val
                        node_inputs[port_name] = pull_val
                
                # Carry over current node property as default if no pulse OR source property found
                elif node and port_name in node.properties:
                    node_inputs[port_name] = node.properties[port_name]

        # Bulk Mirror Update
        if mirror_updates:
            self.bridge.set_batch(mirror_updates, source_node_id="Engine")
            
        # [NEW] Universal Property Fallback for unwired ports
        if node:
            for port_name in node.input_types:
                if port_name in flow_ports: continue
                if port_name not in node_inputs:
                    # Check properties (case-insensitive)
                    search_key = port_name.lower()
                    for p_key, p_val in node.properties.items():
                        if p_key.lower() == search_key:
                            node_inputs[port_name] = p_val
                            break
                 
        # Type Validation
        if node and hasattr(node, "input_types") and node.input_types:
             try:
                 for port, val in node_inputs.items():
                     if port == "_trigger": continue
                     expected_type = node.input_types.get(port)
                     if expected_type:
                         node_inputs[port] = self._validate_and_cast(val, expected_type, node.name, port)
             except ValueError as ve:
                 # Strict Validation Failure
                 error_msg = str(ve)
                 logger.error(error_msg)
                 
                 # 1. Set System Error
                 self.bridge.set("_SYSTEM_LAST_ERROR_MESSAGE", error_msg, "Engine")
                 self.bridge.set("_SYSTEM_LAST_ERROR_NODE", node_id, "Engine")
                 
                 # 2. Trigger Error Flow (if wired)
                 # We need to manually trigger because dispatch() won't be called.
                 self.bridge.set(f"{node_id}_ActivePorts", ["Error Flow", "Error"], "Engine")
                 
                 # 3. Abort Execution for this node
                 return None

        node_inputs["_trigger"] = trigger_port
        return node_inputs

    def _validate_and_cast(self, val, target_type, node_name, port_name):
        """
        Attempts to cast value to target_type with GRACEFUL soft-casting.
        For math operations, returns sensible defaults with warnings instead of raising errors.
        """
        if val is None: return val

        # [DATA SAFETY] Unwrap DataBuffer
        from synapse.core.data import DataBuffer
        if isinstance(val, DataBuffer):
             val = val.get_raw()

        # Proprietary Datetime Format Handling
        if isinstance(val, str) and val.startswith("#") and val.endswith("#"):
            try:
                from synapse.utils.datetime_utils import evaluate_datetime_expression
                # Evaluate expression (e.g. #now + 1d#)
                eval_result = evaluate_datetime_expression(val)
                if eval_result:
                    val = eval_result # Replace val with evaluated string (e.g. #2024-01-02#)
            except Exception as e:
                logger.warning(f"Failed to evaluate datetime expression '{val}': {e}")
        
        try:
            if target_type == "float":
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    # Smart Cleanup: Remove commas, underscores, currency symbols, whitespace
                    cleaned = val.replace(",", "").replace("_", "").replace("$", "").replace("€", "").replace("£", "").strip()
                    if not cleaned: return 0.0 # Graceful empty -> 0
                    try:
                        return float(cleaned)
                    except ValueError:
                        # [GRACEFUL] Extract numeric parts if mixed with text
                        import re
                        numbers = re.findall(r'-?\d+\.?\d*', cleaned)
                        if numbers:
                            logger.warning(f"[AutoCast] '{node_name}.{port_name}': Extracted {numbers[0]} from '{val}'")
                            return float(numbers[0])
                        # Ultimate fallback: return 0.0 with warning
                        logger.warning(f"[AutoCast] '{node_name}.{port_name}': Cannot parse '{val}' as Float, using 0.0")
                        return 0.0
                # Direct conversion for other types
                try:
                    return float(val)
                except:
                    logger.warning(f"[AutoCast] '{node_name}.{port_name}': Cannot convert {type(val).__name__} to Float, using 0.0")
                    return 0.0
            
            elif target_type == "int":
                if isinstance(val, int):
                    return val
                if isinstance(val, float):
                    return int(val)
                if isinstance(val, str):
                    cleaned = val.replace(",", "").replace("_", "").strip()
                    if not cleaned: return 0
                    try:
                        return int(float(cleaned)) # handle "3.5" -> 3
                    except ValueError:
                        # [GRACEFUL] Extract numeric parts
                        import re
                        numbers = re.findall(r'-?\d+', cleaned)
                        if numbers:
                            logger.warning(f"[AutoCast] '{node_name}.{port_name}': Extracted {numbers[0]} from '{val}'")
                            return int(numbers[0])
                        logger.warning(f"[AutoCast] '{node_name}.{port_name}': Cannot parse '{val}' as Int, using 0")
                        return 0
                try:
                    return int(val)
                except:
                    logger.warning(f"[AutoCast] '{node_name}.{port_name}': Cannot convert {type(val).__name__} to Int, using 0")
                    return 0
            
            elif target_type == "bool":
                if isinstance(val, bool):
                    return val
                if isinstance(val, str):
                    val_lower = val.lower().strip()
                    if val_lower in ["true", "yes", "on", "1", "y"]: return True
                    if val_lower in ["false", "no", "off", "0", "n", ""]: return False
                    # [GRACEFUL] Non-empty unknown string = True (Pythonic)
                    logger.warning(f"[AutoCast] '{node_name}.{port_name}': Unknown bool value '{val}', treating as True")
                    return True
                # Numbers: 0 = False, non-zero = True
                if isinstance(val, (int, float)):
                    return val != 0
                return bool(val)
                
            elif target_type == "str":
                return str(val)
                
            elif target_type == "list":
                if isinstance(val, list): return val
                if isinstance(val, tuple): return list(val)
                if isinstance(val, str):
                    # Try JSON parse first
                    if val.startswith("["):
                        try:
                            import json
                            return json.loads(val)
                        except:
                            pass
                    # Comma-separated fallback
                    if "," in val:
                        return [x.strip() for x in val.split(",")]
                return [val]
            
            return val # Unknown type, pass through
            
        except Exception as e:
            logger.warning(f"[AutoCast] Unexpected error in '{node_name}.{port_name}': {e}")
            return val  # Return original on unexpected errors
