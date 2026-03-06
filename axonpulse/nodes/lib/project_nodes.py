from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType

@NodeRegistry.register("Project Var Get", "Workflow")
class ProjectVarGetNode(SuperNode):
    """
    Retrieves a global project variable from the bridge.
    Project variables persist across different graphs within the same project.
    
    Inputs:
    - Flow: Trigger the retrieval.
    - Var Name: The name of the project variable to get.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Value: The current value of the project variable.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_var)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }

    def get_var(self, **kwargs):
        var_name = kwargs.get("Var Name") or self.properties.get("Var Name")
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
    - Var Name: The name of the project variable to set.
    - Value: The new value to assign to the variable.
    
    Outputs:
    - Flow: Pulse triggered after the variable is updated.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Var Name"] = ""
        self.properties["Value"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.set_var)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Var Name": DataType.STRING,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def set_var(self, **kwargs):
        var_name = kwargs.get("Var Name") or self.properties.get("Var Name")
        val_to_set = kwargs.get("Value") or self.properties.get("Value")
        
        if not var_name:
            self.logger.warning("No variable name provided for Project Var Set.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        full_key = f"ProjectVars.{var_name}"
        self.bridge.set(full_key, val_to_set, self.name)
        self.logger.info(f"Updated Project Variable '{var_name}' to: {val_to_set}")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
@NodeRegistry.register("Project Metadata Get", "Workflow")
class ProjectMetadataGetNode(SuperNode):
    """
    Retrieves project metadata (Name, Version, Category, Description) from the bridge.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Name: Project Name.
    - Version: Project Version.
    - Category: Project Category.
    - Description: Project Description.
    """
    node_version = 1

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_metadata)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Name": DataType.STRING,
            "Version": DataType.STRING,
            "Category": DataType.STRING,
            "Description": DataType.STRING
        }

    def get_metadata(self, **kwargs):
        name = self.bridge.get("ProjectMeta.project_name") or ""
        version = self.bridge.get("ProjectMeta.project_version") or "1.0.0"
        category = self.bridge.get("ProjectMeta.project_category") or ""
        description = self.bridge.get("ProjectMeta.project_description") or ""

        self.bridge.set(f"{self.node_id}_Name", name, self.name)
        self.bridge.set(f"{self.node_id}_Version", version, self.name)
        self.bridge.set(f"{self.node_id}_Category", category, self.name)
        self.bridge.set(f"{self.node_id}_Description", description, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Project Metadata Set", "Workflow")
class ProjectMetadataSetNode(SuperNode):
    """
    Updates project metadata in the bridge.
    
    Inputs:
    - Flow: Trigger the update.
    - Name: New Project Name.
    - Version: New Project Version.
    - Category: New Project Category.
    - Description: New Project Description.
    
    Outputs:
    - Flow: Pulse triggered after the update.
    """
    node_version = 1

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Name"] = ""
        self.properties["Version"] = "1.0.0"
        self.properties["Category"] = ""
        self.properties["Description"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.set_metadata)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Name": DataType.STRING,
            "Version": DataType.STRING,
            "Category": DataType.STRING,
            "Description": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def set_metadata(self, **kwargs):
        name = kwargs.get("Name") or self.properties.get("Name")
        version = kwargs.get("Version") or self.properties.get("Version")
        category = kwargs.get("Category") or self.properties.get("Category")
        description = kwargs.get("Description") or self.properties.get("Description")

        if name is not None: self.bridge.set("ProjectMeta.project_name", name, self.name)
        if version is not None: self.bridge.set("ProjectMeta.project_version", version, self.name)
        if category is not None: self.bridge.set("ProjectMeta.project_category", category, self.name)
        if description is not None: self.bridge.set("ProjectMeta.project_description", description, self.name)
        
        self.logger.info(f"Updated Project Metadata: {name} v{version}")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
