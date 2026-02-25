from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("List Remove", "Data")
class ListRemoveNode(SuperNode):
    """
    Removes an item from a list at the specified index.
    Returns a new list containing the remaining elements.
    
    Inputs:
    - Flow: Trigger the removal.
    - List: The source list to modify.
    - Index: The zero-based position of the item to remove.
    
    Outputs:
    - Flow: Triggered after the item is removed.
    - Result: The modified list.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.remove_item)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST,
            "Index": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.LIST
        }

    def remove_item(self, List=None, Index=None, **kwargs):
        list_in = List if List is not None else kwargs.get("List") or []
        index_in = Index if Index is not None else kwargs.get("Index") or 0
        
        try:
            # Create a copy to avoid mutating original reference if shared? 
            # (Bridge passes copies usually, but good practice)
            new_list = list(list_in) if isinstance(list_in, list) else [list_in]
            idx = int(index_in)
            
            if 0 <= idx < len(new_list):
                new_list.pop(idx)
            else:
                self.logger.warning(f"Index {idx} out of bounds.")
                
        except Exception as e:
            self.logger.error(f"Error: {e}")
            new_list = list_in
            
        self.bridge.set(f"{self.node_id}_Result", new_list, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
