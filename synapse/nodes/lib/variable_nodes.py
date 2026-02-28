from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Global Set Var", "Workflow/Variables")
class GlobalSetVarNode(SuperNode):
    """
    Sets a variable at the global (root) level, accessible by any graph or subgraph.
    If the variable doesn't exist, it is created.
    
    Inputs:
    - Flow: Trigger the update.
    - Var Name: The name of the variable.
    - Value: The value to set.
    
    Outputs:
    - Flow: Pulse triggered after the variable is set.
    """
    version = "1.0.1"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.properties["Value"] = None
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        name = kwargs.get("Var Name") or self.properties.get("Var Name")
        val = kwargs.get("Value") or self.properties.get("Value")
        
        if not name:
            self.logger.warning("Global Set Var: No variable name provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # bubble_set ensures it reaches the root registry
        self.bridge.bubble_set(name, val, source_node_id=self.node_id, scope_id="Global")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Global Get Var", "Workflow/Variables")
class GlobalGetVarNode(SuperNode):
    """
    Retrieves a variable from the global (root) level.
    
    Inputs:
    - Flow: Trigger the retrieval.
    - Var Name: The name of the variable.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Value: The current value of the global variable.
    """
    version = "1.0.1"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }

    def do_work(self, **kwargs):
        name = kwargs.get("Var Name") or self.properties.get("Var Name")
        
        if not name:
            self.logger.warning("Global Get Var: No variable name provided.")
            self.set_output("Value", None)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        val = self.bridge.get(name, scope_id="Global")
        self.set_output("Value", val)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Project Set Var", "Workflow/Variables")
class ProjectSetVarNode(SuperNode):
    """
    Sets a variable local to the current graph or subgraph instance.
    Acts like a function-level variable.
    
    Inputs:
    - Flow: Trigger the update.
    - Var Name: The name of the variable.
    - Value: The value to set.
    
    Outputs:
    - Flow: Pulse triggered after the variable is set.
    """
    version = "1.0.1"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.properties["Value"] = None
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        name = kwargs.get("Var Name") or self.properties.get("Var Name")
        val = kwargs.get("Value") or self.properties.get("Value")
        
        if not name:
            self.logger.warning("Project Set Var: No variable name provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Standard set (not bubbled) stays in the local registry
        self.bridge.set(name, val, source_node_id=self.node_id, scope_id="Project")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Project Get Var", "Workflow/Variables")
class ProjectGetVarNode(SuperNode):
    """
    Retrieves a variable local to the current graph or subgraph instance.
    
    Inputs:
    - Flow: Trigger the retrieval.
    - Var Name: The name of the variable.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Value: The current value of the project variable.
    """
    version = "1.0.1"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }

    def do_work(self, **kwargs):
        name = kwargs.get("Var Name") or self.properties.get("Var Name")
        
        if not name:
            self.logger.warning("Project Get Var: No variable name provided.")
            self.set_output("Value", None)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        val = self.bridge.get(name, scope_id="Project")
        self.set_output("Value", val)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
