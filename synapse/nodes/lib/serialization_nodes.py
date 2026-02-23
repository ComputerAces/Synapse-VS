"""
Data Serialization Nodes: Pack (pickle) and Unpack (unpickle).

Data Pack:  Converts any Python object into a portable DataBuffer (bytes).
Data Unpack: Restores the original object from a DataBuffer or raw bytes.
"""
import pickle
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.data import DataBuffer


@NodeRegistry.register("Data Pack", "Data/Serialization")
class DataPackNode(SuperNode):
    """
    Serializes a Python object into a portable byte stream using the pickle protocol.
    Creates a DataBuffer wrapper around the resulting bytes.
    
    Inputs:
    - Flow: Trigger the packing process.
    - Data: The object (Dictionary, List, custom class, etc.) to serialize.
    
    Outputs:
    - Flow: Triggered after the data is packed.
    - Packed: The resulting DataBuffer (bytes).
    - Size: The size of the packed data in bytes.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Protocol"] = 4  # pickle protocol version (2-5)
        self.properties["Data"] = None
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Packed": DataType.BYTES,
            "Size": DataType.INTEGER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.pack_data)

    def pack_data(self, Data=None, **kwargs):
        # Fallback with legacy support
        data = Data if Data is not None else self.properties.get("Data", self.properties.get("Data"))
        
        if data is None:
            self.logger.warning("No data to pack (None).")

        protocol = int(self.properties.get("Protocol", self.properties.get("Protocol", 4)))
        protocol = max(2, min(5, protocol))  # Clamp to valid range

        try:
            packed_bytes = pickle.dumps(data, protocol=protocol)
            buffer = DataBuffer(packed_bytes, content_type="pickle")
            size = len(packed_bytes)

            self.bridge.set(f"{self.node_id}_Packed", buffer, self.name)
            self.bridge.set(f"{self.node_id}_Size", size, self.name)
            self.logger.info(f"Packed {type(data).__name__} → {size:,} bytes")

        except Exception as e:
            self.logger.error(f"Pack Error: {e}")
            self.bridge.set(f"{self.node_id}_Packed", None, self.name)
            self.bridge.set(f"{self.node_id}_Size", 0, self.name)
            
        return True


@NodeRegistry.register("Data Unpack", "Data/Serialization")
class DataUnpackNode(SuperNode):
    """
    Deserializes a byte stream (pickle) back into its original Python object.
    Supports raw bytes or DataBuffer objects as input.
    
    Inputs:
    - Flow: Trigger the unpacking process.
    - Packed: The DataBuffer or raw bytes to restore.
    
    Outputs:
    - Flow: Triggered after the data is restored.
    - Data: The resulting Python object.
    - Type: The string name of the restored object's type.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Packed"] = None
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Packed": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Type": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.unpack_data)

    def unpack_data(self, Packed=None, **kwargs):
        # Fallback with legacy support
        packed = Packed if Packed is not None else self.properties.get("Packed", self.properties.get("Packed"))

        if packed is None:
            self.logger.error("No packed data provided.")
            return False

        # Extract raw bytes from DataBuffer if needed
        raw = packed
        if isinstance(raw, DataBuffer):
            raw = raw.get_raw()
        elif isinstance(raw, str):
            try:
                raw = raw.encode("latin-1")
            except:
                self.logger.error("Cannot interpret string as packed bytes.")
                return False

        if not isinstance(raw, (bytes, bytearray)):
            self.logger.error(f"Expected bytes, got {type(raw).__name__}.")
            return False

        try:
            obj = pickle.loads(raw)
            type_name = type(obj).__name__

            self.bridge.set(f"{self.node_id}_Data", obj, self.name)
            self.bridge.set(f"{self.node_id}_Type", type_name, self.name)
            self.logger.info(f"Unpacked → {type_name}")

        except Exception as e:
            self.logger.error(f"Unpack Error: {e}")
            self.bridge.set(f"{self.node_id}_Data", None, self.name)
            self.bridge.set(f"{self.node_id}_Type", "error", self.name)
            return False

        return True
