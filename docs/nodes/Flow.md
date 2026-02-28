# 🧩 Flow Nodes

This document covers nodes within the **Flow** core category.

## 📂 Control

### Switch

**Version**: `2.1.0`

Directs execution flow based on a match between an input value and one of several named output ports.

This node functions like if-elif-else or switch-case statements in programming. 
It compares the 'Value' against the names of all custom output ports (cases). 
Matching is string-based and case-insensitive. If no match is found, the 'Default' port is triggered.

Inputs:
- Flow: Execution trigger.
- Value: The data item to evaluate.

Outputs:
- Default: Pulse triggered if no matching case is found.
- [Dynamic Cases]: Custom ports where the port name defines the matching value.

---

## 📂 Debug

### Breakpoint

**Version**: `2.1.0`

Temporarily pauses graph execution at this point, allowing manual inspection of state.
Execution can be resumed by the user through the UI or by deleting the pause signal file.
Skipped automatically in Headless mode.

Inputs:
- Flow: Trigger execution to pause here.

Outputs:
- Flow: Triggered immediately (Engine handles the pause step contextually).

---

### Debug Node

**Version**: `2.1.0`

Logs input data to the console for debugging purposes.

Inputs:
- Flow: Execution trigger.
- Data: The information to be logged.

Outputs:
- Flow: Triggered after logging.

---

## 📂 Error Handling

### End Try Node

**Version**: `2.1.0`

Closes an error-handling (Try/Catch) scope.

This node serves as a marker for the Execution Engine to pop the current 
error-handling context and continue normal flow. It ensures that subsequent 
errors are handled by the next level up in the hierarchy.

Inputs:
- Flow: Execution trigger from the Try or Catch block.

Outputs:
- Flow: Pulse triggered after the scope is safely closed.

---

### Last Error Node

**Version**: `2.1.0`

Retrieves information about the most recent error caught by the engine.

This node is typically used within a Catch block or immediately after a 
failure to inspect error details such as the message, node ID, and trace.

Inputs:
- Flow: Trigger the retrieval.

Outputs:
- Flow: Pulse triggered after retrieval.
- Error Object: An Error object containing Message, Node ID, and context.

---

### Raise Error

**Version**: `2.1.0`

Artificially triggers an error to halt execution or test Error Handling.

When flow reaches this node, it forces a Python exception with the 
specified message, which will be caught by any active Try/Catch blocks.

Inputs:
- Flow: Trigger the error.
- Message: The custom error message to report.

Outputs:
- Flow: Pulse triggered on success (rarely reached due to error).
- Error: Pulse triggered if the engine supports non-halting errors.

---

## 📂 General

### Exit For

**Version**: `2.1.0`

Terminates an active loop (For or Foreach) early.

Acts as a 'break' statement. When triggered, it signals the parent loop 
node to stop iterating and transition to its completion 'Flow' output.

Inputs:
- Flow: Trigger the break signal.

Outputs:
- Flow: Pulse triggered after the signal is sent.

---

### Exit While

**Version**: `2.1.0`

Terminates an active While loop early.

Acts as a 'break' statement. When triggered, it signals the 'While Loop' 
node to stop iterating and transition to its completion 'Flow' output.

Inputs:
- Flow: Trigger the break signal.

Outputs:
- Flow: Pulse triggered after the signal is sent.

---

## 📂 SubGraph

### SubGraph Node

**Version**: `2.1.0`

Executes a nested graph (subgraph) as a single node within the current context.

This node allows for hierarchical graph design and logic reuse. It dynamically 
generates input and output ports based on the 'Start' and 'Return' nodes found 
within the child graph file.

Inputs:
- Flow: Trigger execution of the subgraph.
- GraphPath: Path to the .syp graph file to load.
- [Dynamic Inputs]: Data variables passed into the subgraph's Start node.

Outputs:
- Flow: Pulse triggered when the subgraph reaches a Return node.
- Error Flow: Pulse triggered if the subgraph fails to load or execute.
- [Dynamic Outputs]: Data variables returned from the subgraph's Return node.

---

## 📂 Triggers

### Event Trigger

**Version**: `2.1.0`

Standardized service for listening to global system events.
Supports Keyboard Hotkeys, Time Intervals (Timers), and scheduled Date/Time events.
Must be 'Armed' to start listening and 'Disarmed' to stop.

Inputs:
- Arm: Start the background listener.
- Disarm: Stop the background listener.
- Value: The trigger configuration (Hotkey string, time interval, or ISO date).
- Trigger Type: The mode of detection (Keyboard, Timer, Date, Time).

Outputs:
- Flow: Triggered when armed/disarmed.
- Trigger: Pulse fired when the event occurs.
- Stop: Pulse fired when disarmed.

---

### Exit Trigger

**Version**: `2.1.0`

Deactivates a persistent signal (Tag) set by a 'Trigger' node.

When flow reaches this node, the state associated with the specified 'Tag' 
is set to False. This can be used to stop execution branches or reset latches.

Inputs:
- Flow: Trigger the deactivation signal.
- Tag: The unique identifier of the trigger to deactivate.

Outputs:
- Flow: Pulse triggered after the signal is dispatched.

---

### Service Exit Trigger

**Version**: `2.1.0`

Utility node to remotely deactivate an Event Trigger service.
Targeting is done via 'Trigger ID', or all triggers if ID is empty.

Inputs:
- Flow: Execution trigger.
- Trigger ID: The ID of the specific target trigger node (optional).

Outputs:
- Flow: Triggered after the signal is sent.

---

### Trigger

**Version**: `2.1.0`

Sets a persistent signal (Tag) that can be checked or used to release other branches.

This node acts like a digital latch. When triggered via 'Flow', it sets the state 
associated with 'Tag' to True. This state remains until manually deactivated via 
the 'Stop' input or an 'Exit Trigger' node.

Inputs:
- Flow: Set the trigger state to True.
- Stop: Deactivate the trigger (Set state to False).
- Tag: Unique identifier for this trigger state.

Outputs:
- Flow: Pulse triggered after activation.

---

## 📂 Wait

### Throttle

**Version**: `2.1.0`

Delays execution of the flow to prevent rapid repeated triggers.

Similar to a wait, but specifically used to 'throttle' processes that 
might otherwise run too fast or too often. It accepts a delay in milliseconds.

Inputs:
- Flow: execution trigger.
- Delay MS: Duration of the delay in milliseconds.

Outputs:
- Flow: Triggered after the delay is complete.

---

### Wait

**Version**: `2.1.0`

Suspends the execution of the current branch for a specified duration.

This node is non-blocking to other parallel branches. It returns a signal 
tells the Execution Engine to resume this specific branch after the 
'Milliseconds' have elapsed.

Inputs:
- Flow: Trigger to begin the waiting period.
- Milliseconds: The duration to wait (1000ms = 1 second).

Outputs:
- Flow: Pulse triggered after the timer expires.

---

### Yield

**Version**: `2.1.0`

Pauses execution of the 'Flow' branch until a separate 'Trigger' pulse is received.

This is useful for synchronization between asynchronous branches. If the 'Trigger' 
arrives before the 'Flow' reaches this node, the pulse will pass through 
instantly when it arrives.

Inputs:
- Flow: The primary execution branch to be paused.
- Trigger: The signal required to release the paused 'Flow'.

Outputs:
- Flow: The original 'Flow' pulse, released once 'Trigger' is received.

---

[Back to Node Index](Index.md)
