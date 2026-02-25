from synapse.nodes.lib.loop_node import LoopNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("ForEach Node", "Logic/Control Flow")
class ForEachNode(LoopNode):
    """
    Iterates through a list of items, executing the 'Body' output for each element.
    
    Inputs:
    - Flow: Start the iteration from the first item.
    - Continue: Move to the next item in the list.
    - Break: Terminate the loop immediately.
    - List: The collection of items to iterate over.
    
    Outputs:
    - Flow: Triggered when the entire list has been processed or the loop is broken.
    - Body: Triggered for each individual item in the list.
    - Item: The current value from the list.
    - Index: The zero-based position of the current item.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["List"] = []

    def define_schema(self):
        super().define_schema()
        self.input_schema["List"] = DataType.LIST
        self.output_schema["Item"] = DataType.ANY

    def _on_loop_start(self, **kwargs):
        List = kwargs.get("List")
        if List is None:
            List = self.properties.get("List", [])
        
        # Store the list for subsequent iterations
        self.bridge.set(f"{self.node_id}_internal_list", List, self.name)

    def _check_condition(self, index, **kwargs):
        current_list = self.bridge.get(f"{self.node_id}_internal_list") or []
        
        if index < len(current_list):
            item = current_list[index]
            return True, item
            
        return False, None
