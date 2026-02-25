from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
import random
from synapse.core.types import DataType

@NodeRegistry.register("Random", "Math/Random")
class RandomNode(SuperNode):
    """
    Generates a pseudo-random number or currency value within a specified range.
    Supports both integer 'Number' and decimal 'Currency' (2 decimal places) types.
    
    Inputs:
    - Flow: Trigger the random generation.
    - Min: The minimum value of the range.
    - Max: The maximum value of the range.
    - Random Type: The type of output ('Number' or 'Currency').
    
    Outputs:
    - Flow: Pulse triggered after generation.
    - Result: The generated random value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Min"] = 0
        self.properties["Max"] = 100
        self.properties["Random Type"] = "Number"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.generate_random)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Min": DataType.FLOAT,
            "Max": DataType.FLOAT,
            "Random Type": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY
        }

    def generate_random(self, Min=None, Max=None, **kwargs):
        min_val = float(Min if Min is not None else kwargs.get("Min") or self.properties.get("Min", 0))
        max_val = float(Max if Max is not None else kwargs.get("Max") or self.properties.get("Max", 100))
        rtype = kwargs.get("Random Type") or self.properties.get("Random Type") or "Number"
        
        if rtype == "Currency":
            val = random.uniform(min_val, max_val)
            val = round(val, 2)
        else:
            start = int(min_val)
            stop = int(max_val)
            if stop <= start: stop = start + 1
            val = random.randrange(start, stop)
            
        self.logger.info(f"Random ({rtype}): {val}")
        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
