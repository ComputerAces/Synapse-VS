# 📋 Data Formats

Nodes for parsing and manipulating structured data formats like JSON, CSV, and Office documents.

## Nodes

### CSV Query

**Version**: 2.0.2
**Description**: Filters a list of CSV records using SQL-like query syntax.

Query format: "column operator value" (e.g., "price > 100").
Supports AND for multiple conditions.

Inputs:

- Flow: Triggers the filter.
- Data: The input CSV list.
- Query: The filter string.
  
Outputs:

- Flow: Continues after filtering.
- Results: List of records matching the criteria.
- Count: Number of records found.
  
Properties:

- query: Default filter string.

### CSV Read

**Version**: 2.0.2
**Description**: Reads contents from a CSV file into a structured data format.

Inputs:

- Flow: Triggers the read operation.
- Path: Local filesystem path to the CSV file.
  
Outputs:

- Flow: Continues after file is processed.
- Data: List of dictionaries (if header exists) or list of lists.
- Headers: List of column names found in the first row.
- Row Count: Total number of records processed.
  
Properties:

- delimiter: Character separating values (default: ",").
- has_header: Whether the first row contains field names.

### CSV To JSON

**Version**: 2.0.2
**Description**: Converts CSV text/data (List of Dicts) to a JSON string.

Inputs:

- Flow: Triggers the conversion.
- Data: The CSV record list.
  
Outputs:

- Flow: Continues after conversion.
- JSON: The resulting JSON string.
  
Properties:

- None

### CSV Value

**Version**: 2.0.2
**Description**: Extracts a specific cell or an entire column from CSV data.

Inputs:

- Flow: Triggers the extraction.
- Data: The CSV list (from 'CSV Read' or 'CSV Query').
- Column: Name of the header or numeric index to target.
- Row: Numeric index of the row to target.
  
Outputs:

- Flow: Continues after extraction.
- Value: The captured data (single value or list of values).
- Found: True if the target cell/column exists.
  
Properties:

- mode: Operation mode ('Cell' or 'Column').

### CSV Write

**Version**: 2.0.2
**Description**: Writes a structured list of data to a CSV file on disk.

Inputs:

- Flow: Triggers the write operation.
- Data: List of dictionaries or lists to save.
- Path: Target filesystem path for the output file.
  
Outputs:

- Flow: Continues after the file is saved.
  
Properties:

- delimiter: Character separating values (default: ",").

### Excel Commander

**Version**: 2.0.2
**Description**: Automates Excel operations.

### Excel Provider

**Version**: 2.0.2
**Description**: Defines connection parameters for an Excel workbook.

### JSON Keys

**Version**: 2.0.2
**Description**: Returns all Keys from a Dictionary or Indices from a List.

Useful for iterating through dynamic objects where you don't know the
names of the properties beforehand.

Inputs:

- Flow: Triggers the inspection.
- Data: The Dictionary or List to inspect.
- Path: Optional 'jq-like' address to a sub-object.

Outputs:

- Flow: Continues after inspection.
- Keys: A list containing all keys or indices.
- Length: The total count of entries.
  
Properties:

- path: Default JSON path to query.

### JSON Parse

**Version**: 2.0.2
**Description**: Converts a JSON string into a structured Dictionary or List.

JSON (JavaScript Object Notation) is a standard format for data exchange.
Use this to turn text received from an API or file into data that Synapse
nodes can understand and manipulate.

Inputs:

- Flow: Triggers the parse.
- Text: The raw JSON string to parse.

Outputs:

- Flow: Continues after parse.
- Data: The resulting Dictionary or List object.
- Valid: True if the text was correctly formatted JSON, False otherwise.
  
Properties:

- None

### JSON Query

**Version**: 2.0.2
**Description**: Filters a list of objects using a SQL-like Query string.

Query Examples:

- "price > 100"
- "status == 'active' AND type == 'admin'"
- "tags contains 'urgent'"

Inputs:

- Flow: Triggers the query.
- Data: A List of Dictionaries to filter.
- Query: The filtration string.

Outputs:

- Flow: Continues after query.
- Results: The filtered list of items.
- Count: Number of items that matched the query.
  
Properties:

- query: Default SQL-like query string.

### JSON Stringify

**Version**: 2.0.2
**Description**: Converts a Dictionary or List into a JSON text string.

Useful for saving data to files, sending data to a web server,
or preparing a prompt for an AI model.

Inputs:

- Flow: Triggers the operation.
- Data: The Dictionary or List to convert.

Outputs:

- Flow: Continues after operation.
- Text: The resulting JSON string.
  
Properties:

- indent: Number of spaces for pretty-printing (default: 2).

### JSON Value

**Version**: 2.0.2
**Description**: Extracts a specific value from a JSON object using a Path.

Path Syntax Examples:

- "user.name"      -> Gets the name property from the user object.
- "items[0]"       -> Gets the first item in a list.
- "users[*].id"    -> Gets a list of all user IDs.

Inputs:

- Flow: Triggers the extraction.
- Data: The Dictionary, List, or JSON string to search.
- Path: The 'jq-like' address of the value you want.

Outputs:

- Flow: Continues after extraction.
- Value: The extracted data.
- Found: True if the path exists, otherwise False.
  
Properties:

- path: Default JSON path to query.

---
[Back to Nodes Index](Index.md)
