from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Service Return", "Logic")
class ServiceReturnNode(SuperNode):
    """
    Signals the end of a service or subgraph execution phase.
    
    Used within service graphs to return control and data back to 
    the parent graph. It packages all non-flow inputs into a 
    return payload.
    
    Inputs:
    - Flow: Trigger the return.
    
    Outputs:
    - None (Terminator node).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handler("Flow", self.yield_service)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {}

    def yield_service(self, **kwargs):
        # Capture return values
        return_values = {}
        
        # Collect all incoming data ports (STRICT WHITELIST + AGGRESSIVE BLOCK)
        reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
        blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
        
        for k, v in kwargs.items():
            if k.startswith("_SYNP_") and k not in reserved:
                return_values[k] = v
                continue
                
            # [FIX] Capture ALL non-reserved, non-UI-blocked ports
            if k not in reserved:
                # [NUCLEAR] Check for UI keywords in the port name
                pn_lower = k.lower()
                if any(kw in pn_lower for kw in blocked_keywords):
                    continue
                return_values[k] = v

        # [FIX] Resolve Scoped Return Key (Instance Protection)
        parent_id = self.bridge.get("_SYNP_PARENT_NODE_ID")
        return_key = f"SUBGRAPH_RETURN_{parent_id}" if parent_id else "SUBGRAPH_RETURN"
        
        # [FIX] Merge return values safely (Scrub existing data to prevent stale pollution)
        existing_returns = self.bridge.get(return_key) or {}
        if isinstance(existing_returns, dict):
            # Scrub existing data before merge
            to_delete = [k for k in existing_returns if any(kw in k.lower() for kw in blocked_keywords) or k in reserved]
            for k in to_delete: del existing_returns[k]
            
            existing_returns.update(return_values)
            self.bridge.set(return_key, existing_returns, self.name)
        else:
            self.bridge.set(return_key, return_values, self.name)
        
        self.bridge.set("__RETURN_NODE_LABEL__", "Flow", self.name)
        
        # 3. Signal Yield to Engine
        print(f"[{self.name}] Service Yielding control to parent...")
        self.bridge.set("_SYNP_YIELD", True, self.name)
        
        return return_values
