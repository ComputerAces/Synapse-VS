from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Replace", "Data")
class ReplaceNode(SuperNode):
    """
    Replaces occurrences of a specified value with a new value within a string or list.
    
    Inputs:
    - Flow: Trigger the replacement operation.
    - Target: The source string or list to modify.
    - Old: The value or substring to be replaced.
    - New: The replacement value or substring.
    
    Outputs:
    - Flow: Triggered after the replacement is complete.
    - Result: The modified string or list.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Target"] = ""
        self.properties["Old"] = ""
        self.properties["New"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_replace)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Target": DataType.ANY,
            "Old": DataType.ANY,
            "New": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY
        }

    def process_replace(self, Target=None, Old=None, New=None, **kwargs):
        # 1. Resolve Inputs
        target_val = Target if Target is not None else kwargs.get("Target") or self.properties.get("Target")
        old_val = Old if Old is not None else kwargs.get("Old") or self.properties.get("Old", "")
        new_val = New if New is not None else kwargs.get("New") or self.properties.get("New", "")
        
        result = target_val
        
        if target_val is None:
            self.logger.warning("Target is None.")
            self.bridge.set(f"{self.node_id}_Result", None, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # 2. Logic based on type
        if isinstance(target_val, str):
            old_str = str(old_val)
            new_str = str(new_val)
            result = target_val.replace(old_str, new_str)
            
        elif isinstance(target_val, list):
            result = [new_val if item == old_val else item for item in target_val]
            
        else:
            self.logger.warning(f"Unsupported Target type {type(target_val)}.")
            
        # 3. Set Output
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
