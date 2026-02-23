# 🔄 Flow Control

Flow Control nodes manage the execution path of your graph, including branching, looping, and error handling.

## Nodes

### Start Node

**Version**: 2.0.2

**Description**: The designated entry point for graph execution. Every graph requires exactly one `Start Node`. When run, this node fires first to kick off the automation sequence.
**Suggested Use**:

- **Outputs**:
  - `Flow`: The primary execution path.
  - `Error Flow`: Fires if the graph fails during initialization or a critical startup error occurs.
  - **Dynamic Ports**: Can be configured via `additional_outputs` property to pass injected data (e.g., from parent graphs in SubGraphs).

### Return Node

**Version**: 2.0.2

**Description**: Ends the graph execution.
**Suggested Use**:

- Neatlying finishing a workflow.
- Passing a final result back if the graph is used as a SubGraph.

### Branch (If)

**Description**: Checks a condition (True/False) and splits the flow.
**Suggested Use**:

- Error handling: "If File Exists" -> Read, "Else" -> Create.
- AI Logic: "If Score > 0.8" -> Publish, "Else" -> Rewrite.

### ForEach Loop

**Description**: Iterates over a list of items, running the connected flow for each one.
**Suggested Use**:

- Processing a list of files or email addresses.
- **Tip**: Connect `Body` to your logic and `Completed` to what happens after.

### While Loop

**Description**: Repeats a flow as long as a condition is True.
**Suggested Use**:

- Polling a server until it responds.
- Retrying an operation until it succeeds.

### Try / Catch

**Description**: A safety net. If an error occurs in the `Try` path, the flow jumps to `Catch`.
**Suggested Use**:

- Preventing graph crashes during network or file I/O errors.

### Wait

**Version**: 2.0.2

**Description**: Pauses execution for a specified duration (milliseconds).
**Suggested Use**:

- Rate limiting or pacing API calls.

### Throttle

**Version**: 2.0.2
**Description**: Limits the rate of flow execution by inserting a delay.
**Suggested Use**:

- Preventing API rate limit triggers.

### Barrier

**Version**: 2.0.2

**Description**: Synchronization point. Waits for ALL incoming flow wires before proceeding.
**Suggested Use**:

- Joining multiple parallel paths (e.g., waiting for several Shell commands).

### Reset Barrier

**Version**: 2.0.2
**Description**: Resets a Barrier node's state for reuse in loops.

### Breakpoint

**Version**: 2.0.2

**Description**: Pauses execution for debugging.
**Suggested Use**:

- Debugging complex logic paths in real-time.

---
[Back to Nodes Index](Index.md)
