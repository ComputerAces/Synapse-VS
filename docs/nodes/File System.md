# 🧩 File System Nodes

This document covers nodes within the **File System** core category.

## 📂 File Editing

### File Seek

**Version**: `2.1.0`

Adjusts the read/write pointer within an open file provider.

Use this to move the pointer forward, backward, or to a specific offset 
relative to the start, current position, or end of the file.

Inputs:
- Flow: Trigger the seek operation.
- Offset: Number of bytes to move the pointer.
- Whence: Reference point (0: Start, 1: Current, 2: End).

Outputs:
- Flow: Pulse triggered on successful movement.
- Error Flow: Pulse triggered if the seek is invalid or fails.

---

### File System Provider

**Version**: `2.1.0`

Managed service provider for low-level file system I/O.
Opens a persistent file handle and provides hijackable operations (read, write, seek, etc.)
for downstream nodes within its execution scope.

Inputs:
- Flow: Start the file provider scope.
- Provider End: Close the file handle and end the scope.
- File Path: The absolute path to the file.
- Mode: The file open mode (r, w, a, rb, wb, etc.).

Outputs:
- Provider Flow: Active while the file handle is open.
- Provider ID: Unique identifier for this provider.
- Flow: Triggered when the file is closed.

---

## 📂 General

### Change Folder

**Version**: `2.1.0`

Changes the current working directory or global path reference for file operations.
Validates that the target path exists and is a directory before applying the change.

Inputs:
- Flow: Trigger the path change.
- Path: The absolute or relative path to switch to.

Outputs:
- Flow: Triggered if the path was successfully changed.
- Error Flow: Triggered if the path is invalid or inaccessible.

---

### Copy File

**Version**: `2.1.0`

Copies a file or directory from a source path to a destination path.
Supports recursive directory copying and automatic parent directory creation.

Inputs:
- Flow: Trigger the copy operation.
- Source: The path to the file or folder to copy.
- Destination: The target path where the item should be copied.

Outputs:
- Flow: Triggered if the copy operation completes successfully.
- Error Flow: Triggered if the source is missing or an I/O error occurs.

---

### Create File

**Version**: `2.1.0`

Creates a new file at the specified path with the provided content.
Automatically creates parent directories and supports overwriting existing files.

Inputs:
- Flow: Trigger the file creation.
- Path: The full path where the file should be created.
- Content: The text or binary data to write into the file.

Outputs:
- Flow: Triggered if the file is created successfully.
- Error Flow: Triggered if the path is invalid or an I/O error occurs.

---

### Current Folder

**Version**: `2.1.0`

Retrieves the absolute path of the current working directory or the specific project path context.

Inputs:
- Flow: Trigger the path retrieval.

Outputs:
- Flow: Triggered after the path is retrieved.
- Path: The absolute directory path.

---

### Delete File

**Version**: `2.1.0`

Deletes a file or directory from the filesystem.

Inputs:
- Flow: Execution trigger.
- Path: The absolute or relative path to the item to delete.

Outputs:
- Flow: Triggered after the deletion attempt.
- Error Flow: Triggered if the deletion failed.

---

### List Files

**Version**: `2.1.0`

Retrieves a list of filenames within a specified directory.

Filters for files only (excluding subdirectories). Supports project 
variable resolution and defaults to the current working directory if empty.

Inputs:
- Flow: Trigger the listing operation.
- Path: The absolute path of the folder to scan.

Outputs:
- Flow: Pulse triggered after the operation.
- Files List: A list of strings containing the names of files found.

---

### Make Directory

**Version**: `2.1.0`

Creates a new directory at the specified path.

Automatically creates all parent directories if they do not exist 
(equivalent to 'mkdir -p'). Supports project variable resolution.

Inputs:
- Flow: Trigger the directory creation.
- Path: The absolute path of the directory to create.

Outputs:
- Flow: Pulse triggered on successful creation.
- Error Flow: Pulse triggered if the operation fails (e.g., permission denied).

---

### Move File

**Version**: `2.1.0`

Moves or renames a file or directory to a new location.

Uses high-level shell operations to relocate items across the file system. 
Supports project variable resolution for both Source and Destination.

Inputs:
- Flow: Trigger the move operation.
- Source: The absolute current path of the item.
- Dest: The absolute destination path (including new name if applicable).

Outputs:
- Flow: Pulse triggered on successful move.
- Error Flow: Pulse triggered if the move fails or source is missing.

---

### Path Exists

**Version**: `2.1.0`

Checks if a path exists and identifies its type (File vs Directory).

Provides boolean outputs for existence and classification, useful for 
conditional branching before performing file operations.

Inputs:
- Flow: Trigger the existence check.
- Path: The absolute path to verify.

Outputs:
- Flow: Pulse triggered after the check.
- Exists: True if the path exists.
- IsFile: True if the path points to a file.
- IsDir: True if the path points to a directory.

---

### Read File

**Version**: `2.1.0`

Reads content from a file path with support for smart type detection.

This node can read plain text, JSON (as objects), or Images (as ImageObjects). 
It supports project variable resolution (e.g., %ID%) and permission checks.

Inputs:
- Flow: Trigger the read operation.
- Path: The absolute path to the file.
- Start: Starting character offset (for text).
- End: Ending character offset (-1 for until EOF).

Outputs:
- Flow: Pulse triggered on successful read.
- Error Flow: Pulse triggered if the file is missing or error occurs.
- Data: The content retrieved (String, Dict, or ImageObject).

---

### Rename File

**Version**: `2.1.0`

Changes the name of a file or directory while keeping it in the same folder.

This node takes a full path and a new name string, then performs an 
in-place rename within the parent directory.

Inputs:
- Flow: Trigger the rename operation.
- OldPath: The current absolute path of the file.
- NewName: The new name (filename only, not a path).

Outputs:
- Flow: Pulse triggered on successful rename.
- Error Flow: Pulse triggered if the file is missing or rename fails.

---

### Write File

**Version**: `2.1.0`

Writes data to a specified file path with smart type detection.

Supports writing Text, Binary (bytes), JSON (as objects), and Images 
(PIL objects). Automatically creates parent directories if they are missing.

Inputs:
- Flow: Trigger the write operation.
- Path: The absolute destination file path.
- Data: The content to write (String, Bytes, Dict, or Image).
- Mode: Writing behavior ('Overwrite' or 'Append').
- Start Position: Byte offset to start writing from (optional).

Outputs:
- Flow: Pulse triggered on successful write.
- Error Flow: Pulse triggered if permission denied or error occurs.

---

## 📂 Operations

### File Peek

**Version**: `2.1.0`

Reads data from a file without moving the active pointer position.

Peek allows investigating upcoming data in the stream without affecting 
subsequent Read operations within the same provider session.

Inputs:
- Flow: Trigger the peek operation.
- Size: Number of bytes/characters to peek.

Outputs:
- Flow: Pulse triggered on success.
- Error Flow: Pulse triggered if the operation fails.
- Data: The content read.

---

### File Position

**Version**: `2.1.0`

Retrieves the current byte offset of the file pointer.

Useful for tracking progress or saving locations for future Seek operations 
within a file provider scope.

Inputs:
- Flow: Trigger the position check.

Outputs:
- Flow: Pulse triggered on success.
- Error Flow: Pulse triggered if retrieval fails.
- Position: The current integer byte offset.

---

### File Read

**Version**: `2.1.0`

Reads data from an open file using an active FILE provider.

This node retrieves content from the file associated with the current provider 
session. It progresses the file pointer by the number of bytes read.

Inputs:
- Flow: Trigger the read operation.
- Size: Number of bytes/characters to read (-1 for until EOF).

Outputs:
- Flow: Pulse triggered on successful read.
- Error Flow: Pulse triggered if the read fails or no provider is active.
- Data: The resulting content (String or Bytes).

---

### File Write

**Version**: `2.1.0`

Writes data to an open file via an active FILE provider.

This node commits content to the file at the current pointer position. 
It is designed to work within a File Provider scope to handle persistent 
file handles across a logic sequence.

Inputs:
- Flow: Trigger the write operation.
- Data: The content to write (String or Bytes).

Outputs:
- Flow: Pulse triggered on successful write.
- Error Flow: Pulse triggered if the operation fails.

---

[Back to Node Index](Index.md)
