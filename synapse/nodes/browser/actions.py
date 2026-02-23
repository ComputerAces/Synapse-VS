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
        self.properties["Wait Until"] = "load"
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
        wait = kwargs.get("Wait Until") or self.properties.get("Wait Until", "load")
        timeout = int(Timeout) if Timeout is not None else int(self.properties.get("Timeout", 30000))

        handle_id = self.get_provider_id("Browser Provider")
        handle = self.bridge.get(f"{handle_id}_Handle") if handle_id else None

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
        handle = self.bridge.get(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle/Provider found.")
        
        try:
            if use_points:
                px = X if X is not None else 0
                py = Y if Y is not None else 0
                handle.page.mouse.click(px, py)
                self.logger.info(f"Clicked point ({px}, {py})")
            elif sel:
                # Try smarter selector if needed
                handle.page.click(sel)
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
        handle = self.bridge.get(f"{handle_id}_Handle") if handle_id else None
        
        if not handle or not isinstance(handle, BrowserHandle):
             raise RuntimeError(f"[{self.name}] No active Browser Handle/Provider found.")
             
        if not sel:
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True

        try:
            handle.page.fill(sel, txt)
        except Exception as e:
            self.logger.error(f"Browser Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
