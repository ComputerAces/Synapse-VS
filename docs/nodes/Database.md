# 🧩 Database Nodes

This document covers nodes within the **Database** core category.

## 📂 General

### SQL Delete

**Version**: `2.1.0`

Deletes rows from a database table based on specified filters.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to delete from.
- Filters: Dictionary of column values to match for deletion.

Outputs:
- Flow: Triggered after the deletion is complete.
- Affected Rows: The number of rows deleted.

---

### SQL Execute

**Version**: `2.1.0`

Executes a non-query SQL command (e.g., CREATE TABLE, DROP) on the database.

Inputs:
- Flow: Execution trigger.
- Command: The SQL statement to execute.

Outputs:
- Flow: Triggered after the command is executed.
- Affected Rows: The number of rows affected by the command.

---

### SQL Insert

**Version**: `2.1.0`

Inserts a new record into a database table using a dictionary of data.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to insert into.
- Data: Dictionary of column-value pairs to insert.

Outputs:
- Flow: Triggered after the insertion is complete.
- Affected Rows: The number of rows inserted (typically 1).

---

### SQL Query

**Version**: `2.1.0`

Executes a custom SQL query and returns the results as a list of dictionaries.

Inputs:
- Flow: Execution trigger.
- Query: The SQL SELECT statement to execute.

Outputs:
- Flow: Triggered after the query is complete.
- Rows: List of records returned by the query.
- Count: The number of rows returned.

---

### SQL Select

**Version**: `2.1.0`

Executes a SELECT query on a database table and returns matching rows.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to select from.
- Filters: Dictionary of column values to filter by (e.g., {"id": 1}).

Outputs:
- Flow: Triggered after data is retrieved.
- Rows: List of matching records as dictionaries.
- Count: The number of rows returned.

---

### SQL Update

**Version**: `2.1.0`

Updates existing records in a database table.

Inputs:
- Flow: Execution trigger.
- Table: Name of the table to update.
- Data: Dictionary of column-value pairs to set.
- Filters: Dictionary of column values to match for the update.

Outputs:
- Flow: Triggered after the update is complete.
- Affected Rows: The number of rows updated.

---

## 📂 Providers

### CSV Data Provider

**Version**: `2.1.0`

Exposes a directory of CSV files as a simple database.
Allows other nodes to read from or write to CSV files within the specified folder.

Inputs:
- Flow: Trigger to enter the data provider scope.
- Folder Path: The directory where CSV files are stored.

Outputs:
- Done: Triggered upon exiting the provider scope.
- Provider Flow: Active while inside the CSV data context.

---

### JSON Data Provider

**Version**: `2.1.0`

Provides a mock database connection backed by a local JSON file.

Inputs:
- Flow: Execution trigger.
- File Path: Path to the JSON database file.

Outputs:
- Flow: Triggered when the provider is initialized.

---

### Memory Data Provider

**Version**: `2.1.0`

Provides a temporary in-memory SQL database connection.

Inputs:
- Flow: Execution trigger.

Outputs:
- Flow: Triggered when the provider is initialized.

---

### MySQL Provider

**Version**: `2.1.0`

Provides a connection to a MySQL database server.

Inputs:
- Flow: Execution trigger.
- Host: Server hostname or IP address.
- User: Username for authentication.
- Password: Password for authentication.
- Database: Name of the database to connect to.
- Port: Connection port (default 3306).

Outputs:
- Flow: Triggered when the provider is initialized.

---

### ODBC Provider

**Version**: `2.1.0`

Provides a connection to a database via ODBC connection string.

Inputs:
- Flow: Execution trigger.
- Connection String: The standard ODBC connection string.

Outputs:
- Flow: Triggered when the provider is initialized.

---

### SQLite Provider

**Version**: `2.1.0`

Provides a connection to a local SQLite database file.

Inputs:
- Flow: Execution trigger.
- Filename: The path to the SQLite database file.

Outputs:
- Flow: Triggered when the provider is initialized.

---

## 📂 Redis

### Redis Delete

**Version**: `2.1.0`

Removes a key and its value from Redis.

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to delete.

Outputs:
- Flow: Triggered after deletion.
- Success: True if the deletion command was sent successfully.

---

### Redis Get

**Version**: `2.1.0`

Retrieves a value from Redis by its key.

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to fetch.

Outputs:
- Flow: Triggered after the retrieval.
- Value: The data fetched from Redis.
- Found: True if the key exists.

---

### Redis Keys

**Version**: `2.1.0`

Retrieves a list of keys matching a specified pattern.

Inputs:
- Flow: Execution trigger.
- Pattern: Glob-style pattern (e.g., "user:*").

Outputs:
- Flow: Triggered after keys are listed.
- Keys: List of matching key names.

---

### Redis Provider

**Version**: `2.1.0`

Provides a connection to a Redis server for key-value storage and pub/sub.

Inputs:
- Flow: Execution trigger.
- Host: Redis server hostname or IP.
- Port: Redis server port (default 6379).
- Password: Authentication password.
- DB: Database index (default 0).

Outputs:
- Flow: Triggered when the provider is initialized.
- Connected: True if connection was successful.

---

### Redis Publish

**Version**: `2.1.0`

Publishes a message to a Redis channel.

Inputs:
- Flow: Execution trigger.
- Channel: The channel name.
- Message: The string message to publish.

Outputs:
- Flow: Triggered after publishing.
- Subscribers: Number of clients that received the message.

---

### Redis Set

**Version**: `2.1.0`

Stores a value in Redis with an optional time-to-live (TTL).

Inputs:
- Flow: Execution trigger.
- Key: The name of the key to set.
- Value: The data to store.
- TTL: Time to live in seconds (optional).

Outputs:
- Flow: Triggered after the set is successful.
- Success: True if the operation succeeded.

---

### Redis Subscribe

**Version**: `2.1.0`

Subscribes to a Redis channel and triggers Flow for each received message.

Inputs:
- Flow: Execution trigger.
- Channel: The channel name to watch.

Outputs:
- Flow: Triggered for every new message.
- Message: The content of the received message.
- Channel: The channel where the message originated.

---

[Back to Node Index](Index.md)
