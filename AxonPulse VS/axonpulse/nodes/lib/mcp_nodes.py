from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

McpManager = None

def ensure_mcp():
    global McpManager
    if McpManager:
        return True
    if DependencyManager.ensure('mcp'):
        from axonpulse.core.mcp_manager import McpManager as _McpManager
        McpManager = _McpManager
        return True
    return False

@axon_node(category="Connectivity/MCP", version="2.3.0", node_label="MCP Client", outputs=['Status', 'Tools'])
def MCPClientNode(Server_Name: str = 'local_server', Transport: str = 'stdio', Command: str = 'python', Args: list = ['-m', 'mcp.server.stdio'], Env: dict = {}, URL: str = 'http://localhost:8000/sse', Enabled: bool = True, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Connects to a Model Context Protocol (MCP) server.
Supports stdio and SSE transports. Lists available tools upon connection.

Inputs:
- Flow: Trigger the connection.
- Config: Server configuration dictionary.
- Enabled: Toggles the client state.

Outputs:
- Flow: Triggered after connection attempt.
- Status: Connection status message.
- Tools: List of tool names provided by the server."""
    server_name = kwargs.get('Server Name') or _node.properties.get('Server Name', 'local_server')
    transport = kwargs.get('Transport') or _node.properties.get('Transport', 'stdio')
    enabled = kwargs.get('Enabled') if kwargs.get('Enabled') is not None else _node.properties.get('Enabled', True)
    if not enabled:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if not ensure_mcp():
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    manager = McpManager.get_instance()
    success = False
    status_msg = 'Failed'
    tool_names = []
    try:
        if transport == 'stdio':
            cmd = kwargs.get('Command') or _node.properties.get('Command', 'python')
            args = kwargs.get('Args') or _node.properties.get('Args', [])
            env = kwargs.get('Env') or _node.properties.get('Env', {})
            if isinstance(args, str):
                args = args.split()
            else:
                pass
            success = manager.connect_stdio(server_name, cmd, args, env)
        elif transport == 'sse':
            url = kwargs.get('URL') or _node.properties.get('URL', '')
            success = manager.connect_sse(server_name, url)
        else:
            pass
        if success:
            tools = manager.list_tools(server_name)
            tool_names = [t.name for t in tools] if tools else []
            status_msg = 'Connected'
        else:
            pass
    except Exception as e:
        status_msg = f'Error: {e}'
        _node.logger.error(status_msg)
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Status': 'Disabled', 'Tools': [], 'Status': "Missing 'mcp' package", 'Tools': [], 'Status': status_msg, 'Tools': tool_names}


@axon_node(category="Connectivity/MCP", version="2.3.0", node_label="MCP Tool", outputs=['Result', 'Error'])
def MCPToolNode(Server: str = 'local_server', Tool: str = '', Args: dict = {}, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calls a specific tool on a connected MCP server.
Passes arguments and returns the raw output or error message.

Inputs:
- Flow: Trigger the tool call.
- Server: The name of the target MCP server.
- Tool: The name of the tool to execute.
- Args: Dictionary of arguments for the tool.

Outputs:
- Flow: Triggered after the tool execution.
- Result: The response from the tool.
- Error: Error message if the call failed."""
    tgt_server = Server if Server is not None else kwargs.get('Server') or _node.properties.get('Server', 'local_server')
    tgt_tool = Tool if Tool is not None else kwargs.get('Tool') or _node.properties.get('Tool', '')
    args_val = Args if Args is not None else kwargs.get('Args') or _node.properties.get('Args', {})
    if not ensure_mcp():
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    manager = McpManager.get_instance()
    if not tgt_server or not tgt_tool:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        result = manager.call_tool(tgt_server, tgt_tool, args_val)
        content = []
        if hasattr(result, 'content'):
            for c in result.content:
                if hasattr(c, 'text'):
                    content.append(c.text)
                elif hasattr(c, 'data'):
                    content.append(f'<Binary Data: {len(c.data)} bytes>')
                else:
                    content.append(str(c))
        else:
            pass
        final_result = content if len(content) > 1 else content[0] if content else None
    except Exception as e:
        _node.logger.error(f'MCP Call Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Error': "Missing 'mcp' package", 'Error': 'Missing Server or Tool name', 'Result': final_result, 'Error': '', 'Error': str(e), 'Result': None}


@axon_node(category="Connectivity/MCP", version="2.3.0", node_label="MCP Resource", outputs=['Content', 'MimeType', 'Error'])
def MCPResourceNode(Server: str = '', URI: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Reads a resource from a connected MCP server using a URI.
Returns the resource content and its associated MIME type.

Inputs:
- Flow: Trigger the resource read.
- Server: The name of the target MCP server.
- URI: The unique identifier for the resource.

Outputs:
- Flow: Triggered after resource read.
- Content: The resource data.
- MimeType: The detected MIME type of the resource.
- Error: Error message if the read failed."""
    tgt_server = Server if Server is not None else kwargs.get('Server') or _node.properties.get('Server', '')
    tgt_uri = URI if URI is not None else kwargs.get('URI') or _node.properties.get('URI', '')
    if not ensure_mcp():
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    manager = McpManager.get_instance()
    if not tgt_server or not tgt_uri:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        result = manager.read_resource(tgt_server, tgt_uri)
        data = ''
        mime = ''
        if hasattr(result, 'contents') and result.contents:
            item = result.contents[0]
            if hasattr(item, 'text'):
                data = item.text
            else:
                pass
            if hasattr(item, 'mimeType'):
                mime = item.mimeType
            else:
                pass
        else:
            pass
    except Exception as e:
        _node.logger.error(f'MCP Resource Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Error': "Missing 'mcp' package", 'Error': 'Missing Arguments', 'Content': data, 'MimeType': mime, 'Error': '', 'Error': str(e), 'Content': None}
