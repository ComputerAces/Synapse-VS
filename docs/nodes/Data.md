# 🧩 Data Nodes

This document covers nodes within the **Data** core category.

## 📂 Buffers

### Raw Data

**Version**: `2.1.0`

A stateful buffer that stores any data type when triggered by a flow.
Useful for holding values between execution cycles or across graph branches.

### Inputs:
- Flow (flow): Trigger to update the buffered value from the 'Data' input.
- Data (any): The value to be stored in the buffer.

### Outputs:
- Flow (flow): Continues execution after the buffer is updated.
- Data (any): The currently stored value (persistent across pulses).

---

## 📂 DateTime

### Date Add

**Version**: `2.1.0`

Adds a specified amount of time to a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to add to the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string.

---

### Date Subtract

**Version**: `2.1.0`

Subtracts a specified amount of time from a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to subtract from the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string.

---

## 📂 Dictionaries

### Dict Create

**Version**: `2.1.0`

Creates a dictionary object from an existing dictionary or an optional JSON-formatted string.

Inputs:
- Flow: Execution trigger.
- JSON Data: A dictionary or JSON string to initialize the dictionary with.

Outputs:
- Flow: Triggered after the dictionary is created.
- Dictionary: The resulting dictionary object.

---

### Dict Get

**Version**: `2.1.0`

Retrieves a value from a dictionary using a specified key.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to search.
- Key: The key to look for in the dictionary.

Outputs:
- Flow: Triggered after the search is performed.
- Value: The value associated with the key (if found).
- Found: True if the key exists in the dictionary, otherwise False.

---

### Dict Remove

**Version**: `2.1.0`

Removes a key and its associated value from a dictionary.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to modify.
- Key: The key to remove.

Outputs:
- Flow: Triggered after the key is removed.
- Output Dict: The modified dictionary object.

---

### Dict Set

**Version**: `2.1.0`

Sets or updates a value in a dictionary for a given key. Supports nested paths (e.g., 'user.profile.name').

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to modify.
- Key: The key (or dot-notated path) to set.
- Value: The value to assign to the key.

Outputs:
- Flow: Triggered after the value is set.
- Output Dict: The modified dictionary object.

---

## 📂 General

### Boolean

**Version**: `2.1.0`

Standard data node for boolean values (True/False).
Allows manual entry or dynamic conversion of various inputs to boolean.

Inputs:
- Flow: Trigger execution to update the output result.
- Value: The value to be converted/set (supports strings like 'True', '1', 'Yes').

Outputs:
- Flow: Triggered after processing.
- Result: The resulting boolean value (True or False).

---

### Char Node

**Version**: `2.1.0`

Converts a numerical ASCII/Unicode code point into its character representation.
Supports the full Unicode character range (0 to 1,114,111).

Inputs:
- Flow: Trigger the conversion.
- Code: The integer code point (e.g., 65 for 'A').

Outputs:
- Flow: Triggered after conversion.
- Char: The resulting string character.

---

### Currency

**Version**: `2.1.0`

Standardizes a numerical value into a currency format (rounded to 2 decimal places).

Inputs:
- Flow: Trigger the currency formatting.
- Value: The raw numerical value to process.

Outputs:
- Flow: Triggered after the value is formatted.
- Result: The formatted numerical value (2-decimal float).

---

### Data To String

**Version**: `2.1.0`

Converts a structured Data object (Dictionary or List) into a JSON-formatted string.

Inputs:
- Flow: Trigger the conversion.
- Data: The object (Dictionary or List) to serialize.
- Indent: If True, uses 2-space indentation for readability.

Outputs:
- Flow: Triggered if serialization is successful.
- Error Flow: Triggered if the item cannot be serialized.
- String: The resulting JSON string.

---

### Data Type

**Version**: `2.1.0`

Checks the underlying type of the provided Data and routes execution
flow accordingly.

Inputs:
- Flow: Trigger type check.
- Data: Any data to check.

Outputs:
- String Flow: Triggered if Data is a string.
- Number Flow: Triggered if Data is an integer or float.
- Boolean Flow: Triggered if Data is True or False.
- List Flow: Triggered if Data is a List, Tuple, or Set.
- Dict Flow: Triggered if Data is a Dictionary / JSON object.
- None Flow: Triggered if Data is None or Empty.
- Unknown Flow: Triggered if the type is unrecognized (e.g., custom object or binary).

---

### Date

**Version**: `2.1.0`

Manages a date string value. Defaults to the current system date if not specified.

Inputs:
- Flow: Trigger the date retrieval/update.
- Value: Optional date string (YYYY-MM-DD) to set.

Outputs:
- Flow: Triggered after the date is processed.
- Result: The current date string.

---

### Length

**Version**: `2.1.0`

Calculates the length of lists/strings or normalizes numeric/date values within a range.

Inputs:
- Flow: Trigger the length/normalization calculation.
- Value: The item to process (List, String, Number, or Date).
- Min Value: The lower bound for normalization (optional).
- Max Value: The upper bound for normalization (optional).

Outputs:
- Flow: Triggered after the value is processed.
- Length: The numeric length or normalized 0.0-1.0 value.

---

### List Item Node

**Version**: `2.1.0`

Retrieves a single item from a list at the specified index.
Includes safeguards for index-out-of-range errors and invalid inputs.

Inputs:
- Flow: Trigger the item retrieval.
- List: The target list to extract an item from.
- Index: The zero-based position of the item.

Outputs:
- Flow: Triggered if the item is successfully retrieved.
- Item: The extracted data item.
- Error Flow: Triggered if the index is invalid or out of range.

---

### List Node

**Version**: `2.1.0`

Creates a new list from multiple dynamic inputs.
Each input port designated as 'Item X' is collected into the resulting list.

Inputs:
- Flow: Trigger the list creation.
- [Dynamic]: Various 'Item' inputs to include in the list.

Outputs:
- Flow: Triggered after the list is created.
- List: The resulting Python list.
- Length: The number of items in the list.

---

### List Remove

**Version**: `2.1.0`

Removes an item from a list at the specified index.
Returns a new list containing the remaining elements.

Inputs:
- Flow: Trigger the removal.
- List: The source list to modify.
- Index: The zero-based position of the item to remove.

Outputs:
- Flow: Triggered after the item is removed.
- Result: The modified list.

---

### Number

**Version**: `2.1.0`

Manages a numerical value. Supports automatic conversion from strings and dynamic updates.

Inputs:
- Flow: Trigger the number retrieval/update.
- Value: Optional numerical value to set.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The current numerical value.

---

### Replace

**Version**: `2.1.0`

Replaces occurrences of a specified value with a new value within a string or list.

Inputs:
- Flow: Trigger the replacement operation.
- Target: The source string or list to modify.
- Old: The value or substring to be replaced.
- New: The replacement value or substring.

Outputs:
- Flow: Triggered after the replacement is complete.
- Result: The modified string or list.

---

### Search (Regex)

**Version**: `2.1.0`

Searches for a regular expression pattern within a provided text string.
Returns the first match found, its position, and a success flag.

Inputs:
- Flow: Trigger the search.
- Text: The source string to search within.
- Pattern: The RegEx pattern to look for.
- Start Index: The character position to begin the search from.

Outputs:
- Flow: Triggered after the search is complete.
- Match: The text content of the first match found.
- Position: The character index where the match begins.
- Found: True if a match was successfully identified.

---

### Split Text

**Version**: `2.1.0`

Divides a text string into a list of substrings based on a specified delimiter.

Inputs:
- Flow: Trigger the split operation.
- Text: The source string to be divided.
- Delimiter: The character or substring used to split the text.

Outputs:
- Flow: Triggered after the text is split.
- List: The resulting list of substrings.

---

### String

**Version**: `2.1.0`

Manages a text string value. Supports dynamic updates via the Flow input.

Inputs:
- Flow: Trigger the string retrieval/update.
- Value: Optional text string to set.

Outputs:
- Flow: Triggered after the string is processed.
- Result: The current text string.

---

### String Lowercase

**Version**: `2.1.0`

Converts all characters in a text string to lowercase.

Inputs:
- Flow: Trigger the conversion.
- Value: The source text string.

Outputs:
- Flow: Triggered after conversion.
- Result: The lowercase version of the string.

---

### String Replace

**Version**: `2.1.0`

Replaces occurrences of a substring within a source string. 
Supports replacing the first occurrence or all occurrences, with an optional start position.

Inputs:
- Flow: Trigger the replacement.
- Source: The text string to modify.
- Find: The substring to look for.
- Replace: The replacement substring.
- Start Position: The index to begin searching from.
- All: If True, replaces all occurrences; otherwise, replaces only the first.

Outputs:
- Flow: Triggered after the replacement is complete.
- Result: The modified string.

---

### String To Data

**Version**: `2.1.0`

Parses a JSON-formatted string into a structured Data object (Dictionary or List).

Inputs:
- Flow: Trigger the conversion.
- String: The JSON string to parse.

Outputs:
- Flow: Triggered if parsing is successful.
- Error Flow: Triggered if the string is not valid JSON.
- Data: The resulting Dictionary or List.

---

### String Uppercase

**Version**: `2.1.0`

Converts all characters in a text string to uppercase.

Inputs:
- Flow: Trigger the conversion.
- Value: The source text string.

Outputs:
- Flow: Triggered after conversion.
- Result: The uppercase version of the string.

---

## 📂 JSON

### CSV To JSON

**Version**: `2.1.0`

Converts a CSV data list into a JSON-formatted string.
Useful for preparing data for web APIs or storage.

Inputs:
- Flow: Trigger the conversion.
- Data: The CSV data list to convert.

Outputs:
- Flow: Triggered after conversion.
- JSON: The resulting JSON string.

---

### JSON CSV Converter

**Version**: `2.1.0`

Converts between JSON (list of dicts) and CSV string formats.

Inputs:
- Flow: Execution trigger.
- Data: The data to convert (List for JSON to CSV, String for CSV to JSON).

Properties:
- Action: Set to "JSON to CSV" or "CSV to JSON".

Outputs:
- Flow: Triggered after successful conversion.
- Result: The converted data.

---

### JSON Keys

**Version**: `2.1.0`

Retrieves the keys from a JSON object or the indices from a JSON list at a specified path.

Inputs:
- Flow: Execution trigger.
- Data: The JSON object or list.
- Path: Optional path to a nested object or list within the Data.

Outputs:
- Flow: Triggered after the keys are retrieved.
- Keys: A list containing the keys or indices.
- Length: The number of keys or indices found.

---

### JSON Parse

**Version**: `2.1.0`

Parses a JSON-formatted string into a structured Data object (Dictionary or List).

Inputs:
- Flow: Execution trigger.
- Text: The JSON string to parse.

Outputs:
- Flow: Triggered after the parsing attempt.
- Data: The resulting dictionary or list.
- Valid: True if the string was successfully parsed as JSON, otherwise False.

---

### JSON Query

**Version**: `2.1.0`

Filters a list of objects based on a simple query string (e.g., 'age > 20 AND status == "active"').

Inputs:
- Flow: Execution trigger.
- Data: The list of objects (dictionaries) to query.
- Query: The query string specifying the filtering conditions.

Outputs:
- Flow: Triggered after the query is executed.
- Results: The list of items that match the query.
- Count: The number of items found.

---

### JSON Search

**Version**: `2.1.0`

Recursively searches a JSON object (dictionary/list) for a specific string.

Inputs:
- Flow: Execution trigger.
- Data: The JSON object (dictionary or list) to search.
- Search: The string to look for.
- Match Case: If true, the search is case-sensitive.
- Exact Match: If true, the search string must match the value entirely.

Outputs:
- Flow: Triggered after the search finishes.
- Paths: A list of paths (strings) where the matching values were found.
- Values: A list of the actual values that matched.

---

### JSON Stringify

**Version**: `2.1.0`

Converts a structured Data object (Dictionary or List) into a JSON-formatted string.

Inputs:
- Flow: Execution trigger.
- Data: The object (Dictionary or List) to serialize.

Outputs:
- Flow: Triggered if serialization is successful.
- Text: The resulting JSON string.

---

### JSON Value

**Version**: `2.1.0`

Extracts a value from a JSON object or string using a path (e.g., 'user.name' or 'items[0].id').

Inputs:
- Flow: Execution trigger.
- Data: The JSON object or string to search.
- Path: The dot-notated or bracketed path to the desired value.

Outputs:
- Flow: Triggered after the extraction attempt.
- Value: The extracted value (if found).
- Found: True if the path was successfully resolved, otherwise False.

---

## 📂 Lists

### List Count

**Version**: `2.1.0`

Returns the number of items in a list.

Inputs:
- Flow: Execution trigger.
- List: The list to count.

Outputs:
- Flow: Triggered after the count is calculated.
- Count: The number of items in the list.

---

### List Filter

**Version**: `2.1.0`

Filters a list by keeping only the items that match a specific pattern or string.

Inputs:
- Flow: Execution trigger.
- List: The input list to filter.
- Pattern: The string or regex pattern to match against each item.

Outputs:
- Flow: Triggered after the filter is applied.
- Result: The filtered list containing only matching items.
- Count: The number of items in the filtered list.

---

### List Join

**Version**: `2.1.0`

Combines items of a list into a single string using a specified delimiter.

Inputs:
- Flow: Trigger join operation.
- List: The collection of items to join.
- Delimiter: The string inserted between each item.

Outputs:
- Flow: Triggered after the join is complete.
- Result: The concatenated string.

---

### List Reverse

**Version**: `2.1.0`

Reverses the order of items in a list.

Inputs:
- Flow: Execution trigger.
- List: The list to reverse.

Outputs:
- Flow: Triggered after the list is reversed.
- Result: The reversed list.
- Count: The number of items in the list.

---

### List Sort

**Version**: `2.1.0`

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

---

### List Unique

**Version**: `2.1.0`

Removes duplicate items from a list while preserving the original order.

Inputs:
- Flow: Execution trigger.
- List: The list to process.

Outputs:
- Flow: Triggered after duplicates are removed.
- Result: The list containing only unique items.
- Count: The number of unique items.

---

## 📂 Notes

### Memo

**Version**: `2.1.0`

Provides a text area for notes and documentation within the graph. Can store and output a static or dynamic string.

Inputs:
- Flow: Execution trigger.
- Memo Note: The text content to store or display.

Outputs:
- Flow: Triggered when the node is executed.
- Stored Note: The current text content of the memo.

---

## 📂 Parsers

### CSV Query

**Version**: `2.1.0`

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

---

### CSV Read

**Version**: `2.1.0`

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

---

### CSV Value

**Version**: `2.1.0`

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

---

### CSV Write

**Version**: `2.1.0`

Writes a list of objects or rows to a CSV file.
Automatically generates headers if dictionaries are provided.

Inputs:
- Flow: Trigger the write operation.
- Data: The list of objects or rows to save.
- Path: The destination file path.

Outputs:
- Flow: Triggered after the file is saved successfully.

---

## 📂 Serialization

### Data Pack

**Version**: `2.1.0`

Serializes a Python object into a portable byte stream using the pickle protocol.
Creates a DataBuffer wrapper around the resulting bytes.

Inputs:
- Flow: Trigger the packing process.
- Data: The object (Dictionary, List, custom class, etc.) to serialize.

Outputs:
- Flow: Triggered after the data is packed.
- Packed: The resulting DataBuffer (bytes).
- Size: The size of the packed data in bytes.

---

### Data Unpack

**Version**: `2.1.0`

Deserializes a byte stream (pickle) back into its original Python object.
Supports raw bytes or DataBuffer objects as input.

Inputs:
- Flow: Trigger the unpacking process.
- Packed: The DataBuffer or raw bytes to restore.

Outputs:
- Flow: Triggered after the data is restored.
- Data: The resulting Python object.
- Type: The string name of the restored object's type.

---

## 📂 Strings

### Regex

**Version**: `2.1.0`

Checks if a string matches a regular expression pattern.

Inputs:
- Flow: Execution trigger.
- Text: The string to search.
- Pattern: The regular expression pattern.

Outputs:
- Flow: Triggered after search.
- Found: True if a match was found.
- Matches: List of all matches found.

---

### String Combine

**Version**: `2.1.0`

Combines multiple dynamically added input variables into a single concatenated string.

Inputs:
- Flow: Execution trigger.
- [Dynamic Inputs]: Add as many string inputs as you need via the node's context menu.

Outputs:
- Flow: Triggered after concatenation.
- Result: The combined string.

---

### String Find

**Version**: `2.1.0`

Finds the first occurrence of a substring within a larger string.

Inputs:
- Flow: Execution trigger.
- String: The main string to search within.
- Substring: The text to find.
- Start Index: The position to start searching from (default: 0).

Outputs:
- Flow: Triggered after the search is complete.
- Position: The index of the substring (-1 if not found).

---

### String Join

**Version**: `2.1.0`

Concatenates a list of strings into a single string using a specified separator.

Inputs:
- Flow: Execution trigger.
- List: The list of string items to join.
- Separator: The string to insert between items.

Outputs:
- Flow: Triggered after the join is complete.
- Result: The concatenated string.

---

### String Length

**Version**: `2.1.0`

Calculates the number of characters in a string.

Inputs:
- Flow: Execution trigger.
- String: The string to measure.

Outputs:
- Flow: Triggered after the calculation.
- Result: The character count.

---

### Substring

**Version**: `2.1.0`

Extracts a portion of a string based on start and end indices.

Inputs:
- Flow: Execution trigger.
- String: The source string.
- Start: The starting index (inclusive).
- End: The ending index (exclusive). If empty, extracts to the end.

Outputs:
- Flow: Triggered after the extraction.
- Result: The extracted portion of the string.

---

### Template Injector

**Version**: `2.1.0`

Injects values into a string template using placeholders like {name} or {id}.

Inputs:
- Flow: Execution trigger.
- Template: The string template containing {key} placeholders.
- Input Items: A dictionary of key-value pairs to inject into the template.

Outputs:
- Flow: Triggered after the injection is complete.
- Result: The formatted string with placeholders replaced.

---

[Back to Node Index](Index.md)
