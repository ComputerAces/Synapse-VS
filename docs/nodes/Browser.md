# 🧩 Browser Nodes

This document covers nodes within the **Browser** core category.

## 📂 General

### Browser Click

**Version**: `2.1.0`

Performs a click action on a specific element or coordinate within the browser page.
Requires a valid selector or explicit X/Y coordinates.

Inputs:
- Flow: Trigger the click action.
- Selector: CSS or XPath selector for the target element.
- Use Points: If True, uses X and Y coordinates instead of a selector.
- X, Y: Pixel coordinates for the click (relative to page).

Outputs:
- Flow: Triggered after the click attempt.

---

### Browser Close

**Version**: `2.1.0`

Closes the entire browser instance associated with the provider.

Inputs:
- Flow: Trigger to close the browser.

Outputs:
- Flow: Triggered after the browser is shut down.

---

### Browser Close Tab

**Version**: `2.1.0`

Closes the currently active browser tab.

### Inputs:
- Flow (flow): Trigger to close the active tab.

### Outputs:
- Flow (flow): Triggered after the tab is closed.

---

### Browser Data Search

**Version**: `2.1.0`

Locates an element by XPath, Value, or both.
If both are provided, both must match.

Inputs:
- Flow: Trigger search.
- XPath: Formal XPath selector.
- Value: Text content or value to match.

Outputs:
- Flow: Triggered after search.
- Found: True if a match was found.
- Value: The actual text or value of the element.
- Path: The formal XPath of the resolved element.

---

### Browser Element Visible

**Version**: `2.1.0`

Checks if a specific element is currently visible on the page.
Supports XPath or Smart Search strings.

Inputs:
- Flow: Trigger check.
- Path: XPath or Smart Search string.

Outputs:
- Flow: Triggered after check.
- Visible: True if the element exists and is visible.

---

### Browser Get Tab List

**Version**: `2.1.0`

Retrieves a list of all currently open tabs/pages in the browser.

### Inputs:
- Flow (flow): Trigger the retrieval.

### Outputs:
- Flow (flow): Pulse triggered after retrieval.
- Names (list): List of page titles.
- URLs (list): List of page URLs.

---

### Browser Hover

**Version**: `2.1.0`

Moves the mouse hover over a specific element.

### Inputs:
- Flow (flow): Trigger hover.
- Selector (string): Element to hover on.

### Outputs:
- Flow (flow): Triggered after hover attempt.

---

### Browser Magic Find

**Version**: `2.1.0`

Experimental context-aware resolution node.
Finds elements by dot-notation, text, or fuzzy matching and returns their path/data.

### Inputs:
- Flow (flow): Trigger execution.
- Target (string): Smart string (e.g., 'search', '*.button', 'login.email').

### Outputs:
- Flow (flow): Triggered after discovery.
- Path (string): The resolved XPath or identifier.
- Data (any): The current value or text of the element.

---

### Browser Navigate

**Version**: `2.1.0`

Directs the active browser page to a specific URL.
Supports configurable wait conditions to ensure the page has loaded.

Inputs:
- Flow: Trigger the navigation.
- URL: The destination web address (e.g., 'https://google.com').
- Wait Until: Condition to wait for ('load', 'domcontentloaded', 'networkidle', or 'commit').
- Timeout: Maximum time (in milliseconds) to wait for navigation.

Outputs:
- Flow: Triggered after navigation is complete or fails.

---

### Browser Open Tab

**Version**: `2.1.0`

Opens a new browser tab and optionally navigates to a URL.

### Inputs:
- Flow (flow): Trigger to open the tab.
- URL (string): Optional web address to navigate to.

### Outputs:
- Flow (flow): Triggered after the tab is opened.
- Tab Index (integer): The index of the newly created tab.

---

### Browser Provider

**Version**: `2.1.0`

Launches and manages a headless or windowed web browser instance (Chromium, Firefox, WebKit).
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

---

### Browser Scroll

**Version**: `2.1.0`

Scrolls the page by a specific amount or to an element.

### Inputs:
- Flow (flow): Trigger scroll.
- Selector (string): Optional element to scroll into view.
- X (integer): Pixel amount to scroll horizontally.
- Y (integer): Pixel amount to scroll vertically.

### Outputs:
- Flow (flow): Triggered after scroll attempt.

---

### Browser Select Tab

**Version**: `2.1.0`

Switches the focus to a specific browser tab by its index.

### Inputs:
- Flow (flow): Trigger the switch.
- Index (integer): The numerical index of the tab to select (0-based).

### Outputs:
- Flow (flow): Triggered after the switch attempt.

---

### Browser Strip Data

**Version**: `2.1.0`

Extracts text, HTML, or attributes from elements on the page.

### Inputs:
- Flow (flow): Trigger extraction.
- Selector (string): CSS/XPath selector (e.g., 'h1', '.price').
- Mode (string): Extraction mode ('Text', 'HTML', 'Attribute', 'Count').
- Attribute (string): Name of the attribute to extract (if in 'Attribute' mode).

### Outputs:
- Flow (flow): Triggered after extraction.
- Data (any): The extracted string or list of strings.
- Count (integer): Number of elements found.

---

### Browser Text Value

**Version**: `2.1.0`

Extracts purely the text or inner value of a single element using Magic Find.

### Inputs:
- Flow (flow): Trigger extraction.
- Target (string): Smart string to find the element (e.g., 'search', '#header').

### Outputs:
- Flow (flow): Triggered after discovery.
- Text (string): The extracted text or value of the element.

---

### Browser Type

**Version**: `2.1.0`

Inputs text into a specified form field or element.
Uses the Playwright 'fill' method for efficient typing.

Inputs:
- Flow: Trigger the typing action.
- Selector: CSS or XPath selector for the input field.
- Text: The string to be typed into the field.

Outputs:
- Flow: Triggered after the text has been filled.

---

### Browser Wait for Element

**Version**: `2.1.0`

Pauses execution until a specific element appears on the page.

### Inputs:
- Flow (flow): Start waiting.
- Selector (string): CSS/XPath selector of the element.
- State (string): Condition ('attached', 'detached', 'visible', 'hidden').
- Timeout (number): Max wait time in ms.

### Outputs:
- Flow (flow): Triggered when condition is met or timeout occurs.
- Found (boolean): Boolean indicating if the element was found.

---

[Back to Node Index](Index.md)
