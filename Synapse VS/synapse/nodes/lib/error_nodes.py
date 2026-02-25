from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Last Error Node", "Flow/Error Handling")
class LastErrorNode(SuperNode):
    """
    Retrieves information about the most recent error caught by the engine.
    
    This node is typically used within a Catch block or immediately after a 
    failure to inspect error details such as the message, node ID, and trace.
    
    Inputs:
    - Flow: Trigger the retrieval.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Error Object: An Error object containing Message, Node ID, and context.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_last_error)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Object": DataType.ANY
        }

    def get_last_error(self, **kwargs):
        from synapse.core.data import ErrorObject
        
        # Attempt to grab the most recent global error if one exists
        last_err = self.bridge.get("_SYSTEM_GLOBAL_LAST_ERROR")
        if not last_err:
             last_err = ErrorObject("System", "Last Error Node", {}, "No error recorded.")
        
        self.bridge.set(f"{self.node_id}_Error Object", last_err, self.name)
        self.logger.info("Error object retrieved.")
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Raise Error", "Flow/Error Handling")
class RaiseErrorNode(SuperNode):
    """
    Artificially triggers an error to halt execution or test Error Handling.
    
    When flow reaches this node, it forces a Python exception with the 
    specified message, which will be caught by any active Try/Catch blocks.
    
    Inputs:
    - Flow: Trigger the error.
    - Message: The custom error message to report.
    
    Outputs:
    - Flow: Pulse triggered on success (rarely reached due to error).
    - Error: Pulse triggered if the engine supports non-halting errors.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Message"] = "Manual Error Triggered"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.raise_error)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Message": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error": DataType.FLOW
        }

    def raise_error(self, Message=None, **kwargs):
        msg = Message if Message is not None else kwargs.get("Message") or self.properties.get("Message", "Manual Error Triggered")
        self.logger.error(f"Raising manual exception: {msg}")
        raise Exception(msg)
