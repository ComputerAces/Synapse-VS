from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from .provider import BrowserHandle

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Browser", version="2.3.0", node_label="Browser Navigate")
def BrowserNavigateNode(URL: str, Wait_Until: str = 'networkidle', Timeout: float = 30000, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Directs the active browser page to a specific URL.
Supports configurable wait conditions to ensure the page has loaded.

Inputs:
- Flow: Trigger the navigation.
- URL: The destination web address (e.g., 'https://google.com').
- Wait Until: Condition to wait for ('load', 'domcontentloaded', 'networkidle', or 'commit').
- Timeout: Maximum time (in milliseconds) to wait for navigation.

Outputs:
- Flow: Triggered after navigation is complete or fails."""
    url = URL if URL is not None else _node.properties.get('URL', 'about:blank')
    wait = kwargs.get('Wait Until') if kwargs.get('Wait Until') is not None else _node.properties.get('Wait Until', 'networkidle')
    timeout = int(Timeout) if Timeout is not None else int(_node.properties.get('Timeout', 30000))
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle/Provider found.')
    else:
        pass
    try:
        handle.page.goto(url, wait_until=wait, timeout=timeout)
    except Exception as e:
        _node.logger.error(f'Browser Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Click")
def BrowserClickNode(Selector: str, Use_Points: bool, X: float, Y: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a click action on a specific element or coordinate within the browser page.
Requires a valid selector or explicit X/Y coordinates.

Inputs:
- Flow: Trigger the click action.
- Selector: CSS or XPath selector for the target element.
- Use Points: If True, uses X and Y coordinates instead of a selector.
- X, Y: Pixel coordinates for the click (relative to page).

Outputs:
- Flow: Triggered after the click attempt."""
    use_points = kwargs.get('Use Points') if kwargs.get('Use Points') is not None else _node.properties.get('Use Points', False)
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle/Provider found.')
    else:
        pass
    try:
        if use_points:
            px = X if X is not None else 0
            py = Y if Y is not None else 0
            handle.page.mouse.click(px, py)
            _node.logger.info(f'Clicked point ({px}, {py})')
        elif sel:
            handle.magic_find(sel, True)
        else:
            _node.logger.warning('No selector or point provided for click.')
    except Exception as e:
        _node.logger.error(f'Browser Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Type")
def BrowserTypeNode(Selector: str, Text: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Inputs text into a specified form field or element.
Uses the Playwright 'fill' method for efficient typing.

Inputs:
- Flow: Trigger the typing action.
- Selector: CSS or XPath selector for the input field.
- Text: The string to be typed into the field.

Outputs:
- Flow: Triggered after the text has been filled."""
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    txt = Text if Text is not None else _node.properties.get('Text', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle/Provider found.')
    else:
        pass
    if not sel:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    try:
        handle.magic_find(sel, txt)
    except Exception as e:
        _node.logger.error(f'Browser Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Get Tab List", outputs=['Names', 'URLs'])
def BrowserGetTabListNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a list of all currently open tabs/pages in the browser.

### Inputs:
- Flow (flow): Trigger the retrieval.

### Outputs:
- Flow (flow): Pulse triggered after retrieval.
- Names (list): List of page titles.
- URLs (list): List of page URLs."""
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    handle.pages = handle.context.pages
    names = [p.title() for p in handle.pages]
    urls = [p.url for p in handle.pages]
    _node.set_output('Names', names)
    _node.set_output('URLs', urls)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Open Tab", outputs=['Tab Index'])
def BrowserOpenTabNode(URL: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Opens a new browser tab and optionally navigates to a URL.

### Inputs:
- Flow (flow): Trigger to open the tab.
- URL (string): Optional web address to navigate to.

### Outputs:
- Flow (flow): Triggered after the tab is opened.
- Tab Index (integer): The index of the newly created tab."""
    url = URL if URL is not None else _node.properties.get('URL', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    new_page = handle.context.new_page()
    if url:
        new_page.goto(url)
    else:
        pass
    handle.pages = handle.context.pages
    new_index = len(handle.pages) - 1
    handle.active_page_index = new_index
    _node.set_output('Tab Index', new_index)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Select Tab")
def BrowserSelectTabNode(Index: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Switches the focus to a specific browser tab by its index.

### Inputs:
- Flow (flow): Trigger the switch.
- Index (integer): The numerical index of the tab to select (0-based).

### Outputs:
- Flow (flow): Triggered after the switch attempt."""
    target_index = Index if Index is not None else _node.properties.get('Index', 0)
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    handle.pages = handle.context.pages
    if not handle.switch_page(int(target_index)):
        _node.logger.warning(f'Failed to switch to tab index {target_index}. Staying on {handle.active_page_index}')
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Close Tab")
def BrowserCloseTabNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Closes the currently active browser tab.

### Inputs:
- Flow (flow): Trigger to close the active tab.

### Outputs:
- Flow (flow): Triggered after the tab is closed."""
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    if handle.page:
        handle.page.close()
        handle.pages = handle.context.pages
        if handle.active_page_index >= len(handle.pages):
            handle.active_page_index = max(0, len(handle.pages) - 1)
        else:
            pass
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Strip Data", outputs=['Data', 'Count'])
def BrowserStripDataNode(Selector: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts text, HTML, or attributes from elements on the page.

### Inputs:
- Flow (flow): Trigger extraction.
- Selector (string): CSS/XPath selector (e.g., 'h1', '.price').
- Mode (string): Extraction mode ('Text', 'HTML', 'Attribute', 'Count').
- Attribute (string): Name of the attribute to extract (if in 'Attribute' mode).

### Outputs:
- Flow (flow): Triggered after extraction.
- Data (any): The extracted string or list of strings.
- Count (integer): Number of elements found."""
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    if not sel or str(sel).strip() == '' or str(sel).strip() == '/':
        sel = 'body *'
    else:
        pass
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        js_script = '\n            (selector) => {\n                const resolveTarget = (sel) => {\n                    if (!sel) return null;\n                    if (sel.startsWith(\'/\') || sel.startsWith(\'//\')) {\n                        return document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;\n                    }\n                    // Handle Magic Path (dot-notation)\n                    if (/^[\\w\\-]+(?:\\[\\d+\\])?(?:\\.[\\w\\-]+(?:\\[\\d+\\])?)*$/.test(sel)) {\n                         let parts = sel.split(\'.\');\n                         let curr = document;\n                         for (let p of parts) {\n                             if (!curr) break;\n                             let match = p.match(/^([\\w\\-]+)(?:\\[(\\d+)\\])?$/);\n                             if (match) {\n                                 let tag = match[1];\n                                 let idx = parseInt(match[2] || "1");\n                                 let children = Array.from(curr === document ? [document.documentElement] : curr.children)\n                                                   .filter(c => c.tagName.toLowerCase() === tag);\n                                 curr = children[idx - 1];\n                             } else {\n                                 curr = curr.querySelector(p);\n                             }\n                         }\n                         if (curr) return curr;\n                    }\n                    // Fallback to CSS\n                    try { return document.querySelector(sel); } catch(e) { return null; }\n                };\n\n                let targetEl = resolveTarget(selector);\n                if (!targetEl) return JSON.stringify({error: "Element not found"});\n\n                const el = targetEl;\n                const tag = el.tagName.toLowerCase();\n                \n                let data = {\n                    tag: tag,\n                    id: el.id || \'\',\n                    class: el.className || \'\',\n                    text: el.innerText || el.textContent || \'\',\n                    value: el.value || \'\',\n                    innerHTML: el.innerHTML || \'\',\n                    outerHTML: el.outerHTML || \'\',\n                    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)\n                };\n                \n                // Merge all attributes\n                if (el.attributes) {\n                    for (let attr of el.attributes) {\n                        data[attr.name] = String(attr.value);\n                    }\n                }\n                \n                return JSON.stringify(data);\n            }\n            '
        json_results = handle.page.evaluate(js_script, sel)
        import json
        results = json.loads(json_results)
        if 'error' in results:
            _node.logger.warning(f"Browser Strip Data: {results['error']} for selector '{sel}'")
            _node.set_output('Data', {})
            _node.set_output('Count', 0)
        else:
            _node.set_output('Count', 1)
            _node.set_output('Data', results)
    except Exception as e:
        _node.logger.error(f'Extraction Error: {e}')
        _node.set_output('Data', {})
        _node.set_output('Count', 0)
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Strip Elements", outputs=['Data', 'Count'])
def BrowserStripElementsNode(Element_Type: str = 'div', Include_Children: bool = True, Wait_Until: str = 'load', Timeout: float = 30000, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts all elements of a specific type (e.g., 'table', 'tr', 'div') and returns 
their full XPaths and inner text as a dictionary.

### Inputs:
- Flow (flow): Trigger the extraction.
- Element Type (string): The HTML tag name to look for (e.g., 'table', 'li', 'a').
- Include Children (boolean): If True, recursively extracts all descendants of found elements.
- Wait Until (string): Optional wait condition ('load', 'domcontentloaded', 'networkidle').
- Timeout (number): Max time (ms) to wait for condition.

### Outputs:
- Flow (flow): Triggered after extraction.
- Data (list): A list of hierarchical paths (dot-notation).
- Count (integer): Number of elements found."""
    element_type = kwargs.get('Element Type') if kwargs.get('Element Type') is not None else _node.properties.get('Element Type', 'div')
    include_children = kwargs.get('Include Children') if kwargs.get('Include Children') is not None else _node.properties.get('Include Children', True)
    wait = kwargs.get('Wait Until') if kwargs.get('Wait Until') is not None else _node.properties.get('Wait Until', 'load')
    timeout = int(kwargs.get('Timeout')) if kwargs.get('Timeout') is not None else int(_node.properties.get('Timeout', 30000))
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        if wait and wait.lower() != 'none' and (wait.strip() != ''):
            try:
                handle.page.wait_for_load_state(wait, timeout=timeout)
            except Exception as e:
                _node.logger.warning(f"Wait for load state '{wait}' timed out or failed: {e}")
            finally:
                pass
        else:
            pass
        js_script = '\n            (tag, includeChildren) => {\n                const rootElements = Array.from(document.querySelectorAll(tag));\n                let paths = [];\n\n                const getPath = (el) => {\n                    let path = [];\n                    let n = el;\n                    while (n && n.nodeType === Node.ELEMENT_NODE) {\n                        let t = n.nodeName.toLowerCase();\n                        let sib = n, nth = 1;\n                        while (sib = sib.previousElementSibling) {\n                            if (sib.nodeName.toLowerCase() === t) nth++;\n                        }\n                        if (nth !== 1) t += "[" + nth + "]";\n                        path.unshift(t);\n                        n = n.parentNode;\n                    }\n                    return path.join(\'.\');\n                };\n\n                const collect = (el) => {\n                    try {\n                        let p = getPath(el);\n                        if (p && !paths.includes(p)) {\n                            paths.push(p);\n                        }\n                    } catch(e) {}\n                    \n                    if (includeChildren) {\n                        Array.from(el.children).forEach(child => collect(child));\n                    }\n                };\n\n                rootElements.forEach(root => collect(root));\n                return JSON.stringify(paths);\n            }\n            '
        json_results = handle.page.evaluate(js_script, [element_type, include_children])
        import json
        paths = json.loads(json_results)
        if isinstance(paths, list):
            paths = [str(p) for p in paths]
        else:
            paths = []
        _node.set_output('Data', paths)
        _node.set_output('Count', len(paths))
    except Exception as e:
        _node.logger.error(f'Extraction Error: {e}')
        _node.set_output('Data', [])
        _node.set_output('Count', 0)
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Element Attributes", outputs=['Attributes'])
def BrowserElementAttributesNode(Selector: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Returns all attributes of a specific element as a dictionary.

### Inputs:
- Flow (flow): Trigger the action.
- Selector (string): Target element path/selector.

### Outputs:
- Flow (flow): Triggered after extraction.
- Attributes (any): Dictionary of {name: value}."""
    sel = kwargs.get('Selector') or _node.properties.get('Selector')
    if not sel:
        raise ValueError(f'[{_node.name}] Selector is required.')
    else:
        pass
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        js_script = '\n            (selector) => {\n                const resolveTarget = (sel) => {\n                    if (!sel) return null;\n                    if (sel.startsWith(\'/\') || sel.startsWith(\'//\')) {\n                        return document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;\n                    }\n                    // Handle Magic Path (dot-notation)\n                    if (/^[\\w\\-]+(?:\\[\\d+\\])?(?:\\.[\\w\\-]+(?:\\[\\d+\\])?)*$/.test(sel)) {\n                         let parts = sel.split(\'.\');\n                         let curr = document;\n                         for (let p of parts) {\n                             if (!curr) break;\n                             let match = p.match(/^([\\w\\-]+)(?:\\[(\\d+)\\])?$/);\n                             if (match) {\n                                 let tag = match[1];\n                                 let idx = parseInt(match[2] || "1");\n                                 let children = Array.from(curr === document ? [document.documentElement] : curr.children)\n                                                   .filter(c => c.tagName.toLowerCase() === tag);\n                                 curr = children[idx - 1];\n                             } else {\n                                 curr = curr.querySelector(p);\n                             }\n                         }\n                         if (curr) return curr;\n                    }\n                    try { return document.querySelector(sel); } catch(e) { return null; }\n                };\n\n                const el = resolveTarget(selector);\n                if (!el) return JSON.stringify({error: "Not found"});\n\n                let attrs = {};\n                if (el.attributes) {\n                    for (let attr of el.attributes) {\n                        attrs[attr.name] = String(attr.value);\n                    }\n                }\n                return JSON.stringify(attrs);\n            }\n            '
        json_results = handle.page.evaluate(js_script, sel)
        import json
        results = json.loads(json_results)
        if 'error' in results:
            _node.set_output('Attributes', {})
        else:
            _node.set_output('Attributes', results)
    except Exception as e:
        _node.logger.error(f'Attributes Error: {e}')
        _node.set_output('Attributes', {})
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Wait for Element", outputs=['Found'])
def BrowserWaitNode(Selector: str, State: str = 'visible', Timeout: float = 30000, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Pauses execution until a specific element appears on the page.

### Inputs:
- Flow (flow): Start waiting.
- Selector (string): CSS/XPath selector of the element.
- State (string): Condition ('attached', 'detached', 'visible', 'hidden').
- Timeout (number): Max wait time in ms.

### Outputs:
- Flow (flow): Triggered when condition is met or timeout occurs.
- Found (boolean): Boolean indicating if the element was found."""
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    state = State if State is not None else _node.properties.get('State', 'visible')
    timeout = int(Timeout) if Timeout is not None else int(_node.properties.get('Timeout', 30000))
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    found = False
    try:
        found = handle.magic.wait_for(sel, state=state, timeout=timeout)
    except Exception as e:
        _node.logger.warning(f"Wait for element '{sel}' failed: {e}")
    finally:
        pass
    _node.set_output('Found', found)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Scroll")
def BrowserScrollNode(Selector: str, X: float, Y: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Scrolls the page by a specific amount or to an element.

### Inputs:
- Flow (flow): Trigger scroll.
- Selector (string): Optional element to scroll into view.
- X (integer): Pixel amount to scroll horizontally.
- Y (integer): Pixel amount to scroll vertically.

### Outputs:
- Flow (flow): Triggered after scroll attempt."""
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    px = X if X is not None else _node.properties.get('X', 0)
    py = Y if Y is not None else _node.properties.get('Y', 0)
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        if sel:
            handle.page.locator(sel).scroll_into_view_if_needed()
        else:
            handle.page.mouse.wheel(px or 0, py or 0)
    except Exception as e:
        _node.logger.error(f'Scroll Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Hover")
def BrowserHoverNode(Selector: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Moves the mouse hover over a specific element.

### Inputs:
- Flow (flow): Trigger hover.
- Selector (string): Element to hover on.

### Outputs:
- Flow (flow): Triggered after hover attempt."""
    sel = Selector if Selector is not None else _node.properties.get('Selector', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        if sel:
            handle.page.hover(sel)
        else:
            pass
    except Exception as e:
        _node.logger.error(f'Hover Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Close")
def BrowserCloseNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Closes the entire browser instance associated with the provider.

Inputs:
- Flow: Trigger to close the browser.

Outputs:
- Flow: Triggered after the browser is shut down."""
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    try:
        _node.logger.info(f'Closing browser instance for provider: {handle_id}')
        handle.close()
    except Exception as e:
        _node.logger.error(f'Error closing browser: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Magic Find", outputs=['Path', 'Data'])
def BrowserMagicFindNode(Target: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Experimental context-aware resolution node.
Finds elements by dot-notation, text, or fuzzy matching and returns their path/data.

### Inputs:
- Flow (flow): Trigger execution.
- Target (string): Smart string (e.g., 'search', '*.button', 'login.email').

### Outputs:
- Flow (flow): Triggered after discovery.
- Path (string): The resolved XPath or identifier.
- Data (any): The current value or text of the element."""
    target = Target if Target is not None else _node.properties.get('Target', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    result = handle.magic_find(target, None)
    if result:
        _node.set_output('Path', result.get('path'))
        _node.set_output('Data', result.get('data'))
    else:
        _node.set_output('Path', None)
        _node.set_output('Data', None)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Text Value", outputs=['Text'])
def BrowserTextValueNode(Target: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts purely the text or inner value of a single element using Magic Find.

### Inputs:
- Flow (flow): Trigger extraction.
- Target (string): Smart string to find the element (e.g., 'search', '#header').

### Outputs:
- Flow (flow): Triggered after discovery.
- Text (string): The extracted text or value of the element."""
    target = Target or _node.properties.get('Target', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    result = handle.magic_find(target, None)
    if result and 'data' in result:
        _node.set_output('Text', result['data'])
    else:
        _node.set_output('Text', '')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Data Search", outputs=['Found', 'Found Value', 'Path'])
def BrowserDataSearchNode(XPath: str = '', Value: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Locates an element by XPath, Value, or both.
If both are provided, both must match.

Inputs:
- Flow: Trigger search.
- XPath: Formal XPath selector.
- Value: Text content or value to match.

Outputs:
- Flow: Triggered after search.
- Value: The actual text or value of the element.
- Path: The formal XPath of the resolved element."""
    xpath = XPath or _node.properties.get('XPath', '')
    value = Value or _node.properties.get('Value', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    found_element = None
    if xpath:
        sel = xpath if 'xpath=' in xpath or '/' not in xpath else f'xpath={xpath}'
        try:
            elements = handle.page.query_selector_all(sel)
            for el in elements:
                if el.is_visible():
                    found_element = el
                    break
                else:
                    pass
            if not found_element and elements:
                found_element = elements[0]
            else:
                pass
        except:
            pass
        finally:
            pass
        if found_element and value:
            actual_val = found_element.evaluate("el => el.value || el.innerText || ''")
            if value.lower() not in actual_val.lower():
                found_element = None
            else:
                pass
        else:
            pass
    elif value:
        try:
            loc = handle.page.locator(f"text='{value}'").first
            if loc.count() > 0:
                found_element = loc.element_handle()
            else:
                pass
        except:
            pass
        finally:
            pass
    else:
        pass
    if found_element:
        js_xpath = '\n            (el) => {\n                let path = "";\n                for (; el && el.nodeType == 1; el = el.parentNode) {\n                    let index = 1;\n                    for (let sib = el.previousSibling; sib; sib = sib.previousSibling) {\n                        if (sib.nodeType == 1 && sib.tagName == el.tagName) index++;\n                    }\n                    let tagName = el.tagName.toLowerCase();\n                    path = "/" + tagName + "[" + index + "]" + path;\n                }\n                return path;\n            }\n            '
        actual_xpath = found_element.evaluate(js_xpath)
        actual_value = found_element.evaluate("el => el.value || el.innerText || ''")
        _node.set_output('Found', True)
        _node.set_output('Found Value', actual_value)
        _node.set_output('Path', actual_xpath)
    else:
        _node.set_output('Found', False)
        _node.set_output('Found Value', '')
        _node.set_output('Path', '')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Browser", version="2.3.0", node_label="Browser Element Visible", outputs=['Visible'])
def BrowserElementVisibleNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Checks if a specific element is currently visible on the page.
Supports XPath or Smart Search strings.

Inputs:
- Flow: Trigger check.
- Path: XPath or Smart Search string.

Outputs:
- Flow: Triggered after check.
- Visible: True if the element exists and is visible."""
    path = Path or _node.properties.get('Path', '')
    handle_id = self.get_provider_id('Browser Provider')
    handle = _bridge.get_object(f'{handle_id}_Handle') if handle_id else None
    if not handle or not isinstance(handle, BrowserHandle):
        raise RuntimeError(f'[{_node.name}] No active Browser Handle found.')
    else:
        pass
    result = handle.magic_find(path, None)
    visible = False
    if result and result.get('visible'):
        visible = True
    else:
        pass
    _node.set_output('Visible', visible)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
