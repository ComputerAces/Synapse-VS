from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Raw Data", "Data/Buffers")
class RawDataNode(SuperNode):
    """
    A stateful buffer that stores any data type when triggered by a flow.
    Useful for holding values between execution cycles or across graph branches.
    
    ### Inputs:
    - Flow (flow): Trigger to update the buffered value from the 'Data' input.
    - Data (any): The value to be stored in the buffer.
    
    ### Outputs:
    - Flow (flow): Continues execution after the buffer is updated.
    - Data (any): The currently stored value (persistent across pulses).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        # Use a property so the user can set a default value in the UI
        self.properties["Data"] = None
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Data=None, **kwargs):
        """
        When pulsed, update internal data if a new value is provided, 
        then push the current value to the output.
        """
        # 1. Update internal state if input is wired/provided
        # We check against None specifically as requested
        if Data is not None:
             self.properties["Data"] = Data
             
        # 2. Retrieve current value (either newly set or from properties)
        current_val = self.properties.get("Data")
        
        # 3. Set the output on the bridge
        self.bridge.set(f"{self.node_id}_Data", current_val, self.name)
        
        # 4. Signal next flow
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
