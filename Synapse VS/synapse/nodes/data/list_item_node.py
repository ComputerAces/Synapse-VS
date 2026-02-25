from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("List Item Node", "Data")
class ListItemNode(SuperNode):
    """
    Retrieves a single item from a list at the specified index.
    Includes safeguards for index-out-of-range errors and invalid inputs.
    
    Inputs:
    - Flow: Trigger the item retrieval.
    - List: The target list to extract an item from.
    - Index: The zero-based position of the item.
    
    Outputs:
    - Flow: Triggered if the item is successfully retrieved.
    - Item: The extracted data item.
    - Error Flow: Triggered if the index is invalid or out of range.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Index"] = 0
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_item)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST,
            "Index": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Item": DataType.ANY,
            "Error Flow": DataType.FLOW
        }

    def get_item(self, List=None, Index=None, **kwargs):
        target_list = List if List is not None else kwargs.get("List") or []
        index = Index if Index is not None else kwargs.get("Index") or self.properties.get("Index", 0)
        
        # Cast index to int if it's string/float (Handled by SuperNode usually, but safety check)
        try:
            index = int(index)
        except (ValueError, TypeError):
             err = f"Index '{index}' is not a valid integer."
             self.logger.error(err)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
             self.bridge.set("_SYSTEM_LAST_ERROR_MESSAGE", err, self.name)
             return True

        if not isinstance(target_list, list):
             err = f"Input 'List' is not a list. Got {type(target_list)}."
             self.logger.error(err)
             self.bridge.set(f"{self.node_id}_Item", None, self.name)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
             self.bridge.set("_SYSTEM_LAST_ERROR_MESSAGE", err, self.name)
             return True
             
        if 0 <= index < len(target_list):
            item = target_list[index]
            self.bridge.set(f"{self.node_id}_Item", item, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        else:
            err = f"Index {index} out of range (Length: {len(target_list)})."
            self.logger.error(err)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            self.bridge.set("_SYSTEM_LAST_ERROR_MESSAGE", err, self.name)
            
        return True
