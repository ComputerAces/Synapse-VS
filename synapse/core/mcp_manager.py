import asyncio
import threading
import logging
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

logger = logging.getLogger("MCP-Manager")

class McpManager:
    """
    Manages MCP Client sessions in a dedicated asyncio thread.
    Bridge between synchronous Synapse Nodes and async MCP SDK.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = McpManager()
        return cls._instance

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {} # server_name -> session
        self.exit_stack: Dict[str, Any] = {} # Store exit stacks to close connections
        
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True, name="MCP-Async-Loop")
        self.thread.start()
        logger.info("MCP Manager started")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect_stdio(self, name: str, command: str, args: List[str] = [], env: Dict = None) -> bool:
        """Connect to a local StdIO MCP server."""
        if name in self.sessions:
            logger.warning(f"MCP Server {name} already connected.")
            return True
            
        future = asyncio.run_coroutine_threadsafe(self._connect_stdio_async(name, command, args, env), self.loop)
        try:
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Failed to connect to {name}: {e}")
            return False

    async def _connect_stdio_async(self, name: str, command: str, args: List[str], env: Dict):
        from contextlib import AsyncExitStack
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        stack = AsyncExitStack()
        # We must keep the stack alive
        try:
            stdio_transport = await stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            
            self.sessions[name] = session
            self.exit_stack[name] = stack # Keep context alive
            logger.info(f"Connected to MCP Server: {name}")
            return True
        except Exception as e:
            logger.error(f"Async Connect Error: {e}")
            await stack.aclose()
            raise e

    def connect_sse(self, name: str, url: str) -> bool:
        """Connect to a remote SSE MCP server."""
        if name in self.sessions: return True
        future = asyncio.run_coroutine_threadsafe(self._connect_sse_async(name, url), self.loop)
        try: return future.result(timeout=10)
        except Exception: return False

    async def _connect_sse_async(self, name: str, url: str):
        from contextlib import AsyncExitStack
        stack = AsyncExitStack()
        try:
            sse_transport = await stack.enter_async_context(sse_client(url))
            read, write = sse_transport
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            self.sessions[name] = session
            self.exit_stack[name] = stack
            return True
        except Exception as e:
            await stack.aclose()
            raise e

    def list_tools(self, name: str) -> List[Any]:
        if name not in self.sessions: return []
        future = asyncio.run_coroutine_threadsafe(self._list_tools_async(name), self.loop)
        return future.result(timeout=5)

    async def _list_tools_async(self, name: str):
        session = self.sessions[name]
        result = await session.list_tools()
        return result.tools

    def call_tool(self, name: str, tool_name: str, arguments: Dict) -> Any:
        if name not in self.sessions: raise ValueError(f"Server {name} not found")
        future = asyncio.run_coroutine_threadsafe(self._call_tool_async(name, tool_name, arguments), self.loop)
        return future.result(timeout=30) # Tools might take longer

    async def _call_tool_async(self, name: str, tool_name: str, arguments: Dict):
        session = self.sessions[name]
        result = await session.call_tool(tool_name, arguments)
        return result

    def read_resource(self, name: str, uri: str) -> Any:
        if name not in self.sessions: raise ValueError(f"Server {name} not found")
        future = asyncio.run_coroutine_threadsafe(self._read_resource_async(name, uri), self.loop)
        return future.result(timeout=10)
        
    async def _read_resource_async(self, name: str, uri: str):
        session = self.sessions[name]
        result = await session.read_resource(uri)
        return result

    def disconnect(self, name: str):
        if name in self.exit_stack:
            future = asyncio.run_coroutine_threadsafe(self.exit_stack[name].aclose(), self.loop)
            try: future.result(timeout=2)
            except: pass
            del self.sessions[name]
            del self.exit_stack[name]
