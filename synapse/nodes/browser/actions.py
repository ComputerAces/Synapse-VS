from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .provider import BrowserHandle

@NodeRegistry.register("Browser Navigate", "Browser")
class BrowserNavigateNode(SuperNode):
    """
    Directs the active browser page to a specific URL.
    Supports configurable wait conditions to ensure the page has loaded.
    
    Inputs:
    - Flow: Trigger the navigation.
    - URL: The destination web address (e.g., 'https://google.com').
    - Wait Until: Condition to wait for ('load', 'domcontentloaded', 'networkidle', or 'commit').
    - Timeout: Maximum time (in milliseconds) to wait for navigation.
    
    Outputs:
    - Flow: Triggered after navigation is complete or fails.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Wait Until"] = "networkidle"
        self.properties["Timeout"] = 30000
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "URL": DataType.STRING,
            "Wait Until": DataType.STRING,
            "Timeout": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, URL=None, Timeout=None, **kwargs):
        url = URL or self.properties.get("URL", "about:blank")
        wait = kwargs.get("Wait Until") or self.properties.get("Wait Until", "networkidle")
        timeout = int(Timeout) if Timeout is not None else int(self.properties.get("Timeout", 30000))

        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None

        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle/Provider found.")

        try:
            handle.page.goto(url, wait_until=wait, timeout=timeout)
        except Exception as e:
            self.logger.error(f"Browser Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Click", "Browser")
class BrowserClickNode(SuperNode):
    """
    Performs a click action on a specific element or coordinate within the browser page.
    Requires a valid selector or explicit X/Y coordinates.
    
    Inputs:
    - Flow: Trigger the click action.
    - Selector: CSS or XPath selector for the target element.
    - Use Points: If True, uses X and Y coordinates instead of a selector.
    - X, Y: Pixel coordinates for the click (relative to page).
    
    Outputs:
    - Flow: Triggered after the click attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING,
            "Use Points": DataType.BOOLEAN,
            "X": DataType.INTEGER,
            "Y": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, Selector=None, X=None, Y=None, **kwargs):
        use_points = kwargs.get("Use Points", False)
        sel = Selector or self.properties.get("Selector", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle/Provider found.")
        
        try:
            if use_points:
                px = X if X is not None else 0
                py = Y if Y is not None else 0
                handle.page.mouse.click(px, py)
                self.logger.info(f"Clicked point ({px}, {py})")
            elif sel:
                # [MAGIC FIND INTEGRATION]
                handle.magic_find(sel, True) # True triggers Click
            else:
                self.logger.warning("No selector or point provided for click.")
        except Exception as e:
            self.logger.error(f"Browser Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Type", "Browser")
class BrowserTypeNode(SuperNode):
    """
    Inputs text into a specified form field or element.
    Uses the Playwright 'fill' method for efficient typing.
    
    Inputs:
    - Flow: Trigger the typing action.
    - Selector: CSS or XPath selector for the input field.
    - Text: The string to be typed into the field.
    
    Outputs:
    - Flow: Triggered after the text has been filled.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, Selector=None, Text=None, **kwargs):
        sel = Selector or self.properties.get("Selector", "")
        txt = Text or self.properties.get("Text", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle/Provider found.")
             
        if not sel:
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True

        try:
            # [MAGIC FIND INTEGRATION]
            handle.magic_find(sel, txt) # String triggers Type/Fill
        except Exception as e:
            self.logger.error(f"Browser Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Get Tab List", "Browser")
class BrowserGetTabListNode(SuperNode):
    """
    Retrieves a list of all currently open tabs/pages in the browser.
    
    ### Inputs:
    - Flow (flow): Trigger the retrieval.

    ### Outputs:
    - Flow (flow): Pulse triggered after retrieval.
    - Names (list): List of page titles.
    - URLs (list): List of page URLs.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = { "Flow": DataType.FLOW }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Names": DataType.LIST,
            "URLs": DataType.LIST
        }

    def do_work(self, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        # Sync local list with actual context pages
        handle.pages = handle.context.pages
        
        names = [p.title() for p in handle.pages]
        urls = [p.url for p in handle.pages]
        
        self.set_output("Names", names)
        self.set_output("URLs", urls)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Open Tab", "Browser")
class BrowserOpenTabNode(SuperNode):
    """
    Opens a new browser tab and optionally navigates to a URL.
    
    ### Inputs:
    - Flow (flow): Trigger to open the tab.
    - URL (string): Optional web address to navigate to.
    
    ### Outputs:
    - Flow (flow): Triggered after the tab is opened.
    - Tab Index (integer): The index of the newly created tab.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "URL": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Tab Index": DataType.INTEGER
        }

    def do_work(self, URL=None, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        new_page = handle.context.new_page()
        if URL:
            new_page.goto(URL)
            
        handle.pages = handle.context.pages
        new_index = len(handle.pages) - 1
        handle.active_page_index = new_index
        
        self.set_output("Tab Index", new_index)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Select Tab", "Browser")
class BrowserSelectTabNode(SuperNode):
    """
    Switches the focus to a specific browser tab by its index.
    
    ### Inputs:
    - Flow (flow): Trigger the switch.
    - Index (integer): The numerical index of the tab to select (0-based).
    
    ### Outputs:
    - Flow (flow): Triggered after the switch attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Index": DataType.INTEGER
        }
        self.output_schema = { "Flow": DataType.FLOW }

    def do_work(self, Index=0, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        handle.pages = handle.context.pages
        if not handle.switch_page(int(Index)):
            self.logger.warning(f"Failed to switch to tab index {Index}. Staying on {handle.active_page_index}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Close Tab", "Browser")
class BrowserCloseTabNode(SuperNode):
    """
    Closes the currently active browser tab.
    
    ### Inputs:
    - Flow (flow): Trigger to close the active tab.

    ### Outputs:
    - Flow (flow): Triggered after the tab is closed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = { "Flow": DataType.FLOW }
        self.output_schema = { "Flow": DataType.FLOW }

    def do_work(self, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        if handle.page:
            handle.page.close()
            handle.pages = handle.context.pages
            if handle.active_page_index >= len(handle.pages):
                handle.active_page_index = max(0, len(handle.pages) - 1)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Strip Data", "Browser")
class BrowserStripDataNode(SuperNode):
    """
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
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Mode"] = "Text"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Count": DataType.INTEGER
        }

    def do_work(self, Selector=None, **kwargs):
        sel = Selector if Selector is not None else self.properties.get("Selector", "")
        if not sel or str(sel).strip() == "" or str(sel).strip() == "/":
            sel = "body *" # Default to all elements in body if empty or slash
            
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        try:
            js_script = """
            (selector) => {
                const elements = Array.from(document.querySelectorAll(selector));
                
                let results = {};
                for (let el of elements) {
                    const tag = el.tagName.toLowerCase();
                    if (['script', 'style', 'meta', 'link', 'noscript'].includes(tag)) continue;
                    
                    let textContent = el.innerText || el.value || '';
                    let hasId = !!el.id;
                    let hasClass = !!el.className;
                    let isInteractive = ['input', 'textarea', 'select', 'button', 'a', 'form'].includes(tag);
                    
                    if (selector === 'body *') {
                        if (!hasId && !hasClass && !textContent.trim() && !isInteractive) {
                            continue;
                        }
                    }

                    const getPath = (n) => {
                        let path = [];
                        while (n.nodeType === Node.ELEMENT_NODE) {
                            let sel = n.nodeName.toLowerCase();
                            // Do not use ID as the root fallback since we want the hierarchical path
                            if (n.id) {
                                sel += '#' + n.id;
                            }
                            let sib = n, nth = 1;
                            while (sib = sib.previousElementSibling) {
                                if (sib.nodeName.toLowerCase() === sel.split('#')[0]) nth++;
                            }
                            if (nth !== 1) sel += "[" + nth + "]";
                            
                            path.unshift(sel);
                            n = n.parentNode;
                        }
                        return path.join('.');
                    };
                    
                    let path = getPath(el);
                    
                    let data = {
                        tag: tag,
                        id: el.id || '',
                        class: el.className || '',
                        text: textContent
                    };
                    
                    // Dynamically map all attributes
                    if (el.attributes) {
                        for (let attr of el.attributes) {
                            if (attr.name !== 'id' && attr.name !== 'class') {
                                data[attr.name] = attr.value || '';
                            }
                        }
                    }
                    
                    // Clean up empty attributes
                    for (let key in data) {
                        try {
                            if (data[key] === '' || data[key] === null || data[key] === undefined) {
                                delete data[key];
                            } else {
                                // Ensure strict string type to avoid SVGAnimatedString objects
                                data[key] = String(data[key]);
                            }
                        } catch(e) {}
                    }
                    
                    results[path] = data;
                }
                return JSON.stringify(results);
            }
            """
            
            json_results = handle.page.evaluate(js_script, sel)
            import json
            results = json.loads(json_results)
            
            self.set_output("Count", len(results.keys()))
            self.set_output("Data", results) # Always returns a single JSON Object (dictionary)

        except Exception as e:
            self.logger.error(f"Extraction Error: {e}")
            self.set_output("Data", {})
            self.set_output("Count", 0)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Wait for Element", "Browser")
class BrowserWaitNode(SuperNode):
    """
    Pauses execution until a specific element appears on the page.
    
    ### Inputs:
    - Flow (flow): Start waiting.
    - Selector (string): CSS/XPath selector of the element.
    - State (string): Condition ('attached', 'detached', 'visible', 'hidden').
    - Timeout (number): Max wait time in ms.
    
    ### Outputs:
    - Flow (flow): Triggered when condition is met or timeout occurs.
    - Found (boolean): Boolean indicating if the element was found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["State"] = "visible"
        self.properties["Timeout"] = 30000
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING,
            "State": DataType.STRING,
            "Timeout": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Found": DataType.BOOLEAN
        }

    def do_work(self, Selector=None, State=None, Timeout=None, **kwargs):
        sel = Selector or self.properties.get("Selector", "")
        state = State or self.properties.get("State", "visible")
        timeout = int(Timeout) if Timeout is not None else int(self.properties.get("Timeout", 30000))
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        found = False
        try:
            found = handle.magic.wait_for(sel, state=state, timeout=timeout)
        except Exception as e:
            self.logger.warning(f"Wait for element '{sel}' failed: {e}")

        self.set_output("Found", found)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Scroll", "Browser")
class BrowserScrollNode(SuperNode):
    """
    Scrolls the page by a specific amount or to an element.
    
    ### Inputs:
    - Flow (flow): Trigger scroll.
    - Selector (string): Optional element to scroll into view.
    - X (integer): Pixel amount to scroll horizontally.
    - Y (integer): Pixel amount to scroll vertically.
    
    ### Outputs:
    - Flow (flow): Triggered after scroll attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING,
            "X": DataType.INTEGER,
            "Y": DataType.INTEGER
        }
        self.output_schema = { "Flow": DataType.FLOW }

    def do_work(self, Selector=None, X=None, Y=None, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        try:
            if Selector:
                handle.page.locator(Selector).scroll_into_view_if_needed()
            else:
                handle.page.mouse.wheel(X or 0, Y or 0)
        except Exception as e:
            self.logger.error(f"Scroll Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Hover", "Browser")
class BrowserHoverNode(SuperNode):
    """
    Moves the mouse hover over a specific element.
    
    ### Inputs:
    - Flow (flow): Trigger hover.
    - Selector (string): Element to hover on.
    
    ### Outputs:
    - Flow (flow): Triggered after hover attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Selector": DataType.STRING
        }
        self.output_schema = { "Flow": DataType.FLOW }

    def do_work(self, Selector=None, **kwargs):
        sel = Selector or self.properties.get("Selector", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        try:
            if sel:
                handle.page.hover(sel)
        except Exception as e:
            self.logger.error(f"Hover Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Close", "Browser")
class BrowserCloseNode(SuperNode):
    """
    Closes the entire browser instance associated with the provider.
    
    Inputs:
    - Flow: Trigger to close the browser.
    
    Outputs:
    - Flow: Triggered after the browser is shut down.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = { "Flow": DataType.FLOW }
        self.output_schema = { "Flow": DataType.FLOW }

    def do_work(self, **kwargs):
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        try:
            self.logger.info(f"Closing browser instance for provider: {handle_id}")
            handle.close()
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Magic Find", "Browser")
class BrowserMagicFindNode(SuperNode):
    """
    Experimental context-aware resolution node.
    Finds elements by dot-notation, text, or fuzzy matching and returns their path/data.
    
    ### Inputs:
    - Flow (flow): Trigger execution.
    - Target (string): Smart string (e.g., 'search', '*.button', 'login.email').
    
    ### Outputs:
    - Flow (flow): Triggered after discovery.
    - Path (string): The resolved XPath or identifier.
    - Data (any): The current value or text of the element.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Target": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING,
            "Data": DataType.ANY
        }

    def do_work(self, Target=None, **kwargs):
        target = Target or self.properties.get("Target", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        result = handle.magic_find(target, None) # Read mode
        
        if result:
            self.set_output("Path", result.get("path"))
            self.set_output("Data", result.get("data"))
        else:
            self.set_output("Path", None)
            self.set_output("Data", None)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Text Value", "Browser")
class BrowserTextValueNode(SuperNode):
    """
    Extracts purely the text or inner value of a single element using Magic Find.
    
    ### Inputs:
    - Flow (flow): Trigger extraction.
    - Target (string): Smart string to find the element (e.g., 'search', '#header').
    
    ### Outputs:
    - Flow (flow): Triggered after discovery.
    - Text (string): The extracted text or value of the element.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Target"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Target": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }

    def do_work(self, Target=None, **kwargs):
        target = Target or self.properties.get("Target", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        result = handle.magic_find(target, None) # Read mode
        
        if result and "data" in result:
            self.set_output("Text", result["data"])
        else:
            self.set_output("Text", "")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Data Search", "Browser")
class BrowserDataSearchNode(SuperNode):
    """
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
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["XPath"] = ""
        self.properties["Value"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "XPath": DataType.STRING,
            "Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Found": DataType.BOOLEAN,
            "Value": DataType.STRING,
            "Path": DataType.STRING
        }

    def do_work(self, XPath=None, Value=None, **kwargs):
        xpath = XPath or self.properties.get("XPath", "")
        value = Value or self.properties.get("Value", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        found_element = None
        
        # 1. Resolve by XPath if provided
        if xpath:
            sel = xpath if ("xpath=" in xpath or "/" not in xpath) else f"xpath={xpath}"
            try:
                elements = handle.page.query_selector_all(sel)
                # Try to find visible first
                for el in elements:
                    if el.is_visible():
                        found_element = el
                        break
                if not found_element and elements:
                    found_element = elements[0]
            except: pass
            
            # If Value is also provided, we verify the match
            if found_element and value:
                actual_val = found_element.evaluate("el => el.value || el.innerText || ''")
                if value.lower() not in actual_val.lower():
                    found_element = None
        
        # 2. Resolve by Value only if XPath wasn't provided
        elif value:
            try:
                loc = handle.page.locator(f"text='{value}'").first
                if loc.count() > 0:
                    found_element = loc.element_handle()
            except: pass

        if found_element:
            js_xpath = """
            (el) => {
                let path = "";
                for (; el && el.nodeType == 1; el = el.parentNode) {
                    let index = 1;
                    for (let sib = el.previousSibling; sib; sib = sib.previousSibling) {
                        if (sib.nodeType == 1 && sib.tagName == el.tagName) index++;
                    }
                    let tagName = el.tagName.toLowerCase();
                    path = "/" + tagName + "[" + index + "]" + path;
                }
                return path;
            }
            """
            actual_xpath = found_element.evaluate(js_xpath)
            actual_value = found_element.evaluate("el => el.value || el.innerText || ''")
            
            self.set_output("Found", True)
            self.set_output("Value", actual_value)
            self.set_output("Path", actual_xpath)
        else:
            self.set_output("Found", False)
            self.set_output("Value", "")
            self.set_output("Path", "")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Browser Element Visible", "Browser")
class BrowserElementVisibleNode(SuperNode):
    """
    Checks if a specific element is currently visible on the page.
    Supports XPath or Smart Search strings.
    
    Inputs:
    - Flow: Trigger check.
    - Path: XPath or Smart Search string.
    
    Outputs:
    - Flow: Triggered after check.
    - Visible: True if the element exists and is visible.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Visible": DataType.BOOLEAN
        }

    def do_work(self, Path=None, **kwargs):
        path = Path or self.properties.get("Path", "")
        
        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get_object(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle found.")

        result = handle.magic_find(path, None) # Read mode returns metadata
        
        visible = False
        if result and result.get("visible"):
            visible = True
            
        self.set_output("Visible", visible)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
