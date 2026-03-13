import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from axonpulse.nodes.lib.provider_node import ProviderNode

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

serial = None

def ensure_serial():
    global serial
    if serial:
        return True
    if DependencyManager.ensure('pyserial', 'serial'):
        import serial as _s
        serial = _s
        return True
    return False

@NodeRegistry.register('Serial Provider', 'System/Hardware')
class SerialProviderNode(ProviderNode):
    """
    Establishes a Serial communication context (COM port/Baud rate).
    Registers serial settings in the bridge for downstream Serial Port nodes.
    
    Inputs:
    - Flow: Start the Serial provider.
    - Port: The hardware port identifier (e.g., 'COM3', '/dev/ttyUSB0').
    - Baud Rate: The communication speed (default: 9600).
    
    Outputs:
    - Flow: Pulse triggered after the scope successfully closes.
    - Provider Flow: Active pulse for nodes within this serial context.
    - Provider: A dictionary containing the established port settings.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = 'Serial Provider'
        self.properties['Port'] = 'COM3'
        self.properties['Baud Rate'] = 9600

    def define_schema(self):
        super().define_schema()
        self.input_schema['Port'] = DataType.STRING
        self.input_schema['Baud Rate'] = DataType.INTEGER
        self.output_schema['Provider'] = DataType.ANY

    def start_scope(self, **kwargs):
        port = kwargs.get('Port') or self.properties.get('Port')
        baud_rate = kwargs.get('Baud Rate') or self.properties.get('Baud Rate', 9600)
        self.bridge.set(f'{self.node_id}_Port', port, self.name)
        self.bridge.set(f'{self.node_id}_Baud Rate', baud_rate, self.name)
        self.bridge.set(f'{self.node_id}_Provider', {'port': port, 'baud_rate': baud_rate}, self.name)
        return super().start_scope(**kwargs)

@axon_node(category="System/Hardware", version="2.3.0", node_label="Serial Port", outputs=['Response'])
def SerialPortNode(Port: str, Message: str, Baud_Rate: float = 9600, Timeout: float = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sends and receives data over a serial port.
Can discover port settings automatically if nested within a Serial Provider.

Inputs:
- Flow: Trigger the serial transaction.
- Port: The serial port to use (optional if provider is present).
- Message: The string data to send to the device.
- Baud Rate: The communication speed.

Outputs:
- Flow: Pulse triggered after the transaction completes.
- Response: The string data received back from the serial device."""
    port_input = kwargs.get('Port')
    message = str(kwargs.get('Message') or '')
    baud_input = kwargs.get('Baud Rate')
    port = port_input or kwargs.get('Port') or _node.properties.get('Port')
    if not port:
        provider_id = self.get_provider_id('Serial Provider')
        if provider_id:
            port = _bridge.get(f'{provider_id}_Port')
        else:
            pass
    else:
        pass
    if not ensure_serial():
        _node.logger.error('pyserial dependency missing.')
        return False
    else:
        pass
    if not port:
        raise RuntimeError(f'[{_node.name}] Missing Serial Port.')
    else:
        pass
    baud_val = baud_input or kwargs.get('Baud Rate') or _node.properties.get('Baud Rate', 9600)
    baud = int(baud_val)
    timeout = float(kwargs.get('Timeout') or _node.properties.get('Timeout', 1.0))
    try:
        with serial.Serial(port, baud, timeout=timeout) as ser:
            if message:
                ser.write(message.encode('utf-8'))
            else:
                pass
            time.sleep(0.1)
            response = ''
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            else:
                pass
            _node.logger.info(f'Serial sent bytes to {port}, response len: {len(response)}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Serial Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    return response
