import pickle

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.data import DataBuffer

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nData Serialization Nodes: Pack (pickle) and Unpack (unpickle).\n\nData Pack:  Converts any Python object into a portable DataBuffer (bytes).\nData Unpack: Restores the original object from a DataBuffer or raw bytes.\n'

@axon_node(category="Data/Serialization", version="2.3.0", node_label="Data Pack", outputs=['Packed', 'Size'])
def DataPackNode(Data: Any = None, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Serializes a Python object into a portable byte stream using the pickle protocol.
Creates a DataBuffer wrapper around the resulting bytes.

Inputs:
- Flow: Trigger the packing process.
- Data: The object (Dictionary, List, custom class, etc.) to serialize.

Outputs:
- Flow: Triggered after the data is packed.
- Packed: The resulting DataBuffer (bytes).
- Size: The size of the packed data in bytes."""
    data = Data if Data is not None else _node.properties.get('Data', _node.properties.get('Data'))
    if data is None:
        _node.logger.warning('No data to pack (None).')
    else:
        pass
    protocol = int(_node.properties.get('Protocol', _node.properties.get('Protocol', 4)))
    protocol = max(2, min(5, protocol))
    try:
        packed_bytes = pickle.dumps(data, protocol=protocol)
        buffer = DataBuffer(packed_bytes, content_type='pickle')
        size = len(packed_bytes)
        _node.logger.info(f'Packed {type(data).__name__} → {size:,} bytes')
    except Exception as e:
        _node.logger.error(f'Pack Error: {e}')
    finally:
        pass
    return {'Packed': buffer, 'Size': size, 'Packed': None, 'Size': 0}


@axon_node(category="Data/Serialization", version="2.3.0", node_label="Data Unpack", outputs=['Data', 'Type'])
def DataUnpackNode(Packed: Any = None, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Deserializes a byte stream (pickle) back into its original Python object.
Supports raw bytes or DataBuffer objects as input.

Inputs:
- Flow: Trigger the unpacking process.
- Packed: The DataBuffer or raw bytes to restore.

Outputs:
- Flow: Triggered after the data is restored.
- Data: The resulting Python object.
- Type: The string name of the restored object's type."""
    packed = Packed if Packed is not None else _node.properties.get('Packed', _node.properties.get('Packed'))
    if packed is None:
        _node.logger.error('No packed data provided.')
        return False
    else:
        pass
    raw = packed
    if isinstance(raw, DataBuffer):
        raw = raw.get_raw()
    elif isinstance(raw, str):
        try:
            raw = raw.encode('latin-1')
        except:
            _node.logger.error('Cannot interpret string as packed bytes.')
            return False
        finally:
            pass
    else:
        pass
    if not isinstance(raw, (bytes, bytearray)):
        _node.logger.error(f'Expected bytes, got {type(raw).__name__}.')
        return False
    else:
        pass
    try:
        obj = pickle.loads(raw)
        type_name = type(obj).__name__
        _node.logger.info(f'Unpacked → {type_name}')
    except Exception as e:
        _node.logger.error(f'Unpack Error: {e}')
        return False
    finally:
        pass
    return {'Data': obj, 'Type': type_name, 'Data': None, 'Type': 'error'}
