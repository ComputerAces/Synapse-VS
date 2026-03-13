import os

import datetime

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="System/Debug", version="2.3.0", node_label="Log")
def LogNode(File_Path: str = 'axonpulse.log', Message: str = '', Level: str = 'INFO', Max_Size_Kb: float = 1024, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Appends a formatted message to a log file and the console.

This node facilitates debugging and tracking by writing timestamped 
messages to a file (managed via Logging Provider or self-defined). 
It supports multiple log levels (INFO, WARNING, ERROR).

Inputs:
- Flow: Trigger the logging operation.
- File Path: The destination log file path.
- Message: The text content to record.
- Level: The severity of the log (e.g., INFO, ERROR).

Outputs:
- Flow: Triggered after the message is logged."""
    file_path = kwargs.get('File Path') or _node.properties.get('File Path', _node.properties.get('FilePath', 'axonpulse.log'))
    message = kwargs.get('Message') or _node.properties.get('Message', '')
    level = (kwargs.get('Level') or _node.properties.get('Level', 'INFO')).upper().strip()
    max_size = kwargs.get('Max Size Kb') or _node.properties.get('Max Size Kb', _node.properties.get('MaxSizeKb', 1024))
    if not file_path:
        provider_id = self.get_provider_id('Logging Provider')
        if provider_id:
            file_path = _bridge.get(f'{provider_id}_File Path')
        else:
            pass
    else:
        pass
    if not file_path:
        file_path = 'axonpulse.log'
    else:
        pass
    print(f'[{level}] {message}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
