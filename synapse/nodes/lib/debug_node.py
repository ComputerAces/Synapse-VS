from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Debug Node", "Flow/Debug")
class DebugNode(SuperNode):
    """
    Logs input data to the console for debugging purposes.
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The information to be logged.
    
    Outputs:
    - Flow: Triggered after logging.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True 
        self.is_debug = True 
        self.properties["Header"] = "*"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.debug_print)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Header": DataType.STRING,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def debug_print(self, **kwargs):
        # 1. Resolve Data — Wire value takes priority, then live property read
        d = kwargs.get("Data")
        if d is None:
            # Hot-read from properties for live updates during graph execution
            d = self.properties.get("Data")
        
        # 2. Resolve Header — Wire value takes priority, then live property read
        h = kwargs.get("Header")
        if h is None:
            h = self.properties.get("Header", "*")
        
        # [SUBGRAPH BREADCRUMBS] Prepend subgraph context if present
        sub_id = self.bridge.get("_SYNP_SUBGRAPH_ID")
        if sub_id:
            if h and h != "*": h = f"{sub_id} > {h}"
            else: h = sub_id

        # Format Data
        formatted_data = self._format_data(d)
        
        # Default header to '*' and ensure it is always bracketed
        h = h if h else "*"
        output = f"[{h}] {formatted_data}"
        
        try:
            # Prefix with [DEBUG] so MainWindow routes it to Debug Panel
            print(f"[DEBUG] {output}", flush=True)
        except UnicodeEncodeError:
            safe_output = output.encode('ascii', 'replace').decode('ascii')
            print(f"[DEBUG] {safe_output}", flush=True)
            
        # Standard Behavior
        self.bridge.bubble_set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


    def _format_data(self, data):
        # check for get_debug_info method (Duck Typing for Media Objects)
        if hasattr(data, "get_debug_info") and callable(data.get_debug_info):
            try:
                return str(data.get_debug_info()) 
            except:
                pass

        if data is None:
            return str(None)

        # Basic Data Types
        t = type(data)
        t_name = t.__name__
        
        if isinstance(data, (str, int, float, bool)):
            return str([t_name, data])
            
        if isinstance(data, (list, dict, tuple, set)):
             # For collections, maybe show size/length? User said "make a return List with the the data type"
             # Example: [list, 5] (size) or [list, [...]] (content)?
             # User example: "[vidoe data, 5.0, 34567]" -> [Type/Name, Length, Size]
             # For list/dict, Size = len(). 
             # Let's return [type, len].
             return str([t_name, len(data)])

        # Objects/Other
        return str([t_name, str(data)])
