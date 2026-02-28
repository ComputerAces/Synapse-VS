# 🧩 Logic Nodes

This document covers nodes within the **Logic** core category.

## 📂 Control Flow

### Barrier

**Version**: `2.1.0`

A synchronization point that waits for multiple parallel execution paths to arrive before proceeding.
Useful for merging branches of a graph that were split for parallel processing.

Inputs:
- Flow: Primary trigger.
- Flow 1, 2, ...: Additional synchronization inputs (can be added dynamically).
- Timeout: Maximum time (in seconds) to wait for all flows. 0 = wait forever.

Outputs:
- Flow: Triggered once all wired inputs have arrived or the timeout is reached.

---

### Batch Iterator

**Version**: `2.1.0`

Iterates through files in a directory that match a specific pattern.
Supports recursive searching and provides loop control through 'Loop' and 'Exit' inputs.

Inputs:
- Flow: Initial trigger to start the iteration.
- Loop: Trigger for the next iteration step.
- Exit: Trigger to immediately stop the iteration.
- Path: The directory path to scan for files.
- Pattern: Glob pattern for matching files (e.g., '*.txt').
- Recursive: If True, searches subdirectories.

Outputs:
- Flow: Triggered once the iteration is complete or exited.
- Loop Flow: Triggered for each matching file found.
- File Path: The full path of the current file.
- File Name: The name of the current file.
- Index: The current iteration index (starts at 0).
- Count: Total number of files matched.

---

### End Node

**Version**: `2.1.0`

Terminates the execution of the current branch.

When flow reaches this node, the execution engine stops processing further nodes 
in this specific sequence. It is used to mark the logical conclusion of a 
workflow where no further output pulse is desired.

Inputs:
- Flow: Execution trigger.

Outputs:
- None: This node is a terminator and has no outputs.

---

### Exit Batch

**Version**: `2.1.0`

Immediately terminates an active Batch Iterator loop.

This node acts like a 'break' statement. When triggered, it signals the 
parent Batch Iterator to stop processing the current batch and transition 
to its final 'Flow' output.

Inputs:
- Flow: Trigger the early exit.

Outputs:
- Flow: Pulse triggered after signaling the break.

---

### For Node

**Version**: `2.1.0`

Executes a block of code a specific number of times based on a numeric range.

Inputs:
- Flow: Initialize the loop and start the first iteration.
- Continue: Trigger the next iteration of the loop.
- Break: Immediately terminate the loop.
- Start: The numeric value to begin counting from.
- Step: The amount to increment/decrement per iteration.
- Stop: The target value to compare the index against.
- CompareType: The operator used to check the stop condition (e.g., <, <=, ==).

Outputs:
- Flow: Pulse triggered once the loop completes or breaks.
- Body: Pulse triggered for each iteration while the condition is true.
- Index: The current numeric value of the counter.

---

### ForEach Node

**Version**: `2.1.0`

Iterates through a list of items, executing the 'Body' output for each element.

Inputs:
- Flow: Start the iteration from the first item.
- Continue: Move to the next item in the list.
- Break: Terminate the loop immediately.
- End: Terminate the iteration and kill all active parallel branches.
- List: The collection of items to iterate over.

Outputs:
- Flow: Triggered when the entire list has been processed or the loop is broken.
- Body: Triggered for each individual item in the list.
- Item: The current value from the list.
- Index: The zero-based position of the current item.

---

### Parallel Runner

**Version**: `2.1.0`

Executes a subgraph in parallel across multiple worker processes.

Takes a list of 'Items' and a '.syp' graph file, spinning up 
a process pool to execute the graph for each item. Results are 
aggregated into a single list once all workers complete.

Inputs:
- Flow: Trigger the parallel batch.
- Items: The list of data points to process.
- Graph: Path to the .syp subgraph file.
- Threads: Maximum number of parallel workers.

Outputs:
- Flow: Triggered if all workers complete successfully.
- Error Flow: Triggered if any worker fails or a crash occurs.
- Results: List of return values from each execution.
- Errors: List of error details for failing items.

---

### Reset Barrier

**Version**: `2.1.0`

Resets a 'Barrier' node's internal synchronization counters.

Forcibly clears the progress of a specific Barrier, allowing it to 
re-synchronize from zero. Useful for looping or complex branches 
that re-enter the same Barrier multiple times.

Inputs:
- Flow: Trigger the reset.
- Barrier ID: The unique node ID of the Barrier to reset.

Outputs:
- Flow: Triggered after the reset.

---

### Return Node

**Version**: `2.1.0`

The exit point for a graph or subgraph execution.

Sends results back to the caller (e.g., a 'Run Graph' or 'SubGraph' node). 
It consumes all incoming data and bundles it into the return payload.

Inputs:
- Flow: Trigger the return.

Outputs:
- None (Terminator node).

---

### Start Node

**Version**: `2.1.0`

The entry point for a graph or subgraph execution.

Initiates the flow and optionally injects global variables or provider 
contexts into the runtime. It acts as the primary data producer for 
the starting branch.

Inputs:
- None (Initiator node).

Outputs:
- Flow: The primary execution pulse.
- Error Flow: Pulse triggered if context initialization fails.

---

### Try Node

**Version**: `2.1.0`

Initiates a protected execution block (Exception Handler).

Wraps downstream flow in a try-catch pattern. If any node in the 
'Flow' branch encounters an error, the engine will intercept it 
and pulse the 'Catch' port of this node.

Inputs:
- Flow: Trigger the protected branch.

Outputs:
- Flow: The primary pulse to protect.
- Catch: Pulse triggered only on execution failure.
- FailedNode: Name or ID of the node that threw the error.
- ErrorCode: Error message or status code.

---

### While Node

**Version**: `2.1.0`

Repeatedly executes a block of code as long as a boolean condition remains true.

Inputs:
- Flow: Start the while loop evaluation.
- Continue: Trigger the next check of the loop.
- Break: Immediately terminate the loop.
- End: Terminate the loop and kill all active parallel branches.
- Condition: A boolean value determining if the loop should continue.

Outputs:
- Flow: Pulse triggered after the loop finishes.
- Body: Pulse triggered for each iteration while the condition is met.
- Index: The current iteration count (0-based).

---

## 📂 Fuzzy

### Fuzzy Search

**Version**: `2.1.0`

Performs fuzzy string matching and automated spell correction.

This node compares 'Raw Text' against 'Target' (string or list) using fuzzy 
logic. If the initial match is below 'Threshold', it attempts spell 
correction and re-scores. It routes the flow to 'Ambiguous' if no 
satisfactory match is found.

Inputs:
- Flow: Trigger the search.
- Raw Text: The string to be analyzed.
- Target: The reference string or list of candidates to match against.
- Threshold: Minimum score (0-100) to consider a match successful.

Outputs:
- Flow: Triggered if a match exceeds the threshold.
- Ambiguous: Triggered if match score is below the threshold.
- Best Text: The result (either original or spell-corrected).
- Confidence: Per-word match scores.
- Score: Overall fuzzy similarity score.
- Corrected: Boolean indicating if spell correction was applied and improved the score.

---

## 📂 General

### Boolean Type

**Version**: `2.1.0`

A constant boolean node that outputs a fixed True or False value.
Useful for setting toggles or flags within a graph.

Inputs:
- Flow: Triggered upon execution.
- Value: The constant boolean value to output.

Outputs:
- Flow: Triggered upon execution.
- Result: The constant boolean value.

---

### Compare

**Version**: `2.1.0`

Performs a comparison between two values (A and B) using a specified operator.
Supports numbers, strings, and formatted datetime strings.

Inputs:
- Flow: Trigger the comparison.
- Compare Type: The operator to use (==, !=, >, <, >=, <=).
- A: The first value.
- B: The second value.

Outputs:
- True: Triggered if the condition is met.
- False: Triggered if the condition is not met.
- Result: Numeric 1 (True) or 0 (False).
- Compare Result: Boolean result.

---

### Receiver

**Version**: `2.1.0`

Listens for data broadcasted across the graph using a specific 'Tag'.

Acts as a wireless receiver for values sent by 'Sender' nodes. When 
triggered, it retrieves the payload associated with the 'Tag' from 
the engine's global memory.

Inputs:
- Flow: Trigger the retrieval.
- Tag: The unique identifier for the communication channel.

Outputs:
- Flow: Triggered after data is retrieved.
- Data: The primary payload (if single value) or the full dictionary.

---

### Run Split

**Version**: `2.1.0`

Splits flow based on whether a value is populated or 'Null'.

Checks the 'Value' input. If it is non-empty and valid, the 'Valid' 
port is pulsed. If it is None, empty, or "none", the 'Null' 
port is pulsed.

Inputs:
- Flow: Trigger the check.
- Value: The data to validate.

Outputs:
- Valid: Pulse triggered if value is valid.
- Null: Pulse triggered if value is empty/null.

---

### Sender

**Version**: `2.1.0`

Broadcasts data across the graph using a specific 'Tag'.

Acts as a wireless transmitter. Data sent to this node can be 
retrieved by 'Receiver' nodes using the same 'Tag'. Supports 
dynamic inputs which are bundled into the broadcast payload.

Inputs:
- Flow: Trigger the broadcast.
- Tag: The unique identifier for the communication channel.
- Data: The primary payload to send.

Outputs:
- None (Ends execution branch or sinks pulse).

---

### Service Return

**Version**: `2.1.0`

Signals the end of a service or subgraph execution phase.

Used within service graphs to return control and data back to 
the parent graph. It packages all non-flow inputs into a 
return payload.

Inputs:
- Flow: Trigger the return.

Outputs:
- None (Terminator node).

---

## 📂 Scripting

### Python Script

**Version**: `2.1.0`

Executes a Python script either synchronously or as a background service.

Allows for custom logic extension using the bridge API. Scripts can 
be loaded from a file or written directly in the node. Supports 
dynamic inputs and outputs, and automatic dependency installation 
via 'Requirements'.

Inputs:
- Flow: Trigger the script.
- Env: Optional path to a Python executable or virtual environment.
- Script Path: Path to a .py file to execute.
- Script Body: Inline Python code to execute.
- Requirements: New-line separated list of pip packages to ensure.
- Use Current Env: Whether to use the system environment if no 'Env' is provided.

Outputs:
- Flow: Pulse triggered immediately (Service) or after completion (Sync).
- Finished Flow: Pulse triggered after the script finishes execution.
- Error Flow: Pulse triggered if the script crashes or fails to start.
- Std Out: Pulse triggered for each printed line from the script.
- Text Out: The string content of the printed line.

---

[Back to Node Index](Index.md)
