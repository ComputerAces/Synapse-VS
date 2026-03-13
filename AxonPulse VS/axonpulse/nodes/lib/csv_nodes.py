from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import csv

import io

import json

import re

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@NodeRegistry.register('CSV Query', 'Data/Parsers')
class CSVQueryNode(SuperNode):
    """
    Filters CSV data based on simple SQL-like query conditions.
    Supports operators like ==, !=, >, <, and 'contains'.
    
    Inputs:
    - Flow: Trigger the query.
    - Data: The CSV data list to filter.
    - Query: The filter string (e.g., 'Age > 25 AND Status == "Active"').
    
    Outputs:
    - Flow: Triggered after filtering.
    - Results: The filtered list of rows.
    - Count: The number of rows that matched the query.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties['Query'] = ''
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'Data': DataType.LIST, 'Query': DataType.STRING}
        self.output_schema = {'Flow': DataType.FLOW, 'Results': DataType.LIST, 'Count': DataType.NUMBER}

    def register_handlers(self):
        self.register_handler('Flow', self.query_csv)

    def query_csv(self, Data=None, Query=None, **kwargs):
        query_str = Query if Query is not None else self.properties.get('Query', '')
        if not isinstance(Data, list):
            self.logger.error('Data must be a list.')
            return False
        if not query_str or not query_str.strip():
            self.bridge.set(f'{self.node_id}_Results', Data, self.name)
            self.bridge.set(f'{self.node_id}_Count', len(Data), self.name)
            self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
            return True
        conditions = [c.strip() for c in re.split('\\bAND\\b', query_str, flags=re.IGNORECASE)]
        results = [item for item in Data if isinstance(item, dict) and all((self._eval_cond(item, c) for c in conditions))]
        self.bridge.set(f'{self.node_id}_Results', results, self.name)
        self.bridge.set(f'{self.node_id}_Count', len(results), self.name)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

    def _eval_cond(self, item, condition):
        pattern = '^(\\w+)\\s*(==|!=|>=|<=|>|<|contains)\\s*(.+)$'
        m = re.match(pattern, condition.strip())
        if not m:
            return False
        (field, op, val_str) = (m.group(1), m.group(2), m.group(3).strip())
        if field not in item:
            return False
        field_val = item[field]
        comp_val = self._parse_val(val_str)
        try:
            if isinstance(comp_val, (int, float)) and isinstance(field_val, str):
                field_val = float(field_val)
        except ValueError:
            pass
        try:
            if op == '==':
                return field_val == comp_val
            elif op == '!=':
                return field_val != comp_val
            elif op == '>':
                return float(field_val) > float(comp_val)
            elif op == '<':
                return float(field_val) < float(comp_val)
            elif op == '>=':
                return float(field_val) >= float(comp_val)
            elif op == '<=':
                return float(field_val) <= float(comp_val)
            elif op == 'contains':
                return str(comp_val) in str(field_val)
        except:
            return False

    def _parse_val(self, val_str):
        if val_str.startswith("'") and val_str.endswith("'") or (val_str.startswith('"') and val_str.endswith('"')):
            return val_str[1:-1]
        try:
            if '.' in val_str:
                return float(val_str)
            return int(val_str)
        except:
            pass
        if val_str.lower() == 'true':
            return True
        if val_str.lower() == 'false':
            return False
        return val_str

@axon_node(category="Data/Parsers", version="2.3.0", node_label="CSV Read", outputs=['Data', 'Headers', 'RowCount'])
def CSVReadNode(Path: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Reads data from a CSV file and parses it into a list of objects or rows.
Supports custom delimiters and optional header rows.

Inputs:
- Flow: Trigger the read operation.
- Path: The absolute path to the CSV file.

Outputs:
- Flow: Triggered after the file is read.
- Data: The parsed CSV data (list of dictionaries or lists).
- Headers: List of column names found in the header row.
- RowCount: The total number of rows retrieved."""
    path = Path
    if not path or not os.path.isfile(path):
        _node.logger.error(f"File not found: '{path}'")
        return False
    else:
        pass
    delimiter = _node.properties.get('Delimiter', ',')
    has_header = bool(_node.properties.get('Has Header', True))
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = [dict(row) for row in reader]
                headers = reader.fieldnames or []
            else:
                reader = csv.reader(f, delimiter=delimiter)
                rows = [row for row in reader]
                headers = []
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'CSV Read Error: {e}')
        return False
    finally:
        pass
    return {'Data': rows, 'Headers': headers, 'RowCount': len(rows)}


@axon_node(category="Data/Parsers", version="2.3.0", node_label="CSV Write", outputs=['Error Flow'])
def CSVWriteNode(Data: list, Path: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Writes a list of objects or rows to a CSV file.
Automatically generates headers if dictionaries are provided.

Inputs:
- Flow: Trigger the write operation.
- Data: The list of objects or rows to save.
- Path: The destination file path.

Outputs:
- Flow: Triggered after the file is saved successfully."""
    if not Path:
        _node.logger.error('No output path specified.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    if not Data or not isinstance(Data, list):
        _node.logger.error('Data must be a list.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    delimiter = _node.properties.get('Delimiter', ',')
    try:
        if Data and isinstance(Data[0], dict):
            headers = list(Data[0].keys())
            with open(Path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(Data)
        else:
            with open(Path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerows(Data)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'CSV Write Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    finally:
        pass


@axon_node(category="Data/Parsers", version="2.3.0", node_label="CSV Value", outputs=['Value', 'Found'])
def CSVValueNode(Data: list, Column: str, Row: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts a specific value, cell, or column from a CSV data list.
Supports index-based or column-name-based retrieval.

Inputs:
- Flow: Trigger the extraction.
- Data: The CSV data list to extract from.
- Column: The column name or index to retrieve.
- Row: The row index to retrieve (for 'Cell' mode).

Outputs:
- Flow: Triggered after extraction.
- Value: The extracted value or list of values.
- Found: True if the specified data was successfully retrieved."""
    mode = _node.properties.get('Mode', 'Cell')
    if not Data or not isinstance(Data, list):
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if mode == 'Column':
        if not Column:
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        else:
            pass
        values = [row.get(Column) if isinstance(row, dict) else None for row in Data]
    else:
        row_idx = int(Row) if Row is not None else 0
        if row_idx < 0 or row_idx >= len(Data):
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        else:
            pass
        row_data = Data[row_idx]
        found = False
        val = None
        if isinstance(row_data, dict):
            if Column in row_data:
                val = row_data[Column]
                found = True
            else:
                pass
        elif isinstance(row_data, list):
            try:
                col_idx = int(Column) if Column is not None else -1
                if 0 <= col_idx < len(row_data):
                    val = row_data[col_idx]
                    found = True
                else:
                    pass
            except:
                pass
            finally:
                pass
        else:
            pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Found': False, 'Found': False, 'Value': values, 'Found': len(values) > 0, 'Found': False, 'Value': val, 'Found': found}


@axon_node(category="Data/JSON", version="2.3.0", node_label="CSV To JSON", outputs=['JSON'])
def CSVToJSONNode(Data: list, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts a CSV data list into a JSON-formatted string.
Useful for preparing data for web APIs or storage.

Inputs:
- Flow: Trigger the conversion.
- Data: The CSV data list to convert.

Outputs:
- Flow: Triggered after conversion.
- JSON: The resulting JSON string."""
    try:
        result = json.dumps(Data or [], indent=2, default=str)
    except:
        result = '[]'
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
