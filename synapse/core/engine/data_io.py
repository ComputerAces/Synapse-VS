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
        registry = self.port_registry
        
        # [v2.5.0] Gather bridge keys — UUID-based with legacy fallback
        keys_to_pull = []
        legacy_keys = []       # Old-style keys for fallback
        wire_map = {}          # bridge_key → (port_name, source_id, source_port, legacy_key)
        
        # [NUCLEAR] Internal UI keywords to NEVER pull into the data flow
        blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]

        for wire in incoming_wires:
            port_name = wire["to_port"]
            
            # Aggressive Filter for UI Metadata (Skip immediately)
            pn_lower = port_name.lower()
            if any(kw in pn_lower for kw in blocked_keywords):
                continue
                
            if port_name not in flow_ports:
                source_id = wire["from_node"]
                source_port = wire["from_port"]
                
                # Primary: UUID-based key from wire
                uuid_key = wire.get("from_port_uuid")
                if not uuid_key:
                    # Wire was created before PortRegistry — generate on the fly
                    uuid_key = registry.bridge_key(source_id, source_port, "output")
                
                # Legacy fallback key
                legacy_key = f"{source_id}_{source_port}"
                
                keys_to_pull.append(uuid_key)
                legacy_keys.append(legacy_key)
                wire_map[uuid_key] = (port_name, source_id, source_port, legacy_key)

        # Bulk Get (UUID keys)
        bridge_values = self.bridge.get_batch(keys_to_pull) if keys_to_pull else {}
        
        # Identify which UUID keys returned None — need legacy fallback
        missing_uuid_keys = [k for k in keys_to_pull if bridge_values.get(k) is None]
        legacy_fallback_needed = []
        for k in missing_uuid_keys:
            _, _, _, legacy_key = wire_map[k]
            legacy_fallback_needed.append(legacy_key)
        
        # Bulk Get Legacy Keys
        legacy_values = self.bridge.get_batch(legacy_fallback_needed) if legacy_fallback_needed else {}
        
        mirror_updates = {}

        for uuid_key, (port_name, source_id, source_port, legacy_key) in wire_map.items():
            # Try UUID key first, then legacy fallback
            val = bridge_values.get(uuid_key)
            if val is None:
                val = legacy_values.get(legacy_key)
            
            if val is not None:
                # Store under UUID key for the receiving port
                recv_uuid = registry.bridge_key(node_id, port_name, "input")
                mirror_updates[recv_uuid] = val
                node_inputs[port_name] = val
            else:
                # Source Property Fallback
                # For nodes without Flow (Constant/Memo), pull from their properties
                source_node = self.nodes.get(source_id)
                if source_node:
                    pull_val = None
                    search_key = source_port.lower()
                    for p_key, p_val in source_node.properties.items():
                        pk_low = p_key.lower()
                        if pk_low == search_key:
                            pull_val = p_val
                            break
                        # Base Data Node Fallbacks 
                        if search_key == "result" and pk_low == "value":
                            pull_val = p_val
                            break
                        if search_key == "result" and pk_low == "string":
                            pull_val = p_val
                            break
                        if search_key == "string" and pk_low == "data":
                            pull_val = p_val
                            break
                    
                    if pull_val is not None:
                        recv_uuid = registry.bridge_key(node_id, port_name, "input")
                        mirror_updates[recv_uuid] = pull_val
                        node_inputs[port_name] = pull_val
                
                # Current node property as default
                elif node and port_name in node.properties:
                    node_inputs[port_name] = node.properties[port_name]

        # Bulk Mirror Update
        if mirror_updates:
            self.bridge.set_batch(mirror_updates, source_node_id="Engine")
            
        # 2. Multi-Graph / Context Mirroring & Property Fallbacks
        if node:
            # [NUCLEAR] Internal UI keywords to NEVER pull into the data flow
            blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
            
            for port_name in node.input_types:
                # Skip Flow ports or already gathered data
                if port_name in flow_ports or port_name in node_inputs: 
                    continue
                
                # Aggressive Filter for UI Metadata 
                pn_lower = port_name.lower()
                if any(kw in pn_lower for kw in blocked_keywords):
                    continue
                
                # Phase A: Mirroring from Parent Bridge
                if self.parent_bridge:
                    pull_val = self.parent_bridge.get(port_name)
                    if pull_val is None and self.parent_node_id:
                        pull_val = self.parent_bridge.get(f"{self.parent_node_id}_{port_name}")

                    if pull_val is not None:
                        recv_uuid = registry.bridge_key(node_id, port_name, "input")
                        mirror_updates[recv_uuid] = pull_val
                        node_inputs[port_name] = pull_val
                        continue # Found it
                
                # Phase B: Universal Property Fallback
                # Only fallback if we don't already have an explicitly gathered value
                if port_name not in node_inputs:
                    search_key = port_name.lower()
                for p_key, p_val in node.properties.items():
                    if p_key.lower() == search_key:
                        node_inputs[port_name] = p_val
                        break

        # Bulk Mirror Update
        if mirror_updates:
            self.bridge.set_batch(mirror_updates, source_node_id="Engine")
            
        # 3. Type Validation
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
