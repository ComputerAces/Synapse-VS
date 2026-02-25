from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
McpManager = None

def ensure_mcp():
    global McpManager
    if McpManager: return True
    
    if DependencyManager.ensure("mcp"):
        from synapse.core.mcp_manager import McpManager as _McpManager
        McpManager = _McpManager
        return True
    return False

@NodeRegistry.register("MCP Client", "Connectivity/MCP")
class MCPClientNode(SuperNode):
    """
    Connects to a Model Context Protocol (MCP) server.
    Supports stdio and SSE transports. Lists available tools upon connection.
    
    Inputs:
    - Flow: Trigger the connection.
    - Config: Server configuration dictionary.
    - Enabled: Toggles the client state.
    
    Outputs:
    - Flow: Triggered after connection attempt.
    - Status: Connection status message.
    - Tools: List of tool names provided by the server.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Server Name"] = "local_server"
        self.properties["Transport"] = "stdio"
        self.properties["Command"] = "python"
        self.properties["Args"] = ["-m", "mcp.server.stdio"]
        self.properties["URL"] = "http://localhost:8000/sse"
        self.properties["Env"] = {}
        self.properties["Enabled"] = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.connect_mcp)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Server Name": DataType.STRING,
            "Transport": DataType.STRING,
            "Command": DataType.STRING,
            "Args": DataType.LIST,
            "Env": DataType.DICT,
            "URL": DataType.STRING,
            "Enabled": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Status": DataType.STRING,
            "Tools": DataType.LIST
        }

    def connect_mcp(self, **kwargs):
        server_name = kwargs.get("Server Name") or self.properties.get("Server Name", "local_server")
        transport = kwargs.get("Transport") or self.properties.get("Transport", "stdio")
        enabled = kwargs.get("Enabled") if kwargs.get("Enabled") is not None else self.properties.get("Enabled", True)
        
        if not enabled: 
             self.bridge.set(f"{self.node_id}_Status", "Disabled", self.name)
             self.bridge.set(f"{self.node_id}_Tools", [], self.name)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True
             
        if not ensure_mcp(): 
             self.bridge.set(f"{self.node_id}_Status", "Missing 'mcp' package", self.name)
             self.bridge.set(f"{self.node_id}_Tools", [], self.name)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True
        
        manager = McpManager.get_instance()
        
        success = False
        status_msg = "Failed"
        tool_names = []
        
        try:
            if transport == "stdio":
                cmd = kwargs.get("Command") or self.properties.get("Command", "python")
                args = kwargs.get("Args") or self.properties.get("Args", [])
                env = kwargs.get("Env") or self.properties.get("Env", {})
                if isinstance(args, str): args = args.split()
                success = manager.connect_stdio(server_name, cmd, args, env)
            elif transport == "sse":
                 url = kwargs.get("URL") or self.properties.get("URL", "")
                 success = manager.connect_sse(server_name, url)
                 
            if success:
                tools = manager.list_tools(server_name)
                tool_names = [t.name for t in tools] if tools else []
                status_msg = "Connected"
            
        except Exception as e:
            status_msg = f"Error: {e}"
            self.logger.error(status_msg)
            
        self.bridge.set(f"{self.node_id}_Status", status_msg, self.name)
        self.bridge.set(f"{self.node_id}_Tools", tool_names, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("MCP Tool", "Connectivity/MCP")
class MCPToolNode(SuperNode):
    """
    Calls a specific tool on a connected MCP server.
    Passes arguments and returns the raw output or error message.
    
    Inputs:
    - Flow: Trigger the tool call.
    - Server: The name of the target MCP server.
    - Tool: The name of the tool to execute.
    - Args: Dictionary of arguments for the tool.
    
    Outputs:
    - Flow: Triggered after the tool execution.
    - Result: The response from the tool.
    - Error: Error message if the call failed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Server"] = "local_server"
        self.properties["Tool"] = ""
        self.properties["Args"] = {}
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.call_tool)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Server": DataType.STRING,
            "Tool": DataType.STRING,
            "Args": DataType.DICT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY,
            "Error": DataType.STRING
        }

    def call_tool(self, Server=None, Tool=None, Args=None, **kwargs):
        tgt_server = Server if Server is not None else kwargs.get("Server") or self.properties.get("Server", "local_server")
        tgt_tool = Tool if Tool is not None else kwargs.get("Tool") or self.properties.get("Tool", "")
        args_val = Args if Args is not None else kwargs.get("Args") or self.properties.get("Args", {})
        
        if not ensure_mcp(): 
            self.bridge.set(f"{self.node_id}_Error", "Missing 'mcp' package", self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        manager = McpManager.get_instance()
        
        if not tgt_server or not tgt_tool:
             self.bridge.set(f"{self.node_id}_Error", "Missing Server or Tool name", self.name)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True
             
        try:
             result = manager.call_tool(tgt_server, tgt_tool, args_val)
             content = []
             if hasattr(result, 'content'):
                 for c in result.content:
                     if hasattr(c, 'text'): content.append(c.text)
                     elif hasattr(c, 'data'): content.append(f"<Binary Data: {len(c.data)} bytes>")
                     else: content.append(str(c))
             
             final_result = content if len(content) > 1 else (content[0] if content else None)
             
             self.bridge.set(f"{self.node_id}_Result", final_result, self.name)
             self.bridge.set(f"{self.node_id}_Error", "", self.name)
             
        except Exception as e:
             self.logger.error(f"MCP Call Error: {e}")
             self.bridge.set(f"{self.node_id}_Error", str(e), self.name)
             self.bridge.set(f"{self.node_id}_Result", None, self.name)
             
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("MCP Resource", "Connectivity/MCP")
class MCPResourceNode(SuperNode):
    """
    Reads a resource from a connected MCP server using a URI.
    Returns the resource content and its associated MIME type.
    
    Inputs:
    - Flow: Trigger the resource read.
    - Server: The name of the target MCP server.
    - URI: The unique identifier for the resource.
    
    Outputs:
    - Flow: Triggered after resource read.
    - Content: The resource data.
    - MimeType: The detected MIME type of the resource.
    - Error: Error message if the read failed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Server"] = ""
        self.properties["URI"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.read_resource)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Server": DataType.STRING,
            "URI": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Content": DataType.ANY,
            "MimeType": DataType.STRING,
            "Error": DataType.STRING
        }

    def read_resource(self, Server=None, URI=None, **kwargs):
        tgt_server = Server if Server is not None else kwargs.get("Server") or self.properties.get("Server", "")
        tgt_uri = URI if URI is not None else kwargs.get("URI") or self.properties.get("URI", "")
        
        if not ensure_mcp(): 
            self.bridge.set(f"{self.node_id}_Error", "Missing 'mcp' package", self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        manager = McpManager.get_instance()
        if not tgt_server or not tgt_uri:
            self.bridge.set(f"{self.node_id}_Error", "Missing Arguments", self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        try:
            result = manager.read_resource(tgt_server, tgt_uri)
            data = ""
            mime = ""
            if hasattr(result, 'contents') and result.contents:
                item = result.contents[0]
                if hasattr(item, 'text'): data = item.text
                if hasattr(item, 'mimeType'): mime = item.mimeType
                
            self.bridge.set(f"{self.node_id}_Content", data, self.name)
            self.bridge.set(f"{self.node_id}_MimeType", mime, self.name)
            self.bridge.set(f"{self.node_id}_Error", "", self.name)
            
        except Exception as e:
            self.logger.error(f"MCP Resource Error: {e}")
            self.bridge.set(f"{self.node_id}_Error", str(e), self.name)
            self.bridge.set(f"{self.node_id}_Content", None, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
