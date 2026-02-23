import requests
import asyncio
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.data import DataBuffer
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
aiohttp = None
HAS_AIOHTTP = False

def ensure_aiohttp():
    global aiohttp, HAS_AIOHTTP
    if aiohttp: return True
    if DependencyManager.ensure("aiohttp"):
        import aiohttp as _a; aiohttp = _a; HAS_AIOHTTP = True; return True
    return False

@NodeRegistry.register("HTTP Request", "Network/Requests")
class HTTPRequestNode(SuperNode):
    """
    Executes a standard HTTP request (GET, POST, PUT, DELETE, etc.).
    Supports synchronous and asynchronous execution, custom headers, and proxies.
    
    Inputs:
    - Flow: Trigger the request.
    - URL: The target endpoint.
    - Method: HTTP verb to use.
    - Headers: Optional dictionary of HTTP headers.
    - Body: The request payload.
    - Proxy: Optional proxy URL.
    - BaseURL: Optional base URL for relative path requests.
    
    Outputs:
    - Flow: Triggered after the response is received.
    - Response: The raw response data (DataBuffer).
    - Status: The HTTP status code (e.g., 200, 404).
    - Text: The response body as a string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = False 
        self.is_async = True 
        
        self.properties["Method"] = "GET"
        self.properties["URL"] = ""
        self.properties["Timeout"] = 30
        self.properties["BaseURL"] = ""
        self.properties["Proxy"] = ""
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "URL": DataType.STRING,
            "Method": DataType.STRING,
            "Headers": DataType.DICT,
            "Body": DataType.ANY,
            "Proxy": DataType.STRING,
            "BaseURL": DataType.STRING,
            "Timeout": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Response": DataType.ANY,
            "Status": DataType.INT,
            "Text": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_request)

    async def handle_request(self, URL=None, Method=None, Headers=None, Body=None, Proxy=None, BaseURL=None, Timeout=None, **kwargs):
        ensure_aiohttp()
        
        # Resolve Base URL
        base_url = BaseURL if BaseURL is not None else self.properties.get("BaseURL", self.properties.get("BaseUrl", ""))
        if not base_url:
            provider_id = self.get_provider_id("Network Provider")
            if provider_id:
                base_url = self.bridge.get(f"{provider_id}_Base URL")
                
        # Resolve Proxy
        proxy = Proxy if Proxy is not None else self.properties.get("Proxy", self.properties.get("Proxy", ""))
        if not proxy:
             provider_id = self.get_provider_id("Network Provider")
             if provider_id:
                 proxy = self.bridge.get(f"{provider_id}_Proxy")
                 
        # Resolve Default Headers
        headers = Headers if isinstance(Headers, dict) else {}
        provider_id = self.get_provider_id("Network Provider")
        if provider_id:
            default_headers = self.bridge.get(f"{provider_id}_Headers")
            if default_headers:
                # Merge
                merged = default_headers.copy()
                merged.update(headers)
                headers = merged

        url = URL if URL is not None else self.properties.get("URL", self.properties.get("Url", ""))
        if base_url and url and not url.startswith("http"):
             url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
             
        if not url:
            self.logger.warning("No URL provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        method = (Method if Method is not None else self.properties.get("Method", self.properties.get("Method", "GET"))).upper()
        timeout = float(Timeout if Timeout is not None else self.properties.get("Timeout", 30))
        
        data = Body
        if isinstance(Body, DataBuffer):
            data = Body.get_raw()

        try:
            if HAS_AIOHTTP:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, headers=headers, data=data, timeout=timeout, proxy=proxy) as resp:
                        status = resp.status
                        raw_body = await resp.read()
                        text_body = ""
                        try:
                            text_body = raw_body.decode("utf-8")
                        except: pass

                        buf = DataBuffer(raw_body)
                        self.bridge.set(f"{self.node_id}_Response", buf, self.name)
                        self.bridge.set(f"{self.node_id}_Status", status, self.name)
                        self.bridge.set(f"{self.node_id}_Text", text_body, self.name)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: self._sync_request(method, url, headers, data, timeout, proxy))

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            
        except Exception as e:
            self.logger.error(f"HTTP Error: {e}")
            self.bridge.set(f"{self.node_id}_Status", 0, self.name)
            self.bridge.set(f"{self.node_id}_Text", str(e), self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            
        return True

    def _sync_request(self, method, url, headers, data, timeout, proxy):
        import requests
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.request(method, url, headers=headers, data=data, timeout=timeout, proxies=proxies)
        buf = DataBuffer(resp.content)
        self.bridge.set(f"{self.node_id}_Response", buf, self.name)
        self.bridge.set(f"{self.node_id}_Status", resp.status_code, self.name)
        self.bridge.set(f"{self.node_id}_Text", resp.text, self.name)
