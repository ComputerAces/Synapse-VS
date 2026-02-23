# 🔢 Enums

Enum nodes provide a set of pre-defined options for configuring other nodes, ensuring consistent data handling across your graphs.

## Nodes

### Write Mode

**Version**: 2.0.2

**Description**: Selects the file writing behavior (Overwrite or Append).
**Suggested Use**:

- **Overwrite**: Replaces the entire content of a file with new data.
- **Append**: Adds new data to the end of an existing file.
- **Outputs**:
  - `Value`: The selected write mode string (`Overwrite` or `Append`).
  - **Type**: `DataType.WRITEMODE` (LimeGreen).

---
[Back to Nodes Index](Index.md)
