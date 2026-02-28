# 🧩 System Nodes

This document covers nodes within the **System** core category.

## 📂 Automation

### Automation Provider

**Version**: `2.1.0`

Establishes an automation context for managing screens, windows, and input devices.
Acts as a scope provider for mouse, keyboard, and screen capture operations.

Inputs:
- Flow: Trigger to enter the automation scope.
- Target Title: Optional window title to target for automation.
- Monitor: The numeric index of the monitor to capture (default: 1).

Outputs:
- Done: Triggered upon exiting the automation scope.
- Provider Flow: Active while inside the automation context.
- Provider: A handle containing target window and monitor configuration.

---

### Clipboard Read

**Version**: `2.1.0`

Retrieves the current text or image content from the system clipboard.

Inputs:
- Flow: Trigger the clipboard read.

Outputs:
- Flow: Triggered after reading.
- Text: The text content of the clipboard (if available).
- Image: The image content of the clipboard (if available).

---

### Clipboard Write

**Version**: `2.1.0`

Sets the system clipboard to the provided text or image data.

Inputs:
- Flow: Trigger the clipboard write.
- Text: The text string to place on the clipboard.
- Image Data: image data to place on the clipboard.

Outputs:
- Flow: Triggered after writing.

---

### Color Checker

**Version**: `2.1.0`

Samples the color of a specific pixel on the screen.
Returns the color as both a list of RGB components and a standard hex string.

Inputs:
- Flow: Trigger the color check.
- X, Y: Coordinates of the pixel to sample.

Outputs:
- Flow: Triggered after the check.
- Color: The actual sampled color as an RGB list [R, G, B].
- Hex: The actual sampled color as a hex string (e.g., "#FFFFFF").

---

### Mouse Action

**Version**: `2.1.0`

Simulates mouse movements, clicks, and scrolls.

Supports absolute coordinates or relative offsets. Can target specific 
buttons and perform double-clicks.

Inputs:
- Flow: Trigger the mouse action.
- Action: The operation to perform ('Move', 'Click', 'Scroll', etc.).
- X, Y: Target coordinates for the action.
- Button: Which mouse button to use ('left', 'right', 'middle').
- Double Click: Whether to perform a double-click (default False).

Outputs:
- Flow: Pulse triggered after the mouse action is performed.

---

### Process Discovery

**Version**: `2.1.0`

Scans running system processes and filters them by name.
Provides detailed information like PID, name, and owner.

Inputs:
- Flow: Trigger the discovery process.
- Filter Name: Case-insensitive string to filter process names.

Outputs:
- Flow: Triggered after the scan is complete.
- Processes: A list of objects containing process details (ID, Name, CPU, Memory).
- Count: Number of matching processes found.

---

### Screen Capture

**Version**: `2.1.0`

Captures a screenshot of a specific window or a region of a monitor.
Uses the active Automation Provider context if available.

Inputs:
- Flow: Trigger the capture.
- Region: List/String defining the area [Left, Top, Width, Height].
- Window Handle: Optional numeric HWND of a window to capture.

Outputs:
- Flow: Triggered after the capture is complete.
- Image: The resulting image data (PIL Image or path).

---

### Send Keys

**Version**: `2.1.0`

Simulates keyboard input, supporting text blocks and special key combinations.
Works relative to the currently focused window or the active provider target.

Inputs:
- Flow: Trigger the keyboard input.
- Text: The string of characters to type.
- Keys: Special keys to press (e.g., 'ENTER', 'TAB', 'CTRL+V').
- Delay: The delay (in ms) between individual keystrokes.

Outputs:
- Flow: Triggered after the keys are sent.

---

### Window Manager

**Version**: `2.1.0`

Provides tools for finding and interacting with window handles.
Allows focusing, checking existence, or retrieving handles from titles.

Inputs:
- Flow: Trigger the window search.
- Target Title: The window title to search for (supports exact or partial match).

Outputs:
- Flow: Triggered after the search attempt.
- Window Handle: The numeric HWND handle of the found window.
- Process Id: The numeric ID of the process owning the window.
- Bounds: List defining [Left, Top, Width, Height].
- Title: The actual title of the found window.
- Found: True if a matching window was located.

---

### Window State

**Version**: `2.1.0`

Modifies or retrieves the state of a window (Maximize, Minimize, Restore, Hide).
Allows direct programmatic control over window visibility and layering.

Inputs:
- Flow: Trigger the state change.
- Window Handle: Numeric HWND handle of the target window.
- Action: The desired window action (Bring to Front, Minimize, Maximize, etc.).

Outputs:
- Flow: Triggered after the state update is attempted.

---

## 📂 Debug

### Log

**Version**: `2.1.0`

Appends a formatted message to a log file and the console.

This node facilitates debugging and tracking by writing timestamped 
messages to a file (managed via Logging Provider or self-defined). 
It supports multiple log levels (INFO, WARNING, ERROR).

Inputs:
- Flow: Trigger the logging operation.
- File Path: The destination log file path.
- Message: The text content to record.
- Level: The severity of the log (e.g., INFO, ERROR).

Outputs:
- Flow: Triggered after the message is logged.

---

### Logging Provider

**Version**: `2.1.0`

Registers the primary logging service for the graph session.

Initializes a provider context that allows other 'Log' nodes to 
record messages to a centralized file or stream. It sets up 
rotations and file handles used throughout the execution.

Inputs:
- Flow: Trigger the provider initialization.
- File Path: The target log file for the session.

Outputs:
- Done: Pulse triggered once the service is ready.

---

## 📂 General

### Environment Var

**Version**: `2.1.0`

Manages operating system environment variables (e.g., PATH, HOME).

This node can retrieve (Get), set (Set), or delete (Unset) environment 
variables. Setting a variable makes it available to the current process 
and any child processes spawned by Synapse.

Inputs:
- Flow: Trigger the operation.
- Variable Name: The key of the environment variable.
- Variable Value: The new value to set, or empty to retrieve.

Outputs:
- Flow: Pulse triggered after the operation.
- Value: The current state of the variable after the operation.

---

## 📂 Hardware

### MQTT Client

**Version**: `2.1.0`

Publishes or subscribes to MQTT topics.

Communicates with an MQTT broker registered by an 'MQTT Provider'. 
Supports publishing text payloads to specific topics.

Inputs:
- Flow: Trigger the action.
- Broker: Optional override for the broker address.
- Topic: The target topic to interact with.
- Message: The payload to publish.
- Port: Connection port (if not using provider defaults).
- Action: The operation to perform ('Publish', 'Subscribe').

Outputs:
- Flow: Pulse triggered after action completion.

---

### MQTT Provider

**Version**: `2.1.0`

Registers the MQTT broker connection for the graph session.

Initializes a provider context with broker address and port, allowing 
'MQTT Client' nodes to communicate with the broker without manual 
configuration for each node.

Inputs:
- Flow: Trigger the provider initialization.
- Broker: The MQTT broker hostname or IP address.
- Port: The broker's connection port (default 1883).

Outputs:
- Done: Pulse triggered once the provider settings are registered.

---

### Resource Monitor

**Version**: `2.1.0`

Background service that periodically captures system performance metrics.
Monitors CPU, RAM, and primary drive usage on a fixed interval.

Inputs:
- Flow: Start the monitoring service.

Outputs:
- Tick: Pulse triggered on every monitoring interval update.
- CPU Usage: Current CPU utilization percentage.
- RAM Usage: Current RAM utilization percentage.
- Disk Usage: Current primary drive utilization percentage.

---

### Serial Port

**Version**: `2.1.0`

Sends and receives data over a serial port.
Can discover port settings automatically if nested within a Serial Provider.

Inputs:
- Flow: Trigger the serial transaction.
- Port: The serial port to use (optional if provider is present).
- Message: The string data to send to the device.
- Baud Rate: The communication speed.

Outputs:
- Flow: Pulse triggered after the transaction completes.
- Response: The string data received back from the serial device.

---

### Serial Provider

**Version**: `2.1.0`

Establishes a Serial communication context (COM port/Baud rate).
Registers serial settings in the bridge for downstream Serial Port nodes.

Inputs:
- Flow: Start the Serial provider.
- Port: The hardware port identifier (e.g., 'COM3', '/dev/ttyUSB0').
- Baud Rate: The communication speed (default: 9600).

Outputs:
- Flow: Pulse triggered after the scope successfully closes.
- Provider Flow: Active pulse for nodes within this serial context.
- Provider: A dictionary containing the established port settings.

---

## 📂 Monitor

### Watchdog

**Version**: `2.1.0`

Monitors system resource usage including CPU, RAM, and Disk space.
Provides real-time telemetry about the host operating system.

Inputs:
- Flow: Trigger the resource check.

Outputs:
- Flow: Pulse triggered after data is captured.
- CPU: Total CPU usage percentage (FLOAT).
- RAM: Total RAM usage percentage (FLOAT).
- Drives: List of connected drives and their usage (LIST).
- OS: The name of the host operating system (STRING).

---

## 📂 State

### User Activity

**Version**: `2.4.0`

Outputs mouse and keyboard idle counters from the engine's ActivityTracker.

The engine runs a background thread that increments idle counters every 250ms.
When the mouse moves, its counter resets to 0. When a key is pressed, its 
counter resets to 0. Each counter is independent.

Inputs:
- Flow: Trigger a read of current idle counters.

Outputs:
- Flow: Always triggered after read.
- User Activity: Boolean — True if either counter is 0 (recent activity).
- Mouse Idle Time: Milliseconds since last mouse movement (resets to 0 on move).
- Keyboard Idle Time: Milliseconds since last key press (resets to 0 on press).

---

## 📂 Terminal

### Print

**Version**: `2.1.0`

Outputs a message to the system terminal or console.
Useful for debugging and tracking graph execution flow.

Inputs:
- Flow: Trigger the print operation.
- Message: The string message to display.

Outputs:
- Flow: Pulse triggered after the message is printed.

---

### Shell Command

**Version**: `2.1.0`

Executes shell commands on the host system.
Supports both synchronous execution and long-running service processes with 
standard I/O interaction.

Inputs:
- Flow: Execute the command.
- Command: The shell command string to run.
- EnvPath: Optional path to a virtual environment to activate.
- StdIn: Trigger to send 'TextIn' to the running process (Service mode).
- TextIn: String data to send to stdin.

Outputs:
- Started: Triggered when the process starts (Service mode).
- Finished: Triggered when the process exits.
- StdoutData: The full stdout output (Sync mode).
- StderrData: The full stderr output (Sync mode).
- ExitCode: The process exit return code.
- StdOut: Triggered for each line of stdout (Service mode).
- Flow: General pulse triggered after execution starts/finishes.
- TextOut: The most recent line from stdout/stderr (Service mode).
- EnvResult: The environment path that was actually used.

---

## 📂 Time

### Time

**Version**: `2.1.0`

Captures the current system date and time.
Returns the timestamp in a standardized format inside Synapse tags.

Inputs:
- Flow: Trigger the time capture.

Outputs:
- Flow: Pulse triggered after time is captured.
- Time: The current timestamp string (e.g., #[2024-05-20 12:00:00]#).

---

## 📂 VENV

### VENV Create

**Version**: `2.1.0`

Creates a new Python Virtual Environment at the specified path.
Includes pip by default to allow for immediate package installation.

Inputs:
- Flow: Trigger the creation process.
- Path: The target directory for the new VENV.

Outputs:
- Flow: Pulse triggered after the operation finishes.
- Success: True if the environment was created successfully.

---

### VENV Install

**Version**: `2.1.0`

Installs one or more pip packages into an existing virtual environment.

Inputs:
- Flow: Trigger the installation.
- VENV Path: The path to the target virtual environment.
- Packages: A list or single string of package names to install.

Outputs:
- Flow: Pulse triggered after the installation process completes.

---

### VENV List

**Version**: `2.1.0`

Lists all pip packages currently installed in a specified virtual environment.

Inputs:
- Flow: Trigger the listing process.
- VENV Path: The path to the virtual environment to audit.

Outputs:
- Flow: Pulse triggered after the list is retrieved.
- Packages: A list of installed packages and their versions (pip freeze format).

---

### VENV Provider

**Version**: `2.1.0`

Establishes a Virtual Environment (VENV) context for downstream nodes.
Automatically creates the environment if it does not exist and can 
install a list of required pip packages upon initialization.

Inputs:
- Flow: Start the VENV provider.
- Path: The directory where the VENV should be located (default: ./venv).
- Requirements: A list of pip packages to ensure are installed.

Outputs:
- Flow: Pulse triggered after the scope successfully closes.
- Provider Flow: Active pulse for nodes running within this VENV context.
- VENV Path: The absolute path to the virtual environment directory.

---

### VENV Remove

**Version**: `2.1.0`

Deletes an entire virtual environment directory from the disk.

Inputs:
- Flow: Trigger the removal process.
- VENV Path: The path to the virtual environment to delete.

Outputs:
- Flow: Pulse triggered after the deletion attempt.
- Success: True if the directory was successfully removed.

---

### VENV Run

**Version**: `2.1.0`

Executes a Python command or script within the context of a virtual environment.
Supports running specific modules (via -m) or standalone .py files.

Inputs:
- Flow: Trigger the execution.
- Command: The script path or module name to run.
- Args: A list of command-line arguments to pass.

Outputs:
- Flow: Pulse triggered after the command finishes.
- Output: The stdout resulting from the execution.
- Exit Code: The numerical return code of the process.

---

## 📂 Windows

### Registry Modify

**Version**: `2.1.0`

Interfaces with the Windows Registry to write or delete keys.
Requires administrative permissions for some HKEY_LOCAL_MACHINE operations.

Inputs:
- Flow: Trigger the registry operation.
- Key Path: The full registry path (e.g., HKEY_CURRENT_USER\Software\Synapse).
- Value Name: The name of the registry value to target.
- Value Data: The data to write (used for Write Key action).
- Action: 'Write' or 'Delete' (Default: Write).

Outputs:
- Flow: Pulse triggered after the operation completes.

---

### Registry Read

**Version**: `2.1.0`

Reads values from the Windows Registry.

Inputs:
- Flow: Trigger the registry read.
- Key Path: The full registry path.
- Value Name: The name of the registry value to read.

Outputs:
- Flow: Pulse triggered after retrieval.
- Value: The data retrieved from the registry.

---

[Back to Node Index](Index.md)
