# 🧩 Enums Nodes

This document covers nodes within the **Enums** core category.

## 📂 General

### Compare Type

**Version**: `2.1.0`

Provides a selectable comparison operator (e.g., ==, !=, >, <) as a pulse-triggered output.
Essential for configuring conditional logic in nodes that require a comparison operator.

Inputs:
- Flow: Trigger the output of the selected comparison type.
- Value: Optionally set the comparison operator via a logic pulse.

Outputs:
- Flow: Pulse triggered after the value is processed.
- Result: The selected comparison operator string.

---

### Random Type

**Version**: `2.1.0`

Standardizes the selection of random generation algorithms.

Provides a consistent label for common random types like 'Number' (float), 
'Integer', or 'Unique ID' (UUID). This node is typically linked to a 
'Random' node to define its behavior.

Inputs:
- Value: The random type selection (Number, Integer, UID).

Outputs:
- Result: The selected type string.

---

### Write Mode

**Version**: `2.1.0`

Standardizes file writing behaviors such as 'Overwrite' or 'Append'.

This node provides a UI dropdown for selecting how file operations should 
interact with existing files. 'Overwrite' replaces the entire file content, 
while 'Append' adds new data to the end of the file.

Inputs:
- Value: The selected write mode (Overwrite/Append).
- Value Options: The list of toggleable modes.
- Header Color: The UI accent color for this node.

Outputs:
- Result: The selected mode string (compatible with Write nodes).

---

[Back to Node Index](Index.md)
