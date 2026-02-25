from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Project Var Get", "Workflow")
class ProjectVarGetNode(SuperNode):
    """
    Retrieves a global project variable from the bridge.
    Project variables persist across different graphs within the same project.
    
    Inputs:
    - Flow: Trigger the retrieval.
    - Name: The name of the project variable to get.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Value: The current value of the project variable.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Name"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_var)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }

    def get_var(self, Name=None, **kwargs):
        var_name = Name if Name is not None else self.properties.get("Name")
        if not var_name:
            self.logger.warning("No variable name provided for Project Var Get.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        full_key = f"ProjectVars.{var_name}"
        value = self.bridge.get(full_key)
        self.bridge.set(f"{self.node_id}_Value", value, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Project Var Set", "Workflow")
class ProjectVarSetNode(SuperNode):
    """
    Sets a global project variable in the bridge.
    Project variables persist across different graphs within the same project.
    
    Inputs:
    - Flow: Trigger the update.
    - Name: The name of the project variable to set.
    - Value: The new value to assign to the variable.
    
    Outputs:
    - Flow: Pulse triggered after the variable is updated.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Name"] = ""
        self.properties["Value"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.set_var)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Name": DataType.STRING,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def set_var(self, Value=None, Name=None, **kwargs):
        var_name = Name if Name is not None else self.properties.get("Name")
        val_to_set = Value if Value is not None else self.properties.get("Value")
        
        if not var_name:
            self.logger.warning("No variable name provided for Project Var Set.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        full_key = f"ProjectVars.{var_name}"
        self.bridge.set(full_key, val_to_set, self.name)
        self.logger.info(f"Updated Project Variable '{var_name}' to: {val_to_set}")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
