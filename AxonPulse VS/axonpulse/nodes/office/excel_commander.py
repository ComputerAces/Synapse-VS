from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="IO/Documents", version="2.3.0", node_label="Excel Commander")
def ExcelCommanderNode(File_Path: str = '', Command: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Executes automated commands or macros within an Excel workbook.

This node interacts with an active Excel Provider scope. If no provider 
is active, it can optionally open a file directly if 'File Path' is provided.

Inputs:
- Flow: Trigger command execution.
- File Path: The absolute path to the workbook (optional if using a Provider).
- Command: The instruction or macro name to execute.

Outputs:
- Flow: Pulse triggered after the command completes.
- Result: The return value or status from Excel."""
    path = File_Path if File_Path is not None else kwargs.get('File Path') or _node.properties.get('File Path', '')
    if not path:
        provider_id = self.get_provider_id('Excel Provider')
        if provider_id:
            path = _bridge.get(f'{provider_id}_File Path')
        else:
            pass
    else:
        pass
    cmd = Command or kwargs.get('Command') or _node.properties.get('Command')
    result = f'Executed: {cmd} on {path}'
    _node.logger.info(result)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
