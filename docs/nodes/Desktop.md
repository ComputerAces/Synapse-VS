# 🖥️ Desktop Automation

Nodes for automating user interaction, capturing the screen, and managing application windows.

## Nodes

### Automation Provider

**Version**: 2.0.2
**Description**: Establishes an automation context for managing screens, windows, and input devices.
Acts as a scope provider for mouse, keyboard, and screen capture operations.

Inputs:
- Flow: Trigger to enter the automation scope.
- Target Title: Optional window title to target for automation.
- Monitor: The numeric index of the monitor to capture (default: 1).

Outputs:
- Done: Triggered upon exiting the automation scope.
- Provider Flow: Active while inside the automation context.
- Provider: A handle containing target window and monitor configuration.

### Clipboard Read

**Version**: 2.0.2
**Description**: Retrieves the current text or image content from the system clipboard.

Inputs:
- Flow: Trigger the clipboard read.

Outputs:
- Flow: Triggered after reading.
- Text: The text content of the clipboard (if available).
- Image: The image content of the clipboard (if available).

### Clipboard Write

**Version**: 2.0.2
**Description**: Sets the system clipboard to the provided text or image data.

Inputs:
- Flow: Trigger the clipboard write.
- Text: The text string to place on the clipboard.
- Image Data: image data to place on the clipboard.

Outputs:
- Flow: Triggered after writing.

### Color Checker

**Version**: 2.0.2
**Description**: Samples the color of a specific pixel on the screen.
Returns the color as both a list of RGB components and a standard hex string.

Inputs:
- Flow: Trigger the color check.
- X, Y: Coordinates of the pixel to sample.

Outputs:
- Flow: Triggered after the check.
- Color: The actual sampled color as an RGB list [R, G, B].
- Hex: The actual sampled color as a hex string (e.g., "#FFFFFF").

### Mouse Action

**Version**: 2.0.2
**Description**: Simulates mouse movements, clicks, and scrolls.

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

### Process Discovery

**Version**: 2.0.2
**Description**: Scans running system processes and filters them by name.
Provides detailed information like PID, name, and owner.

Inputs:
- Flow: Trigger the discovery process.
- Filter Name: Case-insensitive string to filter process names.

Outputs:
- Flow: Triggered after the scan is complete.
- Processes: A list of objects containing process details (ID, Name, CPU, Memory).
- Count: Number of matching processes found.

### Screen Capture

**Version**: 2.0.2
**Description**: Captures a screenshot of a specific window or a region of a monitor.
Uses the active Automation Provider context if available.

Inputs:
- Flow: Trigger the capture.
- Region: List/String defining the area [Left, Top, Width, Height].
- Window Handle: Optional numeric HWND of a window to capture.

Outputs:
- Flow: Triggered after the capture is complete.
- Image: The resulting image data (PIL Image or path).

### Send Keys

**Version**: 2.0.2
**Description**: Simulates keyboard input, supporting text blocks and special key combinations.
Works relative to the currently focused window or the active provider target.

Inputs:
- Flow: Trigger the keyboard input.
- Text: The string of characters to type.
- Keys: Special keys to press (e.g., 'ENTER', 'TAB', 'CTRL+V').
- Delay: The delay (in ms) between individual keystrokes.

Outputs:
- Flow: Triggered after the keys are sent.

### Window Manager

**Version**: 2.0.2
**Description**: Provides tools for finding and interacting with window handles.
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

### Window State

**Version**: 2.0.2
**Description**: Modifies or retrieves the state of a window (Maximize, Minimize, Restore, Hide).
Allows direct programmatic control over window visibility and layering.

Inputs:
- Flow: Trigger the state change.
- Window Handle: Numeric HWND handle of the target window.
- Action: The desired window action (Bring to Front, Minimize, Maximize, etc.).

Outputs:
- Flow: Triggered after the state update is attempted.

---
[Back to Nodes Index](Index.md)
