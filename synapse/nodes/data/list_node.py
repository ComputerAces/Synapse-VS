from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import re

@NodeRegistry.register("List Node", "Data")
class ListNode(SuperNode):
    """
    Creates a new list from multiple dynamic inputs.
    Each input port designated as 'Item X' is collected into the resulting list.
    
    Inputs:
    - Flow: Trigger the list creation.
    - [Dynamic]: Various 'Item' inputs to include in the list.
    
    Outputs:
    - Flow: Triggered after the list is created.
    - List: The resulting Python list.
    - Length: The number of items in the list.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        if "AdditionalInputs" not in self.properties and "additional_inputs" not in self.properties:
            self.properties["AdditionalInputs"] = []
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.create_list)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        # Dynamic inputs
        additional = self.properties.get("AdditionalInputs", [])
        if not additional:
            additional = self.properties.get("additional_inputs", [])
            
        for name in additional:
            self.input_schema[name] = DataType.ANY
            
        self.output_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST,
            "Length": DataType.INTEGER
        }

    def create_list(self, **kwargs):
        items = []
        
        # Collect all defined Item ports from additional_inputs
        additional = self.properties.get("AdditionalInputs", [])
        if not additional:
            additional = self.properties.get("additional_inputs", [])
        item_pattern = re.compile(r"^Item (\d+)$", re.IGNORECASE)
        
        for port_name in additional:
            match = item_pattern.match(port_name)
            if not match:
                continue
                
            # SuperNode passes args in kwargs if they match schema keys
            val = kwargs.get(port_name)
            
            # If not in kwargs (not wired or None), check properties (Case Insensitive to handle UI bugs)
            if val is None:
                val = self.properties.get(port_name)
                if val is None:
                    search_key = port_name.lower()
                    for k, v in self.properties.items():
                        if k.lower() == search_key:
                            val = v
                            break
            
            if val is not None:
                items.append(val)
        
        length = len(items)
        
        self.bridge.set(f"{self.node_id}_List", items, self.name)
        self.bridge.set(f"{self.node_id}_Length", length, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        
        return True
