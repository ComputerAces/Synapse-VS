from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import csv
import io
import json
import re
import os

# ─────────────────────────────────────────────────
#  CSV Read Node
# ─────────────────────────────────────────────────

@NodeRegistry.register("CSV Read", "Data/Parsers")
class CSVReadNode(SuperNode):
    """
    Reads data from a CSV file and parses it into a list of objects or rows.
    Supports custom delimiters and optional header rows.
    
    Inputs:
    - Flow: Trigger the read operation.
    - Path: The absolute path to the CSV file.
    
    Outputs:
    - Flow: Triggered after the file is read.
    - Data: The parsed CSV data (list of dictionaries or lists).
    - Headers: List of column names found in the header row.
    - RowCount: The total number of rows retrieved.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Delimiter"] = ","
        self.properties["Has Header"] = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST,
            "Headers": DataType.LIST,
            "RowCount": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.read_csv)

    def read_csv(self, Path=None, **kwargs):
        path = Path 
        if not path or not os.path.isfile(path):
             self.logger.error(f"File not found: '{path}'")
             return False

        delimiter = self.properties.get("Delimiter", ",")
        has_header = bool(self.properties.get("Has Header", True))

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

            self.bridge.set(f"{self.node_id}_Data", rows, self.name)
            self.bridge.set(f"{self.node_id}_Headers", headers, self.name)
            self.bridge.set(f"{self.node_id}_RowCount", len(rows), self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"CSV Read Error: {e}")
            return False

@NodeRegistry.register("CSV Write", "Data/Parsers")
class CSVWriteNode(SuperNode):
    """
    Writes a list of objects or rows to a CSV file.
    Automatically generates headers if dictionaries are provided.
    
    Inputs:
    - Flow: Trigger the write operation.
    - Data: The list of objects or rows to save.
    - Path: The destination file path.
    
    Outputs:
    - Flow: Triggered after the file is saved successfully.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Delimiter"] = ","
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.write_csv)

    def write_csv(self, Data=None, Path=None, **kwargs):
        if not Path:
            self.logger.error("No output path specified.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
        if not Data or not isinstance(Data, list):
            self.logger.error("Data must be a list.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        delimiter = self.properties.get("Delimiter", ",")

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

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"CSV Write Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

@NodeRegistry.register("CSV Value", "Data/Parsers")
class CSVValueNode(SuperNode):
    """
    Extracts a specific value, cell, or column from a CSV data list.
    Supports index-based or column-name-based retrieval.
    
    Inputs:
    - Flow: Trigger the extraction.
    - Data: The CSV data list to extract from.
    - Column: The column name or index to retrieve.
    - Row: The row index to retrieve (for 'Cell' mode).
    
    Outputs:
    - Flow: Triggered after extraction.
    - Value: The extracted value or list of values.
    - Found: True if the specified data was successfully retrieved.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Mode"] = "Cell"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST,
            "Column": DataType.STRING,
            "Row": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.get_value)

    def get_value(self, Data=None, Column=None, Row=None, **kwargs):
        mode = self.properties.get("Mode", "Cell")
        if not Data or not isinstance(Data, list):
            self.bridge.set(f"{self.node_id}_Found", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        if mode == "Column":
            if not Column:
                self.bridge.set(f"{self.node_id}_Found", False, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            values = [row.get(Column) if isinstance(row, dict) else None for row in Data]
            self.bridge.set(f"{self.node_id}_Value", values, self.name)
            self.bridge.set(f"{self.node_id}_Found", len(values) > 0, self.name)
        else:
            row_idx = int(Row) if Row is not None else 0
            if row_idx < 0 or row_idx >= len(Data):
                self.bridge.set(f"{self.node_id}_Found", False, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            row_data = Data[row_idx]
            found = False
            val = None
            if isinstance(row_data, dict):
                if Column in row_data:
                    val = row_data[Column]
                    found = True
            elif isinstance(row_data, list):
                try:
                    col_idx = int(Column) if Column is not None else -1
                    if 0 <= col_idx < len(row_data):
                        val = row_data[col_idx]
                        found = True
                except: pass
            self.bridge.set(f"{self.node_id}_Value", val, self.name)
            self.bridge.set(f"{self.node_id}_Found", found, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("CSV Query", "Data/Parsers")
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
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Query"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST,
            "Query": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Results": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.query_csv)

    def query_csv(self, Data=None, Query=None, **kwargs):
        query_str = Query if Query is not None else self.properties.get("Query", "")
        if not isinstance(Data, list):
            self.logger.error("Data must be a list.")
            return False

        if not query_str or not query_str.strip():
            self.bridge.set(f"{self.node_id}_Results", Data, self.name)
            self.bridge.set(f"{self.node_id}_Count", len(Data), self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        conditions = [c.strip() for c in re.split(r'\bAND\b', query_str, flags=re.IGNORECASE)]
        results = [item for item in Data if isinstance(item, dict) and all(self._eval_cond(item, c) for c in conditions)]

        self.bridge.set(f"{self.node_id}_Results", results, self.name)
        self.bridge.set(f"{self.node_id}_Count", len(results), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _eval_cond(self, item, condition):
        pattern = r"^(\w+)\s*(==|!=|>=|<=|>|<|contains)\s*(.+)$"
        m = re.match(pattern, condition.strip())
        if not m: return False
        field, op, val_str = m.group(1), m.group(2), m.group(3).strip()
        if field not in item: return False
        field_val = item[field]
        comp_val = self._parse_val(val_str)
        try:
            if isinstance(comp_val, (int, float)) and isinstance(field_val, str):
                field_val = float(field_val)
        except ValueError: pass

        try:
            if op == "==": return field_val == comp_val
            elif op == "!=": return field_val != comp_val
            elif op == ">": return float(field_val) > float(comp_val)
            elif op == "<": return float(field_val) < float(comp_val)
            elif op == ">=": return float(field_val) >= float(comp_val)
            elif op == "<=": return float(field_val) <= float(comp_val)
            elif op == "contains": return str(comp_val) in str(field_val)
        except: return False

    def _parse_val(self, val_str):
        if (val_str.startswith("'") and val_str.endswith("'")) or (val_str.startswith('"') and val_str.endswith('"')):
            return val_str[1:-1]
        try:
            if '.' in val_str: return float(val_str)
            return int(val_str)
        except: pass
        if val_str.lower() == 'true': return True
        if val_str.lower() == 'false': return False
        return val_str

@NodeRegistry.register("CSV To JSON", "Data/JSON")
class CSVToJSONNode(SuperNode):
    """
    Converts a CSV data list into a JSON-formatted string.
    Useful for preparing data for web APIs or storage.
    
    Inputs:
    - Flow: Trigger the conversion.
    - Data: The CSV data list to convert.
    
    Outputs:
    - Flow: Triggered after conversion.
    - JSON: The resulting JSON string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "JSON": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Data=None, **kwargs):
        try:
            result = json.dumps(Data or [], indent=2, default=str)
        except:
            result = "[]"
        self.bridge.set(f"{self.node_id}_JSON", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
