import struct

import math

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

pyaudio = None

def ensure_pyaudio():
    global pyaudio
    if pyaudio:
        return True
    from axonpulse.core.dependencies import DependencyManager
    if DependencyManager.ensure('pyaudio'):
        import pyaudio as _p
        pyaudio = _p
        return True
    return False

@axon_node(category="Media/Audio", version="2.3.0", node_label="Audio Device List", outputs=['Input Names', 'Input IDs', 'Output Names', 'Output IDs', 'Input Devices', 'Output Devices', 'Input Count', 'Output Count'])
def AudioDeviceListNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Scans the system for available audio input and output devices.
Returns lists of device names and their corresponding indices.

Outputs:
- Flow: Triggered after the scan is complete.
- Input Devices: List of strings (e.g., "0: Microphone").
- Output Devices: List of strings (e.g., "3: Speakers").
- Input Count: Number of input devices found.
- Output Count: Number of output devices found."""
    if not ensure_pyaudio():
        _node.logger.error('pyaudio not installed.')
        return False
    else:
        pass
    _node.logger.info('Starting robust audio device scan...')
    p = pyaudio.PyAudio()
    num_devices = p.get_device_count()
    _node.logger.info(f'Total devices reported by PyAudio system: {num_devices}')
    input_names = []
    input_ids = []
    output_names = []
    output_ids = []
    legacy_inputs = []
    legacy_outputs = []
    seen_inputs = set()
    seen_outputs = set()
    for i in range(num_devices):
        try:
            device_info = p.get_device_info_by_index(i)
            name = device_info.get('name')
            max_in = device_info.get('maxInputChannels', 0)
            max_out = device_info.get('maxOutputChannels', 0)
            if max_in > 0:
                if name not in seen_inputs:
                    input_names.append(name)
                    input_ids.append(i)
                    legacy_inputs.append(f'{i}: {name}')
                    seen_inputs.add(name)
                else:
                    pass
            else:
                pass
            if max_out > 0:
                if name not in seen_outputs:
                    output_names.append(name)
                    output_ids.append(i)
                    legacy_outputs.append(f'{i}: {name}')
                    seen_outputs.add(name)
                else:
                    pass
            else:
                pass
            _node.logger.info(f"Device {i}: '{name}' (In: {max_in}, Out: {max_out})")
        except Exception as e:
            _node.logger.warning(f'Failed to query audio device {i}: {e}')
        finally:
            pass
    p.terminate()
    _node.logger.info(f'Scan complete. Unique inputs: {len(input_ids)}, Unique outputs: {len(output_ids)}')
    _node.set_output('Input Names', input_names)
    _node.set_output('Input IDs', input_ids)
    _node.set_output('Output Names', output_names)
    _node.set_output('Output IDs', output_ids)
    _node.set_output('Input Devices', legacy_inputs)
    _node.set_output('Output Devices', legacy_outputs)
    _node.set_output('Input Count', len(input_ids))
    _node.set_output('Output Count', len(output_ids))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
