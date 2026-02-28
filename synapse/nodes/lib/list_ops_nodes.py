from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType, SortType, SortDirection
import re

class BaseListOpNode(SuperNode):
    """Base class for list operations."""
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def _set_outputs(self, result):
        count = len(result) if isinstance(result, list) else 0
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_Count", count, self.name)
        return True

@NodeRegistry.register("List Join", "Data/Lists")
class ListJoinNode(BaseListOpNode):
    """
    Combines items of a list into a single string using a specified delimiter.
    
    Inputs:
    - Flow: Trigger join operation.
    - List: The collection of items to join.
    - Delimiter: The string inserted between each item.
    
    Outputs:
    - Flow: Triggered after the join is complete.
    - Result: The concatenated string.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Delimiter"] = ","
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Delimiter"] = DataType.STRING
        self.output_schema["Result"] = DataType.STRING

    def register_handlers(self):
        self.register_handler("Flow", self.join_list)

    def join_list(self, List=None, Delimiter=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        delim = Delimiter if Delimiter is not None else self.properties.get("Delimiter", ",")
        
        if not isinstance(input_list, list): 
            input_list = [input_list]
            
        result = str(delim).join([str(i) for i in input_list])
        
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("List Filter", "Data/Lists")
class ListFilterNode(BaseListOpNode):
    """
    Filters a list by keeping only the items that match a specific pattern or string.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The input list to filter.
    - Pattern: The string or regex pattern to match against each item.
    
    Outputs:
    - Flow: Triggered after the filter is applied.
    - Result: The filtered list containing only matching items.
    - Count: The number of items in the filtered list.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Pattern"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Pattern"] = DataType.STRING

    def register_handlers(self):
        self.register_handler("Flow", self.filter_list)

    def filter_list(self, List=None, Pattern=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        pat = str(Pattern if Pattern is not None else self.properties.get("Pattern", ""))
        
        if not isinstance(input_list, list): 
            input_list = [input_list]
            
        is_regex = any(c in pat for c in r"^$\.[]{}()|*+?")
        
        try:
            if is_regex:
                result = [i for i in input_list if re.search(pat, str(i))]
            else:
                result = [i for i in input_list if pat in str(i)]
        except Exception as e:
            self.logger.error(f"Filter Error: {e}")
            result = []
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return self._set_outputs(result)

@NodeRegistry.register("List Unique", "Data/Lists")
class ListUniqueNode(BaseListOpNode):
    """
    Removes duplicate items from a list while preserving the original order.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The list to process.
    
    Outputs:
    - Flow: Triggered after duplicates are removed.
    - Result: The list containing only unique items.
    - Count: The number of unique items.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.unique_list)

    def unique_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        if not isinstance(input_list, list): 
            input_list = [input_list]
        result = list(dict.fromkeys(input_list)) 
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return self._set_outputs(result)

@NodeRegistry.register("List Sort", "Data/Lists")
class ListSortNode(BaseListOpNode):
    version = "2.1.0"
    """
    Sorts a list of items based on a specified type and direction.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The list to sort.
    - Sort By: The type of data to sort (Number, String, Date).
    - Sort Direction: The order of sorting (Ascending, Descending).
    
    Outputs:
    - Flow: Triggered after the list is sorted.
    - Result: The sorted list.
    - Count: The number of items in the list.
    """
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Sort By"] = SortType.STRING
        self.properties["Sort Direction"] = SortDirection.ASCENDING
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Sort By": SortType,
            "Sort Direction": SortDirection
        })

    def register_handlers(self):
        self.register_handler("Flow", self.sort_list)

    def sort_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        sort_by = kwargs.get("Sort By") or self.properties.get("Sort By", SortType.STRING)
        direction = kwargs.get("Sort Direction") or self.properties.get("Sort Direction", SortDirection.ASCENDING)
        
        if not isinstance(input_list, list): 
            input_list = [input_list]
        
        # Sort logic
        reverse = (direction == SortDirection.DESCENDING)
        
        try:
            if sort_by == SortType.NUMBER:
                result = sorted(input_list, key=lambda x: float(str(x)) if x is not None and str(x).strip() else 0, reverse=reverse)
            elif sort_by == SortType.DATE:
                from synapse.utils.datetime_utils import parse_datetime
                result = sorted(input_list, key=lambda x: parse_datetime(str(x)) if x else 0, reverse=reverse)
            else:
                result = sorted(input_list, key=str, reverse=reverse)
        except Exception as e:
            self.logger.warning(f"Sort Error: {e}")
            result = sorted(input_list, key=str, reverse=reverse)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return self._set_outputs(result)

@NodeRegistry.register("List Reverse", "Data/Lists")
class ListReverseNode(BaseListOpNode):
    version = "2.1.0"
    """
    Reverses the order of items in a list.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The list to reverse.
    
    Outputs:
    - Flow: Triggered after the list is reversed.
    - Result: The reversed list.
    - Count: The number of items in the list.
    """
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.reverse_list)

    def reverse_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        if not isinstance(input_list, list): 
            input_list = [input_list]
        result = list(reversed(input_list))
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return self._set_outputs(result)

@NodeRegistry.register("List Count", "Data/Lists")
class ListCountNode(SuperNode):
    """
    Returns the number of items in a list.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The list to count.
    
    Outputs:
    - Flow: Triggered after the count is calculated.
    - Count: The number of items in the list.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["List"] = []
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Count": DataType.INTEGER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.count_list)

    def count_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get("List", [])
        if not isinstance(input_list, list): 
            if input_list is None:
                input_list = []
            elif hasattr(input_list, "__iter__") and not isinstance(input_list, (str, bytes)):
                input_list = list(input_list)
            else:
                input_list = [input_list]
                
        count = len(input_list)
        self.set_output("Count", count)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
