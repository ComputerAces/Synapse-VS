from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType, SortType, SortDirection

import re

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

class BaseListOpNode(SuperNode):
    """Base class for list operations."""

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'List': DataType.LIST}
        self.output_schema = {'Flow': DataType.FLOW, 'Result': DataType.LIST, 'Count': DataType.NUMBER}

    def _set_outputs(self, result):
        count = len(result) if isinstance(result, list) else 0
        self.bridge.set(f'{self.node_id}_Result', result, self.name)
        self.bridge.set(f'{self.node_id}_Count', count, self.name)
        return True

@NodeRegistry.register('List Join', 'Data/Lists')
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
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties['Delimiter'] = ','
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema['Delimiter'] = DataType.STRING
        self.output_schema['Result'] = DataType.STRING

    def register_handlers(self):
        self.register_handler('Flow', self.join_list)

    def join_list(self, List=None, Delimiter=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        delim = Delimiter if Delimiter is not None else self.properties.get('Delimiter', ',')
        if not isinstance(input_list, list):
            input_list = [input_list]
        result = str(delim).join([str(i) for i in input_list])
        self.bridge.set(f'{self.node_id}_Result', result, self.name)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

@NodeRegistry.register('List Filter', 'Data/Lists')
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
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties['Pattern'] = ''
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema['Pattern'] = DataType.STRING

    def register_handlers(self):
        self.register_handler('Flow', self.filter_list)

    def filter_list(self, List=None, Pattern=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        pat = str(Pattern if Pattern is not None else self.properties.get('Pattern', ''))
        if not isinstance(input_list, list):
            input_list = [input_list]
        is_regex = any((c in pat for c in '^$\\.[]{}()|*+?'))
        try:
            if is_regex:
                result = [i for i in input_list if re.search(pat, str(i))]
            else:
                result = [i for i in input_list if pat in str(i)]
        except Exception as e:
            self.logger.error(f'Filter Error: {e}')
            result = []
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return self._set_outputs(result)

@NodeRegistry.register('List Unique', 'Data/Lists')
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
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler('Flow', self.unique_list)

    def unique_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        if not isinstance(input_list, list):
            input_list = [input_list]
        result = list(dict.fromkeys(input_list))
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return self._set_outputs(result)

@NodeRegistry.register('List Sort', 'Data/Lists')
class ListSortNode(BaseListOpNode):
    version = '2.1.0'
    '\n    Sorts a list of items based on a specified type and direction.\n    \n    Inputs:\n    - Flow: Execution trigger.\n    - List: The list to sort.\n    - Sort By: The type of data to sort (Number, String, Date).\n    - Sort Direction: The order of sorting (Ascending, Descending).\n    \n    Outputs:\n    - Flow: Triggered after the list is sorted.\n    - Result: The sorted list.\n    - Count: The number of items in the list.\n    '

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties['Sort By'] = SortType.STRING
        self.properties['Sort Direction'] = SortDirection.ASCENDING
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({'Sort By': SortType, 'Sort Direction': SortDirection})

    def register_handlers(self):
        self.register_handler('Flow', self.sort_list)

    def sort_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        sort_by = kwargs.get('Sort By') or self.properties.get('Sort By', SortType.STRING)
        direction = kwargs.get('Sort Direction') or self.properties.get('Sort Direction', SortDirection.ASCENDING)
        if not isinstance(input_list, list):
            input_list = [input_list]
        reverse = direction == SortDirection.DESCENDING
        try:
            if sort_by == SortType.NUMBER:
                result = sorted(input_list, key=lambda x: float(str(x)) if x is not None and str(x).strip() else 0, reverse=reverse)
            elif sort_by == SortType.DATE:
                from axonpulse.utils.datetime_utils import parse_datetime
                result = sorted(input_list, key=lambda x: parse_datetime(str(x)) if x else 0, reverse=reverse)
            else:
                result = sorted(input_list, key=str, reverse=reverse)
        except Exception as e:
            self.logger.warning(f'Sort Error: {e}')
            result = sorted(input_list, key=str, reverse=reverse)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return self._set_outputs(result)

@NodeRegistry.register('List Reverse', 'Data/Lists')
class ListReverseNode(BaseListOpNode):
    version = '2.1.0'
    '\n    Reverses the order of items in a list.\n    \n    Inputs:\n    - Flow: Execution trigger.\n    - List: The list to reverse.\n    \n    Outputs:\n    - Flow: Triggered after the list is reversed.\n    - Result: The reversed list.\n    - Count: The number of items in the list.\n    '

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler('Flow', self.reverse_list)

    def reverse_list(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        if not isinstance(input_list, list):
            input_list = [input_list]
        result = list(reversed(input_list))
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return self._set_outputs(result)

@NodeRegistry.register('List Add Item', 'Data/Lists')
class ListAddItemNode(BaseListOpNode):
    """
    ### Inputs:
    - Flow (flow): Execution trigger.
    - List (list): The base list to add items to (starts empty if not provided).
    - [Dynamic Inputs]: Add items via the Node's visual context menu.
    
    ### Outputs:
    - Flow (flow): Triggered after the items are added.
    - Result (list): The updated list.
    - Count (number): The length of the updated list.
    """
    version = '2.1.0'
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.hidden_fields = ['Additional Inputs']
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.output_schema['Result'] = DataType.LIST
        self.output_schema['Count'] = DataType.INTEGER

    def register_handlers(self):
        self.register_handler('Flow', self.add_items)

    def add_items(self, List=None, **kwargs):
        input_list = List if List is not None else self.properties.get('List', [])
        if not isinstance(input_list, list):
            if input_list is None:
                current_list = []
            elif hasattr(input_list, '__iter__') and (not isinstance(input_list, (str, bytes))):
                current_list = list(input_list)
            else:
                current_list = [input_list]
        else:
            current_list = list(input_list)
        dynamic_inputs = self.properties.get('Additional Inputs', [])
        if isinstance(dynamic_inputs, str):
            import ast
            try:
                dynamic_inputs = ast.literal_eval(dynamic_inputs)
            except Exception:
                dynamic_inputs = []
        if not isinstance(dynamic_inputs, list):
            dynamic_inputs = []
        for pin_name in dynamic_inputs:
            val = kwargs.get(pin_name)
            if val is None:
                val = self.properties.get(pin_name)
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
                if val[0].lower() in ['str', 'string', 'int', 'integer', 'float', 'number', 'bool', 'boolean', 'any', 'list', 'dict']:
                    val = val[1]
            current_list.append(val)
        self.set_output('List', current_list)
        self.set_output('Count', len(current_list))
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

@axon_node(category="Data/Lists", version="2.3.0", node_label="List Count", outputs=['Count'])
def ListCountNode(List: list = [], _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Returns the number of items in a list.

Inputs:
- Flow: Execution trigger.
- List: The list to count.

Outputs:
- Flow: Triggered after the count is calculated.
- Count: The number of items in the list."""
    input_list = List if List is not None else _node.properties.get('List', [])
    if not isinstance(input_list, list):
        if input_list is None:
            input_list = []
        elif hasattr(input_list, '__iter__') and (not isinstance(input_list, (str, bytes))):
            input_list = list(input_list)
        else:
            input_list = [input_list]
    else:
        pass
    count = len(input_list)
    _node.set_output('Count', count)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
