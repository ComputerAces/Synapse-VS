from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Remap", "Math/Advanced")
class RemapNode(SuperNode):
    """
    Linearly maps a value from one range [In Min, In Max] to another [Out Min, Out Max].
    Commonly used for normalizing sensor data or scaling inputs for UI elements.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The input value to remap.
    - In Min: The lower bound of the input range.
    - In Max: The upper bound of the input range.
    - Out Min: The lower bound of the output range.
    - Out Max: The upper bound of the output range.
    
    Outputs:
    - Flow: Pulse triggered after calculation.
    - Result: The remapped value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.remap_value)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
            "In Min": DataType.FLOAT,
            "In Max": DataType.FLOAT,
            "Out Min": DataType.FLOAT,
            "Out Max": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def remap_value(self, Value=None, **kwargs):
        val_in = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", 0.0)
        in_min = kwargs.get("In Min") if kwargs.get("In Min") is not None else self.properties.get("In Min", 0.0)
        in_max = kwargs.get("In Max") if kwargs.get("In Max") is not None else self.properties.get("In Max", 1.0)
        out_min = kwargs.get("Out Min") if kwargs.get("Out Min") is not None else self.properties.get("Out Min", 0.0)
        out_max = kwargs.get("Out Max") if kwargs.get("Out Max") is not None else self.properties.get("Out Max", 1.0)
        
        try:
            val = float(val_in)
            imin = float(in_min)
            imax = float(in_max)
            omin = float(out_min)
            omax = float(out_max)
            
            # T = (Val - InMin) / (InMax - InMin)
            # Result = OutMin + (OutMax - OutMin) * T
            
            if imax == imin:
                t = 0.0
            else:
                t = (val - imin) / (imax - imin)
                
            res = omin + (omax - omin) * t
            
            self.bridge.set(f"{self.node_id}_Result", res, self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
