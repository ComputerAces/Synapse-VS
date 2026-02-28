# 🧩 Workflow Nodes

This document covers nodes within the **Workflow** core category.

## 📂 General

### Project Var Get

**Version**: `2.1.0`

Retrieves a global project variable from the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the retrieval.
- Name: The name of the project variable to get.

Outputs:
- Flow: Pulse triggered after retrieval.
- Value: The current value of the project variable.

---

### Project Var Set

**Version**: `2.1.0`

Sets a global project variable in the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the update.
- Name: The name of the project variable to set.
- Value: The new value to assign to the variable.

Outputs:
- Flow: Pulse triggered after the variable is updated.

---

[Back to Node Index](Index.md)
