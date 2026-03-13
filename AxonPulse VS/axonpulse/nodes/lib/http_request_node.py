import requests

import asyncio

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.data import DataBuffer

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

aiohttp = None

HAS_AIOHTTP = False

def ensure_aiohttp():
    global aiohttp, HAS_AIOHTTP
    if aiohttp:
        return True
    if DependencyManager.ensure('aiohttp'):
        import aiohttp as _a
        aiohttp = _a
        HAS_AIOHTTP = True
        return True
    return False

@axon_node(category="Network/Requests", version="2.3.0", node_label="HTTP Request", outputs=['Response', 'Status', 'Text'])
def HTTPRequestNode(Headers: dict, Body: Any, URL: str = '', Method: str = 'GET', Proxy: str = '', BaseURL: str = '', Timeout: float = 30, _bridge: Any = None, _node: Any = None, _node_id: str = None) -> Any:
    """Executes a standard HTTP request (GET, POST, PUT, DELETE, etc.).
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
- Text: The response body as a string."""
    import requests
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    resp = requests.request(method, url, headers=headers, data=data, timeout=timeout, proxies=proxies)
    buf = DataBuffer(resp.content)
    return {'Response': buf, 'Status': resp.status_code, 'Text': resp.text}
