# 🧩 Connectivity Nodes

This document covers nodes within the **Connectivity** core category.

## 📂 Actions

### Net Listener

**Version**: `2.1.0`

Establishes an event listener on the active Network Provider to capture incoming messages.
Triggers the graph sequence whenever new data is received.

Inputs:
- Flow: Initialize the listener.
- App ID: Optional identifier for isolation/authentication.

Outputs:
- Flow: Triggered every time a new message is received.
- Message: The incoming data payload.

---

### Net Request

**Version**: `2.1.0`

Executes a high-level network request using the active Network Provider context.
Supports RESTful APIs and basic gRPC stub calls with identity-based authentication.

Inputs:
- Flow: Trigger the network request.
- Method: The HTTP method to use (GET, POST, etc.).
- Endpoint: The specific API path relative to the Base URL.
- Payload: The data to send (Dictionary for JSON, or raw string/bytes).
- App ID: Optional identifier for retrieving authentication credentials.

Outputs:
- Flow: Triggered after the request completes.
- Error Flow: Triggered if the request fails (network error, timeout).
- Response: The raw text or data returned by the server.
- Status: The numeric HTTP status code (e.g., 200, 404).

---

### Net Stream

**Version**: `2.1.0`

Pushes data messages through an established streaming connection in the active Network Provider context.

Inputs:
- Flow: Trigger the message push.
- Message: The data or object to transmit through the stream.

Outputs:
- Flow: Triggered after the message is sent.
- Error Flow: Triggered if the transmission fails.

---

## 📂 MCP

### MCP Client

**Version**: `2.1.0`

Connects to a Model Context Protocol (MCP) server.
Supports stdio and SSE transports. Lists available tools upon connection.

Inputs:
- Flow: Trigger the connection.
- Config: Server configuration dictionary.
- Enabled: Toggles the client state.

Outputs:
- Flow: Triggered after connection attempt.
- Status: Connection status message.
- Tools: List of tool names provided by the server.

---

### MCP Resource

**Version**: `2.1.0`

Reads a resource from a connected MCP server using a URI.
Returns the resource content and its associated MIME type.

Inputs:
- Flow: Trigger the resource read.
- Server: The name of the target MCP server.
- URI: The unique identifier for the resource.

Outputs:
- Flow: Triggered after resource read.
- Content: The resource data.
- MimeType: The detected MIME type of the resource.
- Error: Error message if the read failed.

---

### MCP Tool

**Version**: `2.1.0`

Calls a specific tool on a connected MCP server.
Passes arguments and returns the raw output or error message.

Inputs:
- Flow: Trigger the tool call.
- Server: The name of the target MCP server.
- Tool: The name of the tool to execute.
- Args: Dictionary of arguments for the tool.

Outputs:
- Flow: Triggered after the tool execution.
- Result: The response from the tool.
- Error: Error message if the call failed.

---

## 📂 Providers

### GRPC Provider

**Version**: `2.1.0`

Initializes a gRPC connection handle for high-performance RPC communication.
Sets up the target server address for protocol buffer-based requests.

Inputs:
- Flow: Trigger the creation of the connection handle.
- Server: The target host and port (e.g., 'localhost:50051').

Outputs:
- Flow: Triggered after handle creation.
- Handle: A ConnectionHandle object containing the gRPC configuration.

---

### REST Provider

**Version**: `2.1.0`

Initializes a REST-based connection handle for communicating with web APIs.
Acts as a configuration provider for Net Request and other connectivity nodes.

Inputs:
- Flow: Trigger the creation of the connection handle.
- Base URL: The root URL for the target API (e.g., 'https://api.example.com').
- Port: The destination port for the connection.
- Timeout: Request timeout in seconds.
- AuthStrategy: The authentication method to use (e.g., 'Bearer').

Outputs:
- Flow: Triggered after handle creation.
- Handle: A ConnectionHandle object containing the REST configuration.

---

### WebSocket Provider

**Version**: `2.1.0`

Initializes a WebSocket connection handle for real-time bi-directional communication.
Supports automatic reconnection settings and standard WSS protocols.

Inputs:
- Flow: Trigger the creation of the connection handle.
- URL: The full WSS endpoint URL (e.g., 'wss://echo.websocket.org').
- Reconnect: Toggles automatic reconnection on connection loss.

Outputs:
- Flow: Triggered after handle creation.
- Handle: A ConnectionHandle object containing the WebSocket configuration.

---

[Back to Node Index](Index.md)
