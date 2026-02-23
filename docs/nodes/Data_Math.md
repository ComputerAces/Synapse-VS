# 📊 Data & Math

Nodes for handling variables, performing arithmetic, and manipulating data structures.

## Nodes

### Abs

**Version**: 2.0.2
**Description**: Calculates the absolute value (magnitude) of a numerical input.
Ensures the result is non-negative.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The absolute value of the input.

### Acos

**Version**: 2.0.2
**Description**: Calculates the arc cosine (inverse cosine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

### Add

**Version**: 2.0.2
**Description**: Combines two values using addition, string concatenation, or list merging.
Automatically detects data types and applies the appropriate combination logic.

Inputs:
- Flow: Trigger the addition process.
- A: The first value (Number, String, or List).
- B: The second value (Number, String, or List).

Outputs:
- Flow: Triggered after combination.
- Result: The sum, merged list, or concatenated string.

### Asin

**Version**: 2.0.2
**Description**: Calculates the arc sine (inverse sine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

### Atan

**Version**: 2.0.2
**Description**: Calculates the arc tangent (inverse tangent) of a value.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

### Atan2

**Version**: 2.0.2
**Description**: Calculates the arc tangent of Y/X, handling quadrant information correctly.
Ensures a result in the full 360-degree (2*pi) range.

Inputs:
- Flow: Trigger the calculation.
- Y: The y-coordinate value.
- X: The x-coordinate value.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set).

### Boolean

**Version**: 2.0.2
**Description**: Standard data node for boolean values (True/False).
Allows manual entry or dynamic conversion of various inputs to boolean.

Inputs:
- Flow: Trigger execution to update the output result.
- Value: The value to be converted/set (supports strings like 'True', '1', 'Yes').

Outputs:
- Flow: Triggered after processing.
- Result: The resulting boolean value (True or False).

### CSV Data Provider

**Version**: 2.0.2
**Description**: Exposes a directory of CSV files as a simple database.
Allows other nodes to read from or write to CSV files within the specified folder.

Inputs:
- Flow: Trigger to enter the data provider scope.
- Folder Path: The directory where CSV files are stored.

Outputs:
- Done: Triggered upon exiting the provider scope.
- Provider Flow: Active while inside the CSV data context.

### CSV Query

**Version**: 2.0.2
**Description**: Filters CSV data based on simple SQL-like query conditions.
Supports operators like ==, !=, >, <, and 'contains'.

Inputs:
- Flow: Trigger the query.
- Data: The CSV data list to filter.
- Query: The filter string (e.g., 'Age > 25 AND Status == "Active"').

Outputs:
- Flow: Triggered after filtering.
- Results: The filtered list of rows.
- Count: The number of rows that matched the query.

### CSV Read

**Version**: 2.0.2
**Description**: Reads data from a CSV file and parses it into a list of objects or rows.
Supports custom delimiters and optional header rows.

Inputs:
- Flow: Trigger the read operation.
- Path: The absolute path to the CSV file.

Outputs:
- Flow: Triggered after the file is read.
- Data: The parsed CSV data (list of dictionaries or lists).
- Headers: List of column names found in the header row.
- RowCount: The total number of rows retrieved.

### CSV To JSON

**Version**: 2.0.2
**Description**: Converts a CSV data list into a JSON-formatted string.
Useful for preparing data for web APIs or storage.

Inputs:
- Flow: Trigger the conversion.
- Data: The CSV data list to convert.

Outputs:
- Flow: Triggered after conversion.
- JSON: The resulting JSON string.

### CSV Value

**Version**: 2.0.2
**Description**: Extracts a specific value, cell, or column from a CSV data list.
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

### CSV Write

**Version**: 2.0.2
**Description**: Writes a list of objects or rows to a CSV file.
Automatically generates headers if dictionaries are provided.

Inputs:
- Flow: Trigger the write operation.
- Data: The list of objects or rows to save.
- Path: The destination file path.

Outputs:
- Flow: Triggered after the file is saved successfully.

### Ceil

**Version**: 2.0.2
**Description**: Rounds a numerical value up to the nearest integer.

Inputs:
- Flow: Trigger the ceiling operation.
- Value: The number to round up.

Outputs:
- Flow: Triggered after rounding.
- Result: The resulting integer.

### Char Node

**Version**: 2.0.2
**Description**: Converts a numerical ASCII/Unicode code point into its character representation.
Supports the full Unicode character range (0 to 1,114,111).

Inputs:
- Flow: Trigger the conversion.
- Code: The integer code point (e.g., 65 for 'A').

Outputs:
- Flow: Triggered after conversion.
- Char: The resulting string character.

### Clamp

**Version**: 2.0.2
**Description**: Restricts a numerical value to a defined range [Min, Max].
If the value is outside the range, it is set to the nearest boundary.

Inputs:
- Flow: Trigger the clamp operation.
- Value: The number to restrict.
- Min: The lower boundary.
- Max: The upper boundary.

Outputs:
- Flow: Triggered after processing.
- Result: The clamped value.

### Cos

**Version**: 2.0.2
**Description**: Calculates the cosine of a given angle.
Supports both Degrees and Radians based on the Degrees property.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The cosine of the angle.

### Currency

**Version**: 2.0.2
**Description**: Standardizes a numerical value into a currency format (rounded to 2 decimal places).

Inputs:
- Flow: Trigger the currency formatting.
- Value: The raw numerical value to process.

Outputs:
- Flow: Triggered after the value is formatted.
- Result: The formatted numerical value (2-decimal float).

### Data Pack

**Version**: 2.0.2
**Description**: Serializes a Python object into a portable byte stream using the pickle protocol.
Creates a DataBuffer wrapper around the resulting bytes.

Inputs:
- Flow: Trigger the packing process.
- Data: The object (Dictionary, List, custom class, etc.) to serialize.

Outputs:
- Flow: Triggered after the data is packed.
- Packed: The resulting DataBuffer (bytes).
- Size: The size of the packed data in bytes.

### Data To String

**Version**: 2.0.2
**Description**: Converts a structured Data object (Dictionary or List) into a JSON-formatted string.

Inputs:
- Flow: Trigger the conversion.
- Data: The object (Dictionary or List) to serialize.
- Indent: If True, uses 2-space indentation for readability.

Outputs:
- Flow: Triggered if serialization is successful.
- Error Flow: Triggered if the item cannot be serialized.
- String: The resulting JSON string.

### Data Unpack

**Version**: 2.0.2
**Description**: Deserializes a byte stream (pickle) back into its original Python object.
Supports raw bytes or DataBuffer objects as input.

Inputs:
- Flow: Trigger the unpacking process.
- Packed: The DataBuffer or raw bytes to restore.

Outputs:
- Flow: Triggered after the data is restored.
- Data: The resulting Python object.
- Type: The string name of the restored object's type.

### Date

**Version**: 2.0.2
**Description**: Manages a date string value. Defaults to the current system date if not specified.

Inputs:
- Flow: Trigger the date retrieval/update.
- Value: Optional date string (YYYY-MM-DD) to set.

Outputs:
- Flow: Triggered after the date is processed.
- Result: The current date string.

### Date Add

**Version**: 2.0.2
**Description**: Adds a specified amount of time to a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to add to the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string.

### Date Subtract

**Version**: 2.0.2
**Description**: Subtracts a specified amount of time from a provided date string and returns the new date.

Inputs:
- Flow: Execution trigger.
- Date: The starting date string (ISO format or 'now').
- Amount: The numeric value to subtract from the date.
- Unit: The time unit (Milliseconds, Seconds, Minutes, Hours, Day, Week, Month, Year).

Outputs:
- Flow: Triggered once the calculation is complete.
- Result: The calculated date as a string.

### Degrees To Radians

**Version**: 2.0.2
**Description**: Converts an angle from degrees to radians.

Inputs:
- Flow: Trigger the conversion.
- Degrees: The angle in degrees.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in radians.

### Dict Create

**Version**: 2.0.2
**Description**: Creates a dictionary object from an existing dictionary or an optional JSON-formatted string.

Inputs:
- Flow: Execution trigger.
- JSON Data: A dictionary or JSON string to initialize the dictionary with.

Outputs:
- Flow: Triggered after the dictionary is created.
- Dictionary: The resulting dictionary object.

### Dict Get

**Version**: 2.0.2
**Description**: Retrieves a value from a dictionary using a specified key.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to search.
- Key: The key to look for in the dictionary.

Outputs:
- Flow: Triggered after the search is performed.
- Value: The value associated with the key (if found).
- Found: True if the key exists in the dictionary, otherwise False.

### Dict Remove

**Version**: 2.0.2
**Description**: Removes a key and its associated value from a dictionary.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to modify.
- Key: The key to remove.

Outputs:
- Flow: Triggered after the key is removed.
- Output Dict: The modified dictionary object.

### Dict Set

**Version**: 2.0.2
**Description**: Sets or updates a value in a dictionary for a given key. Supports nested paths (e.g., 'user.profile.name').

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to modify.
- Key: The key (or dot-notated path) to set.
- Value: The value to assign to the key.

Outputs:
- Flow: Triggered after the value is set.
- Output Dict: The modified dictionary object.

### Divide

**Version**: 2.0.2
**Description**: Divides two numbers and provides the quotient.

Inputs:
- Flow: Execution trigger.
- A: The dividend.
- B: The divisor.
- Handle Div 0: If true, returns 0 instead of triggering Error Flow on division by zero.

Outputs:
- Flow: Triggered on successful division.
- Error Flow: Triggered if division by zero occurs and not handled.
- Result: The quotient.

### Exp

**Version**: 2.0.2
**Description**: Exponential Function (e^x). Calculates the result of Euler's number (e ≈ 2.71828) raised to the power of the input 'Value'.

This node is the inverse of the natural logarithm (LN). It is fundamental in modeling processes that grow or decay 
proportionally to their current value, such as population dynamics, radioactive decay, and continuously compounded interest.

Inputs:
- Flow: Trigger the calculation.
- Value: The exponent (x) for 'e'.

Outputs:
- Flow: Triggered after calculation completion.
- Result: The calculated value (e^Value).

### Floor

**Version**: 2.0.2
**Description**: Rounds a numerical value down to the nearest integer that is less than or equal to the input.

Unlike standard rounding which may round up or down depending on the decimal part, Floor always moves 
the value towards negative infinity. 
Example: 3.7 -> 3.0, -3.2 -> -4.0.

Inputs:
- Flow: Trigger the floor operation.
- Value: The number to round down.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The largest integer less than or equal to 'Value'.

### Inverse Lerp

**Version**: 2.0.2
**Description**: Calculates the normalized interpolant (T) for a value within a specific range [A, B].

This is the inverse of the Lerp operation. It determines where 'Value' sits 
relative to A and B.

Inputs:
- Flow: Trigger the calculation.
- A: The lower bound (maps to 0.0).
- B: The upper bound (maps to 1.0).
- Value: The number to normalize.

Outputs:
- Flow: Triggered after calculation.
- T: The normalized position (0.0 to 1.0).

### JSON CSV Converter

**Version**: 2.0.2
**Description**: Converts between JSON (list of dicts) and CSV string formats.

Inputs:
- Flow: Execution trigger.
- Data: The data to convert (List for JSON to CSV, String for CSV to JSON).

Properties:
- Action: Set to "JSON to CSV" or "CSV to JSON".

Outputs:
- Flow: Triggered after successful conversion.
- Result: The converted data.

### JSON Data Provider

**Version**: 2.0.2
**Description**: Provides a mock database connection backed by a local JSON file.

Inputs:
- Flow: Execution trigger.
- File Path: Path to the JSON database file.

Outputs:
- Flow: Triggered when the provider is initialized.

### JSON Keys

**Version**: 2.0.2
**Description**: Retrieves the keys from a JSON object or the indices from a JSON list at a specified path.

Inputs:
- Flow: Execution trigger.
- Data: The JSON object or list.
- Path: Optional path to a nested object or list within the Data.

Outputs:
- Flow: Triggered after the keys are retrieved.
- Keys: A list containing the keys or indices.
- Length: The number of keys or indices found.

### JSON Parse

**Version**: 2.0.2
**Description**: Parses a JSON-formatted string into a structured Data object (Dictionary or List).

Inputs:
- Flow: Execution trigger.
- Text: The JSON string to parse.

Outputs:
- Flow: Triggered after the parsing attempt.
- Data: The resulting dictionary or list.
- Valid: True if the string was successfully parsed as JSON, otherwise False.

### JSON Query

**Version**: 2.0.2
**Description**: Filters a list of objects based on a simple query string (e.g., 'age > 20 AND status == "active"').

Inputs:
- Flow: Execution trigger.
- Data: The list of objects (dictionaries) to query.
- Query: The query string specifying the filtering conditions.

Outputs:
- Flow: Triggered after the query is executed.
- Results: The list of items that match the query.
- Count: The number of items found.

### JSON Stringify

**Version**: 2.0.2
**Description**: Converts a structured Data object (Dictionary or List) into a JSON-formatted string.

Inputs:
- Flow: Execution trigger.
- Data: The object (Dictionary or List) to serialize.

Outputs:
- Flow: Triggered if serialization is successful.
- Text: The resulting JSON string.

### JSON Value

**Version**: 2.0.2
**Description**: Extracts a value from a JSON object or string using a path (e.g., 'user.name' or 'items[0].id').

Inputs:
- Flow: Execution trigger.
- Data: The JSON object or string to search.
- Path: The dot-notated or bracketed path to the desired value.

Outputs:
- Flow: Triggered after the extraction attempt.
- Value: The extracted value (if found).
- Found: True if the path was successfully resolved, otherwise False.

### Length

**Version**: 2.0.2
**Description**: Calculates the length of lists/strings or normalizes numeric/date values within a range.

Inputs:
- Flow: Trigger the length/normalization calculation.
- Value: The item to process (List, String, Number, or Date).
- Min Value: The lower bound for normalization (optional).
- Max Value: The upper bound for normalization (optional).

Outputs:
- Flow: Triggered after the value is processed.
- Length: The numeric length or normalized 0.0-1.0 value.

### Lerp

**Version**: 2.0.2
**Description**: Performs Linear Interpolation (Lerp) between two values based on a weight factor.

Formula: Result = A + (B - A) * T. 
If T is 0.0, the result is A. If T is 1.0, the result is B.

Inputs:
- Flow: Trigger the calculation.
- A: The start value (0%).
- B: The end value (100%).
- T: The interpolation factor (typically 0.0 to 1.0).

Outputs:
- Flow: Triggered after calculation.
- Result: The interpolated value.

### List Filter

**Version**: 2.0.2
**Description**: Filters a list by keeping only the items that match a specific pattern or string.

Inputs:
- Flow: Execution trigger.
- List: The input list to filter.
- Pattern: The string or regex pattern to match against each item.

Outputs:
- Flow: Triggered after the filter is applied.
- Result: The filtered list containing only matching items.
- Count: The number of items in the filtered list.

### List Item Node

**Version**: 2.0.2
**Description**: Retrieves a single item from a list at the specified index.
Includes safeguards for index-out-of-range errors and invalid inputs.

Inputs:
- Flow: Trigger the item retrieval.
- List: The target list to extract an item from.
- Index: The zero-based position of the item.

Outputs:
- Flow: Triggered if the item is successfully retrieved.
- Item: The extracted data item.
- Error Flow: Triggered if the index is invalid or out of range.

### List Join

**Version**: 2.0.2
**Description**: Combines items of a list into a single string using a specified delimiter.

Inputs:
- Flow: Trigger join operation.
- List: The collection of items to join.
- Delimiter: The string inserted between each item.

Outputs:
- Flow: Triggered after the join is complete.
- Result: The concatenated string.

### List Node

**Version**: 2.0.2
**Description**: Creates a new list from multiple dynamic inputs.
Each input port designated as 'Item X' is collected into the resulting list.

Inputs:
- Flow: Trigger the list creation.
- [Dynamic]: Various 'Item' inputs to include in the list.

Outputs:
- Flow: Triggered after the list is created.
- List: The resulting Python list.
- Length: The number of items in the list.

### List Remove

**Version**: 2.0.2
**Description**: Removes an item from a list at the specified index.
Returns a new list containing the remaining elements.

Inputs:
- Flow: Trigger the removal.
- List: The source list to modify.
- Index: The zero-based position of the item to remove.

Outputs:
- Flow: Triggered after the item is removed.
- Result: The modified list.

### List Reverse

**Version**: 2.0.2
**Description**: Reverses the order of items in a list.

Inputs:
- Flow: Execution trigger.
- List: The list to reverse.

Outputs:
- Flow: Triggered after the list is reversed.
- Result: The reversed list.
- Count: The number of items in the list.

### List Sort

**Version**: 2.0.2
**Description**: Sorts a list of items based on a specified type and direction.

Inputs:
- Flow: Execution trigger.
- List: The list to sort.
- Sort By: The type of data to sort (Number, String, Date).
- Sort Direction: The order of sorting (Ascending, Descending).

Outputs:
- Flow: Triggered after the list is sorted.
- Result: The sorted list.
- Count: The number of items in the list.

### List Unique

**Version**: 2.0.2
**Description**: Removes duplicate items from a list while preserving the original order.

Inputs:
- Flow: Execution trigger.
- List: The list to process.

Outputs:
- Flow: Triggered after duplicates are removed.
- Result: The list containing only unique items.
- Count: The number of unique items.

### Log10

**Version**: 2.0.2
**Description**: Calculates the base-10 logarithm of a given value.
Input must be a positive number.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The base-10 logarithm.

### Logarithm

**Version**: 2.0.2
**Description**: Calculates the logarithm of a value to a specified base.
Handles mathematical undefined cases (non-positive values) through an Error Flow.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to calculate the log for.
- Base: The logarithmic base (defaults to e).

Outputs:
- Flow: Triggered after success.
- Result: The calculated logarithm.
- Error Flow: Triggered if the input is non-positive or calculation fails.

### Max

**Version**: 2.0.2
**Description**: Returns the larger of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The maximum of A and B.

### Memo

**Version**: 2.0.2
**Description**: Provides a text area for notes and documentation within the graph. Can store and output a static or dynamic string.

Inputs:
- Flow: Execution trigger.
- Memo Note: The text content to store or display.

Outputs:
- Flow: Triggered when the node is executed.
- Stored Note: The current text content of the memo.

### Memory Data Provider

**Version**: 2.0.2
**Description**: Provides a temporary in-memory SQL database connection.

Inputs:
- Flow: Execution trigger.

Outputs:
- Flow: Triggered when the provider is initialized.

### Min

**Version**: 2.0.2
**Description**: Returns the smaller of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The minimum of A and B.

### Modulo

**Version**: 2.0.2
**Description**: Calculates the remainder of a division (modulo operation).

Inputs:
- Flow: Trigger the calculation.
- A: The dividend.
- B: The divisor.

Outputs:
- Flow: Triggered after calculation.
- Result: A modulo B.

### Multiply

**Version**: 2.0.2
**Description**: Performs multiplication of two numeric values.
Automatically handles integer and float conversion for the result.

Inputs:
- Flow: Trigger the multiplication.
- A: The first factor.
- B: The second factor.

Outputs:
- Flow: Triggered after the product is calculated.
- Result: The product of A and B.

### MySQL Provider

**Version**: 2.0.2
**Description**: Provides a connection to a MySQL database server.

Inputs:
- Flow: Execution trigger.
- Host: Server hostname or IP address.
- User: Username for authentication.
- Password: Password for authentication.
- Database: Name of the database to connect to.
- Port: Connection port (default 3306).

Outputs:
- Flow: Triggered when the provider is initialized.

### Number

**Version**: 2.0.2
**Description**: Manages a numerical value. Supports automatic conversion from strings and dynamic updates.

Inputs:
- Flow: Trigger the number retrieval/update.
- Value: Optional numerical value to set.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The current numerical value.

### ODBC Provider

**Version**: 2.0.2
**Description**: Provides a connection to a database via ODBC connection string.

Inputs:
- Flow: Execution trigger.
- Connection String: The standard ODBC connection string.

Outputs:
- Flow: Triggered when the provider is initialized.

### Power

**Version**: 2.0.2
**Description**: Calculates the power of a base number raised to an exponent.
Supports negative exponents and fractional bases.

Inputs:
- Flow: Trigger the calculation.
- Base: The number to be raised.
- Exponent: The power to raise the base to.

Outputs:
- Flow: Triggered after calculation.
- Result: The calculated power.

### Radians To Degrees

**Version**: 2.0.2
**Description**: Converts an angle from radians to degrees.

Inputs:
- Flow: Trigger the conversion.
- Radians: The angle in radians.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in degrees.

### Redis Delete

**Version**: 2.0.2
**Description**: Removes a key and its value from Redis.

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to delete.

Outputs:
- Flow: Triggered after deletion.
- Success: True if the deletion command was sent successfully.

### Redis Get

**Version**: 2.0.2
**Description**: Retrieves a value from Redis by its key.

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to fetch.

Outputs:
- Flow: Triggered after the retrieval.
- Value: The data fetched from Redis.
- Found: True if the key exists.

### Redis Keys

**Version**: 2.0.2
**Description**: Retrieves a list of keys matching a specified pattern.

Inputs:
- Flow: Execution trigger.
- Pattern: Glob-style pattern (e.g., "user:*").

Outputs:
- Flow: Triggered after keys are listed.
- Keys: List of matching key names.

### Redis Provider

**Version**: 2.0.2
**Description**: Provides a connection to a Redis server for key-value storage and pub/sub.

Inputs:
- Flow: Execution trigger.
- Host: Redis server hostname or IP.
- Port: Redis server port (default 6379).
- Password: Authentication password.
- DB: Database index (default 0).

Outputs:
- Flow: Triggered when the provider is initialized.
- Connected: True if connection was successful.

### Redis Publish

**Version**: 2.0.2
**Description**: Publishes a message to a Redis channel.

Inputs:
- Flow: Execution trigger.
- Channel: The channel name.
- Message: The string message to publish.

Outputs:
- Flow: Triggered after publishing.
- Subscribers: Number of clients that received the message.

### Redis Set

**Version**: 2.0.2
**Description**: Stores a value in Redis with an optional time-to-live (TTL).

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to set.
- Value: The data to store.
- TTL: Time to live in seconds (optional).

Outputs:
- Flow: Triggered after the set is successful.
- Success: True if the operation succeeded.

### Redis Subscribe

**Version**: 2.0.2
**Description**: Subscribes to a Redis channel and triggers Flow for each received message.

Inputs:
- Flow: Execution trigger.
- Channel: The channel name to watch.

Outputs:
- Flow: Triggered for every new message.
- Message: The content of the received message.
- Channel: The channel where the message originated.

### Regex

**Version**: 2.0.2
**Description**: Checks if a string matches a regular expression pattern.

Inputs:
- Flow: Execution trigger.
- Text: The string to search.
- Pattern: The regular expression pattern.

Outputs:
- Flow: Triggered after search.
- Found: True if a match was found.
- Matches: List of all matches found.

### Remap

**Version**: 2.0.2
**Description**: Linearly maps a value from one range [In Min, In Max] to another [Out Min, Out Max].
Commonly used for normalizing sensor data or scaling inputs for UI elements.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value to remap.
- In Min: The lower bound of the input range.
- In Max: The upper bound of the input range.
- Out Min: The lower bound of the output range.
- Out Max: The upper bound of the output range.

Outputs:
- Flow: Pulse triggered after calculation.
- Result: The remapped value.

### Replace

**Version**: 2.0.2
**Description**: Replaces occurrences of a specified value with a new value within a string or list.

Inputs:
- Flow: Trigger the replacement operation.
- Target: The source string or list to modify.
- Old: The value or substring to be replaced.
- New: The replacement value or substring.

Outputs:
- Flow: Triggered after the replacement is complete.
- Result: The modified string or list.

### Round

**Version**: 2.0.2
**Description**: Rounds a numerical value to a specified number of decimal places.

Inputs:
- Flow: Trigger the round operation.
- Value: The number to round.
- Decimals: The number of decimal places to keep.

Outputs:
- Flow: Triggered after rounding.
- Result: The rounded number.

### SQLite Provider

**Version**: 2.0.2
**Description**: Provides a connection to a local SQLite database file.

Inputs:
- Flow: Execution trigger.
- Filename: The path to the SQLite database file.

Outputs:
- Flow: Triggered when the provider is initialized.

### Search (Regex)

**Version**: 2.0.2
**Description**: Searches for a regular expression pattern within a provided text string.
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

### Sin

**Version**: 2.0.2
**Description**: Calculates the sine of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The sine of the angle.

### Split Text

**Version**: 2.0.2
**Description**: Divides a text string into a list of substrings based on a specified delimiter.

Inputs:
- Flow: Trigger the split operation.
- Text: The source string to be divided.
- Delimiter: The character or substring used to split the text.

Outputs:
- Flow: Triggered after the text is split.
- List: The resulting list of substrings.

### Sqrt

**Version**: 2.0.2
**Description**: Calculates the square root of a given numerical value.
Ensures the input is non-negative (clamped to 0) to avoid imaginary results.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The square root of the input.

### String

**Version**: 2.0.2
**Description**: Manages a text string value. Supports dynamic updates via the Flow input.

Inputs:
- Flow: Trigger the string retrieval/update.
- Value: Optional text string to set.

Outputs:
- Flow: Triggered after the string is processed.
- Result: The current text string.

### String Join

**Version**: 2.0.2
**Description**: Concatenates a list of strings into a single string using a specified separator.

Inputs:
- Flow: Execution trigger.
- List: The list of string items to join.
- Separator: The string to insert between items.

Outputs:
- Flow: Triggered after the join is complete.
- Result: The concatenated string.

### String Length

**Version**: 2.0.2
**Description**: Calculates the number of characters in a string.

Inputs:
- Flow: Execution trigger.
- String: The string to measure.

Outputs:
- Flow: Triggered after the calculation.
- Result: The character count.

### String Lowercase

**Version**: 2.0.2
**Description**: Converts all characters in a text string to lowercase.

Inputs:
- Flow: Trigger the conversion.
- Value: The source text string.

Outputs:
- Flow: Triggered after conversion.
- Result: The lowercase version of the string.

### String Replace

**Version**: 2.0.2
**Description**: Replaces occurrences of a substring within a source string. 
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

### String To Data

**Version**: 2.0.2
**Description**: Parses a JSON-formatted string into a structured Data object (Dictionary or List).

Inputs:
- Flow: Trigger the conversion.
- String: The JSON string to parse.

Outputs:
- Flow: Triggered if parsing is successful.
- Error Flow: Triggered if the string is not valid JSON.
- Data: The resulting Dictionary or List.

### String Uppercase

**Version**: 2.0.2
**Description**: Converts all characters in a text string to uppercase.

Inputs:
- Flow: Trigger the conversion.
- Value: The source text string.

Outputs:
- Flow: Triggered after conversion.
- Result: The uppercase version of the string.

### Substring

**Version**: 2.0.2
**Description**: Extracts a portion of a string based on start and end indices.

Inputs:
- Flow: Execution trigger.
- String: The source string.
- Start: The starting index (inclusive).
- End: The ending index (exclusive). If empty, extracts to the end.

Outputs:
- Flow: Triggered after the extraction.
- Result: The extracted portion of the string.

### Subtract

**Version**: 2.0.2
**Description**: Subtracts one value from another. Supports both numeric subtraction 
and date/time offsets (subtracting seconds or days from a timestamp).

Inputs:
- Flow: Trigger the calculation.
- A: The base value (Number or Formatted Datetime).
- B: The value to subtract (Number).

Outputs:
- Flow: Triggered after the difference is calculated.
- Result: The resulting difference or offset date.

### Tan

**Version**: 2.0.2
**Description**: Calculates the tangent of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The tangent of the angle.

### Template Injector

**Version**: 2.0.2
**Description**: Injects values into a string template using placeholders like {name} or {id}.

Inputs:
- Flow: Execution trigger.
- Template: The string template containing {key} placeholders.
- Input Items: A dictionary of key-value pairs to inject into the template.

Outputs:
- Flow: Triggered after the injection is complete.
- Result: The formatted string with placeholders replaced.

---
[Back to Nodes Index](Index.md)
