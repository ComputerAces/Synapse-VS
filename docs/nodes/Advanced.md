# 🚀 Advanced & Integration

Nodes for extending Synapse VS with custom code, managing complex data structures, and cross-platform integration.

## Nodes

### AND

**Version**: 2.0.2
**Description**: Performs a logical AND operation on a set of boolean inputs.
Returns True only if all provided inputs are True.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate (supports dynamic expansion).

Outputs:
- Flow: Triggered after evaluation.
- Result: True if all inputs are True, False otherwise.

### Archive Read

**Version**: 2.1.0
**Description**: Extracts ZIP archives into a targeted destination folder.

Inputs:
- Flow: Trigger the extraction process.
- Archive Path: The absolute path to the .zip archive to extract.
- Destination Folder: The folder path where the contents will be extracted.

Outputs:
- Flow: Triggered after extraction (success or failure).
- Success: Triggered ONLY if the extraction was successful.
- Extracted Path: The absolute path to the folder containing extracted files.

### Archive Write

**Version**: 2.1.0
**Description**: Compresses files or directories into a ZIP archive.

Inputs:
- Flow: Trigger the compression process.
- Source Path: The absolute path of the file or folder to be compressed.
- Archive Path: The absolute path where the resulting ZIP file will be saved.

Outputs:
- Flow: Triggered after compression (success or failure).
- Success: Triggered ONLY if the compression was successful.
- Result Path: The absolute path to the generated ZIP file.

### Barrier

**Version**: 2.0.2
**Description**: A synchronization point that waits for multiple parallel execution paths to arrive before proceeding.
Useful for merging branches of a graph that were split for parallel processing.

Inputs:
- Flow: Primary trigger.
- Flow 1, 2, ...: Additional synchronization inputs (can be added dynamically).
- Timeout: Maximum time (in seconds) to wait for all flows. 0 = wait forever.

Outputs:
- Flow: Triggered once all wired inputs have arrived or the timeout is reached.

### Batch Iterator

**Version**: 2.0.2
**Description**: Iterates through files in a directory that match a specific pattern.
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

### Boolean Flip

**Version**: 2.0.2
**Description**: Inverts the provided boolean value (True becomes False, and vice-versa).

Inputs:
- Flow: Trigger the inversion.
- Value: The boolean value to flip.

Outputs:
- Flow: Triggered after the flip.
- Result: The inverted boolean result.

### Boolean Type

**Version**: 2.0.2
**Description**: A constant boolean node that outputs a fixed True or False value.
Useful for setting toggles or flags within a graph.

Inputs:
- Flow: Triggered upon execution.
- Value: The constant boolean value to output.

Outputs:
- Flow: Triggered upon execution.
- Result: The constant boolean value.

### Breakpoint

**Version**: 2.0.2
**Description**: Temporarily pauses graph execution at this point, allowing manual inspection of state.
Execution can be resumed by the user through the UI or by deleting the pause signal file.
Skipped automatically in Headless mode.

Inputs:
- Flow: Trigger execution to pause here.

Outputs:
- Flow: Triggered immediately (Engine handles the pause step contextually).

### Browser Click

**Version**: 2.0.2
**Description**: Performs a click action on a specific element or coordinate within the browser page.
Requires a valid selector or explicit X/Y coordinates.

Inputs:
- Flow: Trigger the click action.
- Selector: CSS or XPath selector for the target element.
- Use Points: If True, uses X and Y coordinates instead of a selector.
- X, Y: Pixel coordinates for the click (relative to page).

Outputs:
- Flow: Triggered after the click attempt.

### Browser Navigate

**Version**: 2.0.2
**Description**: Directs the active browser page to a specific URL.
Supports configurable wait conditions to ensure the page has loaded.

Inputs:
- Flow: Trigger the navigation.
- URL: The destination web address (e.g., 'https://google.com').
- Wait Until: Condition to wait for ('load', 'domcontentloaded', 'networkidle', or 'commit').
- Timeout: Maximum time (in milliseconds) to wait for navigation.

Outputs:
- Flow: Triggered after navigation is complete or fails.

### Browser Provider

**Version**: 2.0.2
**Description**: Launches and manages a headless or windowed web browser instance (Chromium, Firefox, WebKit).
Establishes a context for all subsequent browser-based actions.

Inputs:
- Flow: Trigger to launch the browser and enter the scope.
- App ID: Optional unique identifier for the browser session.
- Browser Type: The browser engine to use (Chromium, Firefox, WebKit).
- Headless: If True, runs the browser without a visible window.
- Devtools: If True, opens the browser with developer tools enabled.

Outputs:
- Done: Triggered upon closing the browser and exiting the scope.
- Provider Flow: Active while the browser is running.

### Browser Type

**Version**: 2.0.2
**Description**: Inputs text into a specified form field or element.
Uses the Playwright 'fill' method for efficient typing.

Inputs:
- Flow: Trigger the typing action.
- Selector: CSS or XPath selector for the input field.
- Text: The string to be typed into the field.

Outputs:
- Flow: Triggered after the text has been filled.

### Camera Capture

**Version**: 2.0.2
**Description**: Starts a continuous video and/or audio capture session from a camera device.
Provides a "Provider Flow" for downstream nodes to access live frames or perform
actions while the camera is active. Consumes the camera resource until stopped.

Inputs:
- Flow: Start the capture session.
- Provider End: Close the session and stop recording.
- Camera Index: Integer index or hardware name of the camera.
- Record Audio: Whether to capture audio alongside video.
- Use Memory: If True, saves to a temporary file (RAM disk/temp).
- File Name: The base filename for the saved recording.

Outputs:
- Flow: Triggered after the session is successfully closed.
- Video Data: The resulting video file or bytes.
- Provider Flow: Active pulse during the session.
- Provider ID: Used by downstream nodes to identify this capture source.

### Camera Image

**Version**: 2.0.2
**Description**: Retrieves the most recent frame from an active Camera Provider.
This node acts as a consumer, pulling frames published by a capture service.

Inputs:
- Flow: Trigger the frame retrieval.

Outputs:
- Flow: Pulse triggered after the image is retrieved.
- Image: The captured image object.

### Camera Image Capture

**Version**: 2.0.2
**Description**: Captures a single still image from a specified camera.
This node is self-contained and does not require a Camera Provider to be active.
It opens the camera, grabs a frame, and coordinates immediate closure.

Inputs:
- Flow: Trigger the image capture.
- Camera Index: Integer index or hardware name of the camera.

Outputs:
- Flow: Triggered after the capture attempt.
- Image: The captured image object.

### Camera List

**Version**: 2.0.2
**Description**: Scans the system for available camera devices (OpenCV indices and hardware names).
Returns a list of friendly names or indices that can be used by other Camera nodes.

Inputs:
- Flow: Trigger the scan.
- Max Search: The maximum number of indices to probe.

Outputs:
- Flow: Triggered after the scan is complete.
- Cameras: List of identified camera names.
- Count: Total number of cameras found.

### Color Constant

**Version**: 2.0.2
**Description**: Outputs a fixed color value.
Supports RGBA hex strings (e.g., "#800080FF") and manages the color data type.

Inputs:
- Flow: Trigger the output.
- Color: Optional input to override the constant value.

Outputs:
- Flow: Triggered after output.
- Result: The specified color in RGBA hex format.

### Compare

**Version**: 2.0.2
**Description**: Performs a comparison between two values (A and B) using a specified operator.
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

### Compare Type

**Version**: 2.0.2
**Description**: Provides a selectable comparison operator (e.g., ==, !=, >, <) as a pulse-triggered output.
Essential for configuring conditional logic in nodes that require a comparison operator.

Inputs:
- Flow: Trigger the output of the selected comparison type.
- Value: Optionally set the comparison operator via a logic pulse.

Outputs:
- Flow: Pulse triggered after the value is processed.
- Result: The selected comparison operator string.

### Cosh

**Version**: 2.0.2
**Description**: Calculates the hyperbolic cosine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic cosine.

### Debug Node

**Version**: 2.0.2
**Description**: Logs input data to the console for debugging purposes.

Inputs:
- Flow: Execution trigger.
- Data: The information to be logged.

Outputs:
- Flow: Triggered after logging.

### E

**Version**: 2.0.2
**Description**: Outputs the mathematical constant e (Euler's number, 2.71828...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of e.

### End Node

**Version**: 2.0.2
**Description**: Terminates the execution of the current branch.

When flow reaches this node, the execution engine stops processing further nodes 
in this specific sequence. It is used to mark the logical conclusion of a 
workflow where no further output pulse is desired.

Inputs:
- Flow: Execution trigger.

Outputs:
- None: This node is a terminator and has no outputs.

### End Try Node

**Version**: 2.0.2
**Description**: Closes an error-handling (Try/Catch) scope.

This node serves as a marker for the Execution Engine to pop the current 
error-handling context and continue normal flow. It ensures that subsequent 
errors are handled by the next level up in the hierarchy.

Inputs:
- Flow: Execution trigger from the Try or Catch block.

Outputs:
- Flow: Pulse triggered after the scope is safely closed.

### Environment Var

**Version**: 2.0.2
**Description**: Manages operating system environment variables (e.g., PATH, HOME).

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

### Event Log Watcher

**Version**: 2.0.2
**Description**: Reads recent entries from Windows Event Logs (System, Application, Security).
Allows monitoring system events and security logs for specific patterns.

Inputs:
- Flow: Trigger the log reading operation.
- Log Type: The log category to read ('System', 'Application', or 'Security').
- Limit: The maximum number of recent events to retrieve.

Outputs:
- Flow: Triggered after logs are retrieved.
- Logs: A list of event dictionaries containing time, source, ID, and message.

### Event Trigger

**Version**: 2.0.2
**Description**: Standardized service for listening to global system events.
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

### Excel Commander

**Version**: 2.0.2
**Description**: Executes automated commands or macros within an Excel workbook.

This node interacts with an active Excel Provider scope. If no provider 
is active, it can optionally open a file directly if 'File Path' is provided.

Inputs:
- Flow: Trigger command execution.
- File Path: The absolute path to the workbook (optional if using a Provider).
- Command: The instruction or macro name to execute.

Outputs:
- Flow: Pulse triggered after the command completes.
- Result: The return value or status from Excel.

### Excel Provider

**Version**: 2.0.2
**Description**: Establishes an automation environment for Microsoft Excel workbooks.

This provider manages the lifecycle of an Excel application instance, 
allowing downstream 'Excel Commander' nodes to execute within a shared context.

Inputs:
- Flow: Open Excel and load the specified workbook.
- Provider End: Close the workbook and shut down Excel.
- File Path: The absolute path to the workbook (.xlsx, .xls).

Outputs:
- Provider Flow: Active while the spreadsheet is open.
- Provider ID: Identifier for automation node targeting.
- Flow: Pulse triggered after the scope is closed.

### Exit Batch

**Version**: 2.0.2
**Description**: Immediately terminates an active Batch Iterator loop.

This node acts like a 'break' statement. When triggered, it signals the 
parent Batch Iterator to stop processing the current batch and transition 
to its final 'Flow' output.

Inputs:
- Flow: Trigger the early exit.

Outputs:
- Flow: Pulse triggered after signaling the break.

### Exit For

**Version**: 2.0.2
**Description**: Terminates an active loop (For or Foreach) early.

Acts as a 'break' statement. When triggered, it signals the parent loop 
node to stop iterating and transition to its completion 'Flow' output.

Inputs:
- Flow: Trigger the break signal.

Outputs:
- Flow: Pulse triggered after the signal is sent.

### Exit Trigger

**Version**: 2.0.2
**Description**: Deactivates a persistent signal (Tag) set by a 'Trigger' node.

When flow reaches this node, the state associated with the specified 'Tag' 
is set to False. This can be used to stop execution branches or reset latches.

Inputs:
- Flow: Trigger the deactivation signal.
- Tag: The unique identifier of the trigger to deactivate.

Outputs:
- Flow: Pulse triggered after the signal is dispatched.

### Exit While

**Version**: 2.0.2
**Description**: Terminates an active While loop early.

Acts as a 'break' statement. When triggered, it signals the 'While Loop' 
node to stop iterating and transition to its completion 'Flow' output.

Inputs:
- Flow: Trigger the break signal.

Outputs:
- Flow: Pulse triggered after the signal is sent.

### File Watcher

**Version**: 2.0.2
**Description**: Monitors a file for changes by comparing its last modification time.

This node checks if the file at 'Path' has been updated since the last check 
or since 'Last Time'. It is useful for triggering logic when a configuration 
file, log, or data export is updated by an external process.

Inputs:
- Flow: Trigger the check.
- Path: The absolute path to the file to monitor.
- Last Time: Optional ISO timestamp to compare against (replaces internal memory).

Outputs:
- Flow: Pulse triggered after the check.
- Changed: Boolean True if the file has been modified.
- Time: The ISO timestamp of the file's current modification time.

### For Node

**Version**: 2.0.2
**Description**: Executes a block of code a specific number of times based on a numeric range.

This node maintains an internal counter ('Index'). It supports 'Continue' 
(next iteration) and 'Break' (exit loop) flow inputs for granular control 
over iteration logic.

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

### ForEach Node

**Version**: 2.0.2
**Description**: Iterates through a list of items, executing the 'Body' output for each element.

This node maintains the current iteration state, allowing for sequential processing 
of arrays or collections. It supports 'Continue' and 'Break' signals for loop control.

Inputs:
- Flow: Start the iteration from the first item.
- Continue: Move to the next item in the list.
- Break: Terminate the loop immediately.
- List: The collection of items to iterate over.

Outputs:
- Flow: Triggered when the entire list has been processed or the loop is broken.
- Body: Triggered for each individual item in the list.
- Item: The current value from the list.
- Index: The zero-based position of the current item.

### Fuzzy Search

**Version**: 2.0.2
**Description**: Performs fuzzy string matching and automated spell correction.

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

### HTML Parser

**Version**: 2.0.2
**Description**: Parses HTML content and extracts data using CSS Selectors.

This node takes an HTML string and applies a CSS selector (e.g., 'a', '.title', 
'#content') to find matching elements, returning their stripped text content 
as a list.

Inputs:
- Flow: Trigger the parsing process.
- HTML String: The raw HTML content to parse.
- Selector: CSS Selector string for targeting elements.

Outputs:
- Flow: Triggered after parsing completes.
- Text List: List of extracted text strings from matching elements.

### Last Error Node

**Version**: 2.0.2
**Description**: Retrieves information about the most recent error caught by the engine.

This node is typically used within a Catch block or immediately after a 
failure to inspect error details such as the message, node ID, and trace.

Inputs:
- Flow: Trigger the retrieval.

Outputs:
- Flow: Pulse triggered after retrieval.
- Error Object: An Error object containing Message, Node ID, and context.

### MCP Client

**Version**: 2.0.2
**Description**: Connects to a Model Context Protocol (MCP) server.
Supports stdio and SSE transports. Lists available tools upon connection.

Inputs:
- Flow: Trigger the connection.
- Config: Server configuration dictionary.
- Enabled: Toggles the client state.

Outputs:
- Flow: Triggered after connection attempt.
- Status: Connection status message.
- Tools: List of tool names provided by the server.

### MCP Resource

**Version**: 2.0.2
**Description**: Reads a resource from a connected MCP server using a URI.
Returns the resource content and its associated MIME type.

Inputs:
- Flow: Trigger the resource read.
- Server: The name of the target MCP server.
- URI: The unique identifier for the resource.

Outputs:
- Flow: Triggered after resource read.
- Content: The resource data.
- MimeType: The detected MIME type of the resource.
- Error: Error message if the read failed.

### MCP Tool

**Version**: 2.0.2
**Description**: Calls a specific tool on a connected MCP server.
Passes arguments and returns the raw output or error message.

Inputs:
- Flow: Trigger the tool call.
- Server: The name of the target MCP server.
- Tool: The name of the tool to execute.
- Args: Dictionary of arguments for the tool.

Outputs:
- Flow: Triggered after the tool execution.
- Result: The response from the tool.
- Error: Error message if the call failed.

### Merge Color

**Version**: 2.0.2
**Description**: Combines individual Red, Green, Blue, and Alpha components into a single color value.
Resulting output is an RGBA hex string.

Inputs:
- Flow: Trigger the merge.
- R, G, B, A: Numerical components (0-255).

Outputs:
- Flow: Triggered after merge.
- Color: The combined color in RGBA hex format.

### NAND

**Version**: 2.0.2
**Description**: Performs a logical NAND operation.

Returns True if at least one input is False. Returns False only 
if all provided inputs are True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NAND result.

### NOR

**Version**: 2.0.2
**Description**: Performs a logical NOR operation.

Returns True only if all provided inputs are False. Returns False 
 if at least one input is True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NOR result.

### NOT

**Version**: 2.0.2
**Description**: Logical NOT operator. Inverts the input boolean.

Inputs:
- Flow: Trigger execution.
- In: The input boolean value.

Outputs:
- Flow: Triggered after inversion.
- Result: The inverted result.

### Net Listener

**Version**: 2.0.2
**Description**: Establishes an event listener on the active Network Provider to capture incoming messages.
Triggers the graph sequence whenever new data is received.

Inputs:
- Flow: Initialize the listener.
- App ID: Optional identifier for isolation/authentication.

Outputs:
- Flow: Triggered every time a new message is received.
- Message: The incoming data payload.

### Net Request

**Version**: 2.0.2
**Description**: Executes a high-level network request using the active Network Provider context.
Supports RESTful APIs and basic gRPC stub calls with identity-based authentication.

Inputs:
- Flow: Trigger the network request.
- Method: The HTTP method to use (GET, POST, etc.).
- Endpoint: The specific API path relative to the Base URL.
- Payload: The data to send (Dictionary for JSON, or raw string/bytes).
- App ID: Optional identifier for retrieving authentication credentials.

Outputs:
- Flow: Triggered after the request completes.
- Error Flow: Triggered if the request fails (network error, timeout).
- Response: The raw text or data returned by the server.
- Status: The numeric HTTP status code (e.g., 200, 404).

### Net Stream

**Version**: 2.0.2
**Description**: Pushes data messages through an established streaming connection in the active Network Provider context.

Inputs:
- Flow: Trigger the message push.
- Message: The data or object to transmit through the stream.

Outputs:
- Flow: Triggered after the message is sent.
- Error Flow: Triggered if the transmission fails.

### OR

**Version**: 2.0.2
**Description**: Performs a logical OR operation on a set of boolean inputs.

Returns True if at least one of the provided inputs is True. 
Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if any input is True, False otherwise.

### Parallel Runner

**Version**: 2.0.2
**Description**: Executes a subgraph in parallel across multiple worker processes.

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

### Pi

**Version**: 2.0.2
**Description**: Outputs the mathematical constant Pi (3.14159...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of Pi.

### Print

**Version**: 2.0.2
**Description**: Outputs a message to the system terminal or console.
Useful for debugging and tracking graph execution flow.

Inputs:
- Flow: Trigger the print operation.
- Message: The string message to display.

Outputs:
- Flow: Pulse triggered after the message is printed.

### Project Var Get

**Version**: 2.0.2
**Description**: Retrieves a global project variable from the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the retrieval.
- Name: The name of the project variable to get.

Outputs:
- Flow: Pulse triggered after retrieval.
- Value: The current value of the project variable.

### Project Var Set

**Version**: 2.0.2
**Description**: Sets a global project variable in the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the update.
- Name: The name of the project variable to set.
- Value: The new value to assign to the variable.

Outputs:
- Flow: Pulse triggered after the variable is updated.

### Python Script

**Version**: 2.0.2
**Description**: Executes a Python script either synchronously or as a background service.

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

### Raise Error

**Version**: 2.0.2
**Description**: Artificially triggers an error to halt execution or test Error Handling.

When flow reaches this node, it forces a Python exception with the 
specified message, which will be caught by any active Try/Catch blocks.

Inputs:
- Flow: Trigger the error.
- Message: The custom error message to report.

Outputs:
- Flow: Pulse triggered on success (rarely reached due to error).
- Error: Pulse triggered if the engine supports non-halting errors.

### Random

**Version**: 2.0.2
**Description**: Generates a pseudo-random number or currency value within a specified range.
Supports both integer 'Number' and decimal 'Currency' (2 decimal places) types.

Inputs:
- Flow: Trigger the random generation.
- Min: The minimum value of the range.
- Max: The maximum value of the range.
- Random Type: The type of output ('Number' or 'Currency').

Outputs:
- Flow: Pulse triggered after generation.
- Result: The generated random value.

### Random Type

**Version**: 2.0.2
**Description**: Standardizes the selection of random generation algorithms.

Provides a consistent label for common random types like 'Number' (float), 
'Integer', or 'Unique ID' (UUID). This node is typically linked to a 
'Random' node to define its behavior.

Inputs:
- Value: The random type selection (Number, Integer, UID).

Outputs:
- Result: The selected type string.

### Receiver

**Version**: 2.0.2
**Description**: Listens for data broadcasted across the graph using a specific 'Tag'.

Acts as a wireless receiver for values sent by 'Sender' nodes. When 
triggered, it retrieves the payload associated with the 'Tag' from 
the engine's global memory.

Inputs:
- Flow: Trigger the retrieval.
- Tag: The unique identifier for the communication channel.

Outputs:
- Flow: Triggered after data is retrieved.
- Data: The primary payload (if single value) or the full dictionary.

### Registry Modify

**Version**: 2.0.2
**Description**: Interfaces with the Windows Registry to write or delete keys.
Requires administrative permissions for some HKEY_LOCAL_MACHINE operations.

Inputs:
- Flow: Trigger the registry operation.
- Key Path: The full registry path (e.g., HKEY_CURRENT_USER\Software\Synapse).
- Value Name: The name of the registry value to target.
- Value Data: The data to write (used for Write Key action).
- Action: 'Write' or 'Delete' (Default: Write).

Outputs:
- Flow: Pulse triggered after the operation completes.

### Registry Read

**Version**: 2.0.2
**Description**: Reads values from the Windows Registry.

Inputs:
- Flow: Trigger the registry read.
- Key Path: The full registry path.
- Value Name: The name of the registry value to read.

Outputs:
- Flow: Pulse triggered after retrieval.
- Value: The data retrieved from the registry.

### Render Timeline

**Version**: 2.0.2
**Description**: Renders a compiled timeline into a video file.

Uses MoviePy to process a 'SceneList' (timeline) and export it 
as an MP4, GIF, or other video format. Supports resolution, FPS, 
and audio ducking controls.

Inputs:
- Flow: Trigger the render.
- Compiled Timeline: The SceneList data to render.
- Output Path: Destination file path (default 'output.mp4').
- Width: Output video width (default 1920).
- Height: Output video height (default 1080).
- FPS: Frames per second (default 24).
- Auto Ducking: Whether to automatically lower background music for speech.

Outputs:
- Flow: Pulse triggered once rendering completes.

### Reset Barrier

**Version**: 2.0.2
**Description**: Resets a 'Barrier' node's internal synchronization counters.

Forcibly clears the progress of a specific Barrier, allowing it to 
re-synchronize from zero. Useful for looping or complex branches 
that re-enter the same Barrier multiple times.

Inputs:
- Flow: Trigger the reset.
- Barrier ID: The unique node ID of the Barrier to reset.

Outputs:
- Flow: Triggered after the reset.

### Return Node

**Version**: 2.0.2
**Description**: The exit point for a graph or subgraph execution.

Sends results back to the caller (e.g., a 'Run Graph' or 'SubGraph' node). 
It consumes all incoming data and bundles it into the return payload.

Inputs:
- Flow: Trigger the return.

Outputs:
- None (Terminator node).

### Run Split

**Version**: 2.0.2
**Description**: Splits flow based on whether a value is populated or 'Null'.

Checks the 'Value' input. If it is non-empty and valid, the 'Valid' 
port is pulsed. If it is None, empty, or "none", the 'Null' 
port is pulsed.

Inputs:
- Flow: Trigger the check.
- Value: The data to validate.

Outputs:
- Valid: Pulse triggered if value is valid.
- Null: Pulse triggered if value is empty/null.

### SFTP Transfer

**Version**: 2.0.2
**Description**: Performs file transfers using the SFTP protocol.
Supports both Upload and Download operations. Can automatically 
discover credentials if nested inside an SSH Provider scope.

Inputs:
- Flow: Trigger the file transfer.
- Host: Target hostname (Optional if using SSH Provider).
- User: Username (Optional if using SSH Provider).
- Password: Password (Optional if using SSH Provider).
- Local Path: The filesystem path on the local machine.
- Remote Path: The filesystem path on the remote server.

Outputs:
- Complete: Pulse triggered when the transfer finishes successfully.
- Progress: Pulse triggered during transfer updates.

### Sender

**Version**: 2.0.2
**Description**: Broadcasts data across the graph using a specific 'Tag'.

Acts as a wireless transmitter. Data sent to this node can be 
retrieved by 'Receiver' nodes using the same 'Tag'. Supports 
dynamic inputs which are bundled into the broadcast payload.

Inputs:
- Flow: Trigger the broadcast.
- Tag: The unique identifier for the communication channel.
- Data: The primary payload to send.

Outputs:
- None (Ends execution branch or sinks pulse).

### Service Controller

**Version**: 2.0.2
**Description**: Manages Windows Services (Start, Stop, Restart).
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

### Service Exit Trigger

**Version**: 2.0.2
**Description**: Utility node to remotely deactivate an Event Trigger service.
Targeting is done via 'Trigger ID', or all triggers if ID is empty.

Inputs:
- Flow: Execution trigger.
- Trigger ID: The ID of the specific target trigger node (optional).

Outputs:
- Flow: Triggered after the signal is sent.

### Service Return

**Version**: 2.0.2
**Description**: Signals the end of a service or subgraph execution phase.

Used within service graphs to return control and data back to 
the parent graph. It packages all non-flow inputs into a 
return payload.

Inputs:
- Flow: Trigger the return.

Outputs:
- None (Terminator node).

### Shell Command

**Version**: 2.0.2
**Description**: Executes shell commands on the host system.
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

### Sinh

**Version**: 2.0.2
**Description**: Calculates the hyperbolic sine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic sine.

### SocketIO Client Provider

**Version**: 2.0.2
**Description**: Connects to a remote SocketIO server.

Inputs:
- Flow: Establish connection and enter scope.
- URL: The server URL (Default: http://127.0.0.1:5000).

Outputs:
- Provider Flow: Active while connected.

### SocketIO Emit

**Version**: 2.0.2
**Description**: Emits an event to the active SocketIO Provider.

Inputs:
- Flow: Trigger emission.
- Event: The event name.
- Body: The data payload.

Outputs:
- Flow: Triggered after the event is emitted.

### SocketIO On Event

**Version**: 2.0.2
**Description**: Listens for a specific event on the active SocketIO Provider.

Inputs:
- Flow: Start the event watch.
- Stop: Stop the event watch and finish.
- Event: The event name to listen for.

Outputs:
- On Event: Pulse triggered when message received.
- Received Data: The data payload.
- Flow: Triggered when the service stops.

### SocketIO Room

**Version**: 2.0.2
**Description**: Manages client participation in SocketIO rooms.
Requires a SocketIO Server Provider.

Inputs:
- Flow: Trigger management.
- SID: Client session ID.
- Room: Room name.
- Action: 'Join' or 'Leave' (Default: Join).

Outputs:
- Flow: Triggered after the room action is performed.

### SocketIO Server Provider

**Version**: 2.0.2
**Description**: Hosts a SocketIO server. Can attach to an existing Flask Host.

Inputs:
- Flow: Start the server and enter scope.
- Provider End: Pulse to close scope.
- Host: (Optional) The address to bind to if standalone.
- Port: (Optional) The port to bind to if standalone (Default: 5000).

Outputs:
- Provider Flow: Active while the server is running.
- Provider ID: Unique ID for this provider.

### Split Color

**Version**: 2.0.2
**Description**: Deconstructs a color value into its individual Red, Green, Blue, and Alpha components.
Supports both RGBA hex strings and list formats.

Inputs:
- Flow: Trigger the split.
- Color: The color value to split.

Outputs:
- Flow: Triggered after split.
- R, G, B, A: The numerical components (0-255).

### Start Node

**Version**: 2.0.2
**Description**: The entry point for a graph or subgraph execution.

Initiates the flow and optionally injects global variables or provider 
contexts into the runtime. It acts as the primary data producer for 
the starting branch.

Inputs:
- None (Initiator node).

Outputs:
- Flow: The primary execution pulse.
- Error Flow: Pulse triggered if context initialization fails.

### SubGraph Node

**Version**: 2.0.2
**Description**: Executes a nested graph (subgraph) as a single node within the current context.

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

### Switch

**Version**: 2.0.2
**Description**: Directs execution flow based on a match between an input value and one of several named output ports.

This node functions like if-elif-else or switch-case statements in programming. 
It compares the 'Value' against the names of all custom output ports (cases). 
Matching is string-based and case-insensitive. If no match is found, the 'Default' port is triggered.

Inputs:
- Flow: Execution trigger.
- Value: The data item to evaluate.

Outputs:
- Default: Pulse triggered if no matching case is found.
- [Dynamic Cases]: Custom ports where the port name defines the matching value.

### TCP Client Provider

**Version**: 2.0.2
**Description**: Connects to a remote TCP server and provides the connection to child nodes.

Inputs:
- Flow: Establish connection and enter scope.
- Host: Server address.
- Port: Server port.

Outputs:
- Provider Flow: Active while connected.

### TCP Receive

**Version**: 2.0.2
**Description**: Receives data from an active TCP Provider context.

Inputs:
- Flow: Trigger receive.
- Buffer Size: Max bytes to read (Default: 4096).

Outputs:
- Flow: Pulse triggered after receiving.
- Body: The received data.

### TCP Send

**Version**: 2.0.2
**Description**: Sends data through an active TCP Provider context.

Inputs:
- Flow: Trigger send.
- Body: Data to send (String or Bytes).

Outputs:
- Flow: Triggered after the data is sent.

### TCP Server Provider

**Version**: 2.0.2
**Description**: Hosts a TCP server and provides connection handles to child nodes.

Inputs:
- Flow: Start the server and enter scope.
- Provider End: Pulse to close scope.
- Host: Interface to bind to (Default: 127.0.0.1).
- Port: Port to listen on (Default: 6000).

Outputs:
- Provider Flow: Active while the server is running.
- Provider ID: Unique ID for this provider.
- On Connection: Pulse triggered for each new client connection.
- Client Info: Address of the connected client.

### Tanh

**Version**: 2.0.2
**Description**: Calculates the hyperbolic tangent of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic tangent.

### Throttle

**Version**: 2.0.2
**Description**: Delays execution of the flow to prevent rapid repeated triggers.

Similar to a wait, but specifically used to 'throttle' processes that 
might otherwise run too fast or too often. It accepts a delay in milliseconds.

Inputs:
- Flow: execution trigger.
- Delay MS: Duration of the delay in milliseconds.

Outputs:
- Flow: Triggered after the delay is complete.

### Time

**Version**: 2.0.2
**Description**: Captures the current system date and time.
Returns the timestamp in a standardized format inside Synapse tags.

Inputs:
- Flow: Trigger the time capture.

Outputs:
- Flow: Pulse triggered after time is captured.
- Time: The current timestamp string (e.g., #[2024-05-20 12:00:00]#).

### Timeline Start

**Version**: 2.0.2
**Description**: Initiates a new video timeline session.

Creates an empty 'SceneList' object that can be populated with 
clips, graphics, and audio by downstream nodes. Acts as a 
provider for video building tasks.

Inputs:
- Flow: Trigger the timeline start.

Outputs:
- Flow: Pulse triggered once the timeline is initialized.
- SceneList: The empty SceneList object.

### Trigger

**Version**: 2.0.2
**Description**: Sets a persistent signal (Tag) that can be checked or used to release other branches.

This node acts like a digital latch. When triggered via 'Flow', it sets the state 
associated with 'Tag' to True. This state remains until manually deactivated via 
the 'Stop' input or an 'Exit Trigger' node.

Inputs:
- Flow: Set the trigger state to True.
- Stop: Deactivate the trigger (Set state to False).
- Tag: Unique identifier for this trigger state.

Outputs:
- Flow: Pulse triggered after activation.

### Try Node

**Version**: 2.0.2
**Description**: Initiates a protected execution block (Exception Handler).

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

### User Activity

**Version**: 2.0.2
**Description**: Monitors system-wide user activity to detect idle states.
Uses native OS hooks (Windows) or mouse tracking fallback to distinguish 
between active and idle sessions.

Inputs:
- Flow: Check for user activity.
- Timeout MS: The idle duration threshold in milliseconds (default: 5000).

Outputs:
- Active Flow: Pulse triggered if activity was detected within the timeout.
- Idle Flow: Pulse triggered if the system has been idle longer than the timeout.

### VENV Create

**Version**: 2.0.2
**Description**: Creates a new Python Virtual Environment at the specified path.
Includes pip by default to allow for immediate package installation.

Inputs:
- Flow: Trigger the creation process.
- Path: The target directory for the new VENV.

Outputs:
- Flow: Pulse triggered after the operation finishes.
- Success: True if the environment was created successfully.

### VENV Install

**Version**: 2.0.2
**Description**: Installs one or more pip packages into an existing virtual environment.

Inputs:
- Flow: Trigger the installation.
- VENV Path: The path to the target virtual environment.
- Packages: A list or single string of package names to install.

Outputs:
- Flow: Pulse triggered after the installation process completes.

### VENV List

**Version**: 2.0.2
**Description**: Lists all pip packages currently installed in a specified virtual environment.

Inputs:
- Flow: Trigger the listing process.
- VENV Path: The path to the virtual environment to audit.

Outputs:
- Flow: Pulse triggered after the list is retrieved.
- Packages: A list of installed packages and their versions (pip freeze format).

### VENV Provider

**Version**: 2.0.2
**Description**: Establishes a Virtual Environment (VENV) context for downstream nodes.
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

### VENV Remove

**Version**: 2.0.2
**Description**: Deletes an entire virtual environment directory from the disk.

Inputs:
- Flow: Trigger the removal process.
- VENV Path: The path to the virtual environment to delete.

Outputs:
- Flow: Pulse triggered after the deletion attempt.
- Success: True if the directory was successfully removed.

### VENV Run

**Version**: 2.0.2
**Description**: Executes a Python command or script within the context of a virtual environment.
Supports running specific modules (via -m) or standalone .py files.

Inputs:
- Flow: Trigger the execution.
- Command: The script path or module name to run.
- Args: A list of command-line arguments to pass.

Outputs:
- Flow: Pulse triggered after the command finishes.
- Output: The stdout resulting from the execution.
- Exit Code: The numerical return code of the process.

### Wait

**Version**: 2.0.2
**Description**: Suspends the execution of the current branch for a specified duration.

This node is non-blocking to other parallel branches. It returns a signal 
tells the Execution Engine to resume this specific branch after the 
'Milliseconds' have elapsed.

Inputs:
- Flow: Trigger to begin the waiting period.
- Milliseconds: The duration to wait (1000ms = 1 second).

Outputs:
- Flow: Pulse triggered after the timer expires.

### Watchdog

**Version**: 2.0.2
**Description**: Monitors system resource usage including CPU, RAM, and Disk space.
Provides real-time telemetry about the host operating system.

Inputs:
- Flow: Trigger the resource check.

Outputs:
- Flow: Pulse triggered after data is captured.
- CPU: Total CPU usage percentage (FLOAT).
- RAM: Total RAM usage percentage (FLOAT).
- Drives: List of connected drives and their usage (LIST).
- OS: The name of the host operating system (STRING).

### While Node

**Version**: 2.0.2
**Description**: Repeatedly executes a block of code as long as a boolean condition remains true.

The condition is re-evaluated at the start of each iteration. Use 'Loop' 
to signal the next check, and 'Exit' to break out early.

Inputs:
- Flow: Start the while loop evaluation.
- Loop: Trigger the next iteration/check of the loop.
- Exit: Immediately terminate the loop.
- Condition: A boolean value determining if the loop should continue.

Outputs:
- Loop Flow: Pulse triggered for each iteration while the condition is met.

### Window Information

**Version**: 2.0.2
**Description**: Retrieves detailed properties for a specific window given its handle.
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

### Window List

**Version**: 2.0.2
**Description**: Retrieves a list of all visible window titles and handles for a specific process.
Useful for identifying target windows for automation.

Inputs:
- Flow: Trigger the window enumeration.
- Process ID: The numeric ID of the process to inspect.

Outputs:
- Flow: Triggered after listing is complete.
- Titles: List of window titles found.
- Handles: List of numeric window handles (HWND) found.

### Write Mode

**Version**: 2.0.2
**Description**: Standardizes file writing behaviors such as 'Overwrite' or 'Append'.

This node provides a UI dropdown for selecting how file operations should 
interact with existing files. 'Overwrite' replaces the entire file content, 
while 'Append' adds new data to the end of the file.

Inputs:
- Value: The selected write mode (Overwrite/Append).
- Value Options: The list of toggleable modes.
- Header Color: The UI accent color for this node.

Outputs:
- Result: The selected mode string (compatible with Write nodes).

### XNOR

**Version**: 2.0.2
**Description**: Performs a logical XNOR operation.

Returns True if an even number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The XNOR result.

### XOR

**Version**: 2.0.2
**Description**: Performs a logical XOR (Exclusive OR) operation.

Returns True if an odd number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if the XOR condition is met.

### Yield

**Version**: 2.0.2
**Description**: Pauses execution of the 'Flow' branch until a separate 'Trigger' pulse is received.

This is useful for synchronization between asynchronous branches. If the 'Trigger' 
arrives before the 'Flow' reaches this node, the pulse will pass through 
instantly when it arrives.

Inputs:
- Flow: The primary execution branch to be paused.
- Trigger: The signal required to release the paused 'Flow'.

Outputs:
- Flow: The original 'Flow' pulse, released once 'Trigger' is received.

---
[Back to Nodes Index](Index.md)
