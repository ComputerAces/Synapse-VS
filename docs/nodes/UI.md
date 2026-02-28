# 🧩 UI Nodes

This document covers nodes within the **UI** core category.

## 📂 Dialogs

### File Dialog

**Version**: `2.1.0`

Triggers a native operating system dialog for selecting files or folders.
Supports 'Open File', 'Save File', and 'Open Folder' modes across Windows, macOS, and Linux.

This node provides a bridge to the underlying host OS GUI, allowing users to select 
existing files for reading, define new file paths for saving, or choosing entire 
directories for batch operations.

Inputs:
- Flow: Execution trigger (Pulse).
- Mode: The dialog behavior (Open File, Save File, or Open Folder).
- Title: Custom text shown in the dialog window's header.
- Filter: Optional file extension filters (e.g., 'Text Files (*.txt), *.txt; *.csv').

Outputs:
- Flow: Pulse triggered if a valid path was selected.
- Cancelled: Pulse triggered if the user closed the window or clicked 'Cancel'.
- Path: The absolute path to the selected item.

---

## 📂 General

### Custom Form

**Version**: `2.1.0`

Renders a dynamic user interface form based on a matching schema.
Supports both GUI (via Bridge) and CLI rendering modes.

Inputs:
- Flow: Trigger the form display.
- Title: The window or header title for the form.
- Blocking: If True, execution waits until the user submits the form.
- Schema: A list of field definitions (label, type, default).

Outputs:
- Flow: Triggered after form submission (or immediately if non-blocking).
- Form Data: A dictionary containing the user's input values.

---

### Message Box

**Version**: `2.1.0`

Displays a modal message box to the user.

Supports various types (Infor, Warning, Error) and button configurations 
(OK, Yes/No, OK/Cancel). Can block execution until the user interacts 
with the dialog.

Inputs:
- Flow: Trigger the display.
- Title: The title of the message box window.
- Message: The text content to display.
- Type: The style of the box ('info', 'warning', 'error').
- Buttons: The button layout ('ok', 'yes_no', 'ok_cancel').
- Blocking: Whether to wait for user input (default True).

Outputs:
- Flow: Pulse triggered after closure (or immediately if non-blocking).
- Result: The button clicked by the user (e.g., 'ok', 'yes', 'no').

---

### Text Display

**Version**: `2.1.0`

Displays text content to the user in a dedicated window or console block.
Commonly used for showing long reports, logs, or multi-line data summaries.

Inputs:
- Flow: Trigger the display.
- Text: The string content to show.

Outputs:
- Flow: Pulse triggered after the window is closed or processed.

---

## 📂 Overlays

### Overlay Highlighter

**Version**: `2.1.0`

Spawns a temporary visual highlight on the screen at specified coordinates.
Useful for guiding user attention or debugging UI element positions.

Inputs:
- Flow: Trigger the overlay display.
- Rect: The [x, y, w, h] coordinates for the highlight.
- Color: The [r, g, b, a] color of the highlight.

Outputs:
- Flow: Pulse triggered after the overlay thread starts.

---

## 📂 Toasts

### Toast

**Version**: `2.1.0`

Displays a system-native toast notification.
On Windows, this uses win11toast for rich notifications. On other 
platforms, it falls back to desktop-notifier.

Inputs:
- Flow: Trigger the notification.
- Title: The bold header text of the toast.
- Message: The main body text of the notification.

Outputs:
- Flow: Pulse triggered after the toast is sent.
- OnClick: Pulse triggered if the user clicks on the notification.

---

### Toast Input

**Version**: `2.1.0`

Displays a toast notification with a text input field (Windows only).
Falls back to a standard PyQt input dialog on non-Windows platforms.

Inputs:
- Flow: Trigger the interactive notification.
- Title: The title of the input request.
- Message: Instructions or prompt text for the user.
- Value: Default text to populate the input field.

Outputs:
- Flow: Pulse triggered after the user submits or closes the dialog.
- Text: The string content entered by the user.
- OnClick: Pulse triggered upon successful submission.

---

### Toast Media

**Version**: `2.1.0`

Displays a system-native toast notification with an attached image.
Ideal for alerts that require visual context, such as security 
camera triggers or status updates with icons.

Inputs:
- Flow: Trigger the notification.
- Title: The bold header text of the toast.
- Message: The main body text of the notification.
- Path: The absolute or relative path to the image file to display.

Outputs:
- Flow: Pulse triggered after the toast is sent.
- OnClick: Pulse triggered if the user clicks on the notification.

---

[Back to Node Index](Index.md)
