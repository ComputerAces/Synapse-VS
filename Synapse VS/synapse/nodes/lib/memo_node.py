from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Memo", "Data/Notes")
class MemoNode(SuperNode):
    """
    Provides a text area for notes and documentation within the graph. Can store and output a static or dynamic string.
    
    Inputs:
    - Flow: Execution trigger.
    - Memo Note: The text content to store or display.
    
    Outputs:
    - Flow: Triggered when the node is executed.
    - Stored Note: The current text content of the memo.
    """
    version = "2.1.0"
 
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Memo Note"] = "Double click to edit note..."
        self.define_schema()
        # No handlers needed as it doesn't process flow, but we can add one if needed.
        # Actually, if it has inputs, it might receive data?
        # But usually Memo is just a static note.
        # IF another node connects to "Memo Note" input, it should update?
        # But without Flow, when does it update? 
        # In SuperNode, we can register "update" handler if we want reactive data?
        # For now, we'll leave it without handlers as it's mostly visual/provider.
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Memo Note": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Stored Note": DataType.STRING
        }
