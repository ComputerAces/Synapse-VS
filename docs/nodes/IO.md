# 🧩 IO Nodes

This document covers nodes within the **IO** core category.

## 📂 Documents

### Excel Commander

**Version**: `2.1.0`

Executes automated commands or macros within an Excel workbook.

This node interacts with an active Excel Provider scope. If no provider 
is active, it can optionally open a file directly if 'File Path' is provided.

Inputs:
- Flow: Trigger command execution.
- File Path: The absolute path to the workbook (optional if using a Provider).
- Command: The instruction or macro name to execute.

Outputs:
- Flow: Pulse triggered after the command completes.
- Result: The return value or status from Excel.

---

### Excel Provider

**Version**: `2.1.0`

Establishes an automation environment for Microsoft Excel workbooks.

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

---

## 📂 Files

### Archive Read

**Version**: `2.1.0`

Extracts ZIP archives into a targeted destination folder.

Inputs:
- Flow: Trigger the extraction process.
- Archive Path: The absolute path to the .zip archive to extract.
- Destination Folder: The folder path where the contents will be extracted.

Outputs:
- Flow: Triggered after extraction (success or failure).
- Success: Triggered ONLY if the extraction was successful.
- Extracted Path: The absolute path to the folder containing extracted files.

---

### Archive Write

**Version**: `2.1.0`

Compresses files or directories into a ZIP archive.

Inputs:
- Flow: Trigger the compression process.
- Source Path: The absolute path of the file or folder to be compressed.
- Archive Path: The absolute path where the resulting ZIP file will be saved.

Outputs:
- Flow: Triggered after compression (success or failure).
- Success: Triggered ONLY if the compression was successful.
- Result Path: The absolute path to the generated ZIP file.

---

### File Watcher

**Version**: `2.1.0`

Monitors a file for changes by comparing its last modification time.

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

---

[Back to Node Index](Index.md)
