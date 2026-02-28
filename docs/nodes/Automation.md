# 🧩 Automation Nodes

This document covers nodes within the **Automation** core category.

## 📂 Windows

### Event Log Watcher

**Version**: `2.1.0`

Reads recent entries from Windows Event Logs (System, Application, Security).
Allows monitoring system events and security logs for specific patterns.

Inputs:
- Flow: Trigger the log reading operation.
- Log Type: The log category to read ('System', 'Application', or 'Security').
- Limit: The maximum number of recent events to retrieve.

Outputs:
- Flow: Triggered after logs are retrieved.
- Logs: A list of event dictionaries containing time, source, ID, and message.

---

### Service Controller

**Version**: `2.1.0`

Manages Windows Services (Start, Stop, Restart).
Requires administrative privileges for most operations.

Inputs:
- Flow: Trigger execution.
- Service Name: The technical name of the service (e.g., 'Spooler').
- Action: The operation to perform ('Start', 'Stop', or 'Restart').

Outputs:
- Flow: Standard follow-up trigger.
- Success: Triggered if the service operation completed successfully.
- Failure: Triggered if the operation failed (e.g., service not found, access denied).
- Previous Status: The status of the service before the action was taken.

---

### Window Information

**Version**: `2.1.0`

Retrieves detailed properties for a specific window given its handle.
Includes title, dimensions, position, class name, and visibility status.

Inputs:
- Flow: Trigger the information retrieval.
- Handle: The numeric handle (HWND) of the target window.

Outputs:
- Flow: Triggered after information is gathered.
- Title: The window's title text.
- X, Y: Coordinates of the window's top-left corner.
- Width, Height: Dimensions of the window.
- Class Name: The internal Windows class name for the window.
- Is Visible: True if the window is currently visible.

---

### Window List

**Version**: `2.1.0`

Retrieves a list of all visible window titles and handles for a specific process.
Useful for identifying target windows for automation.

Inputs:
- Flow: Trigger the window enumeration.
- Process ID: The numeric ID of the process to inspect.

Outputs:
- Flow: Triggered after listing is complete.
- Titles: List of window titles found.
- Handles: List of numeric window handles (HWND) found.

---

[Back to Node Index](Index.md)
