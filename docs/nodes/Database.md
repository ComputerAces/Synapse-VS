# Database

## Nodes

### SQL Delete

**Version**: 2.0.2
**Description**: Deletes rows from a database table based on specified filters.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to delete from.
- Filters: Dictionary of column values to match for deletion.

Outputs:
- Flow: Triggered after the deletion is complete.
- Affected Rows: The number of rows deleted.

### SQL Execute

**Version**: 2.0.2
**Description**: Executes a non-query SQL command (e.g., CREATE TABLE, DROP) on the database.

Inputs:
- Flow: Execution trigger.
- Command: The SQL statement to execute.

Outputs:
- Flow: Triggered after the command is executed.
- Affected Rows: The number of rows affected by the command.

### SQL Insert

**Version**: 2.0.2
**Description**: Inserts a new record into a database table using a dictionary of data.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to insert into.
- Data: Dictionary of column-value pairs to insert.

Outputs:
- Flow: Triggered after the insertion is complete.
- Affected Rows: The number of rows inserted (typically 1).

### SQL Query

**Version**: 2.0.2
**Description**: Executes a custom SQL query and returns the results as a list of dictionaries.

Inputs:
- Flow: Execution trigger.
- Query: The SQL SELECT statement to execute.

Outputs:
- Flow: Triggered after the query is complete.
- Rows: List of records returned by the query.
- Count: The number of rows returned.

### SQL Select

**Version**: 2.0.2
**Description**: Executes a SELECT query on a database table and returns matching rows.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to select from.
- Filters: Dictionary of column values to filter by (e.g., {"id": 1}).

Outputs:
- Flow: Triggered after data is retrieved.
- Rows: List of matching records as dictionaries.
- Count: The number of rows returned.

### SQL Update

**Version**: 2.0.2
**Description**: Updates existing records in a database table.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to update.
- Data: Dictionary of column-value pairs to set.
- Filters: Dictionary of column values to match for the update.

Outputs:
- Flow: Triggered after the update is complete.
- Affected Rows: The number of rows updated.

---
[Back to Nodes Index](Index.md)
