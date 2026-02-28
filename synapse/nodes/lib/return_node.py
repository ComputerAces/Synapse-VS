from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Return Node", "Logic/Control Flow")
class ReturnNode(SuperNode):
    """
    The exit point for a graph or subgraph execution.
    
    Sends results back to the caller (e.g., a 'Run Graph' or 'SubGraph' node). 
    It consumes all incoming data and bundles it into the return payload.
    
    Inputs:
    - Flow: Trigger the return.
    
    Outputs:
    - None (Terminator node).
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.hidden_outputs = ["Flow"]
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        # Base schema
        self.input_schema = {"Flow": DataType.FLOW}
        # Terminators are forbidden from having Output Flow or Output Data
        self.output_schema = {}

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        # Capture return values
        return_values = {}
        
        # Collect all incoming data ports (STRICT WHITELIST)
        # We ONLY capture keys that are defined in self.input_types AND not blocked by keywords
        # This prevents UI metadata (Label, header_color, etc.) from leaking even if in schema.
        reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
        blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
        
        for k, v in kwargs.items():
            if k.startswith("_SYNP_") and k not in reserved:
                return_values[k] = v
                continue
                
            # [FIX] Capture ALL non-reserved, non-UI-blocked ports
            # We no longer check 'if k in self.input_types' because dynamic nodes
            # might receive wired data before their internal property-backed schema is updated.
            if k not in reserved:
                # [NUCLEAR] Check for UI keywords in the port name
                pn_lower = k.lower()
                if any(kw in pn_lower for kw in blocked_keywords):
                    continue
                return_values[k] = v
        
        # [FIX] Resolve Scoped Return Key (Instance Protection)
        # We look for _SYNP_PARENT_NODE_ID injected by the calling SubGraphNode.
        parent_id = self.bridge.get("_SYNP_PARENT_NODE_ID")
        return_key = f"SUBGRAPH_RETURN_{parent_id}" if parent_id else "SUBGRAPH_RETURN"
        self.logger.info(f"Using return_key: {return_key} (Parent ID: {parent_id})")
        self.logger.info(f"Captured return_values: {list(return_values.keys())}")

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
        
        # Determine label (engine usually looks for specific node name or default Flow)
        label = self.name if self.name != "Return Node" else "Flow"
        self.bridge.set("__RETURN_NODE_LABEL__", label, self.name)
        
        # No active ports - flow terminates here
        self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        return True

