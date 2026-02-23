# 🌐 Web & Internet

Nodes for interacting with web services, creating servers, and handling HTTP requests.

## Nodes

### Flask Host

**Version**: 2.0.2
**Description**: HTTP Server Provider (Flask). Launches a local web server to handle incoming network requests.

This node acts as a service provider, allowing other 'Flask Route' nodes to register endpoints 
within its scope. It is the foundation for creating local REST APIs, webhooks, or simple 
web interfaces directly within a Synapse graph.

Inputs:
- Flow: Trigger to start the server.
- Provider End: Signal to stop the server (Cleanup).
- Host: The address to bind to (e.g., '127.0.0.1' for local, '0.0.0.0' for all interfaces).
- Port: The TCP port to listen on (Default: 5000).

Outputs:
- Provider Flow: Active pulse while the server is running.
- Service ID: Unique identifier for this Flask service.
- Flow: Triggered after the server scope is closed.

### Flask Response

**Version**: 2.0.2
**Description**: Sends an HTTP response back to a client that triggered a 'Flask Route'.

This node completes the lifecycle of an HTTP request. It uses the 'Request ID' 
provided by the route node to ensure the response reaches the correct client.

Inputs:
- Flow: Trigger the response.
- Body: The content to send back (String/HTML/JSON).
- Status Code: The HTTP status code (e.g., 200, 404).
- Request ID: The token from the corresponding 'Flask Route' node.
- Content Type: The MIME type (e.g., 'text/html', 'application/json').

Outputs:
- Flow: Triggered after the response is sent to the bridge.

### Flask Route

**Version**: 2.0.2
**Description**: Registers an HTTP endpoint (URL path) on an active Flask server.

When an external request matches this route's path and method, the 'Trigger' pulse 
is fired. The graph then processes the request and MUST return a 'Flask Response' 
node to finish the transaction.

Inputs:
- Flow: Register the route with the provider.
- Service ID: Optional ID of the Flask Host.
- Path: The URL endpoint (e.g., '/api/data').
- Method: The HTTP method (GET, POST, etc.).

Outputs:
- Trigger: Pulse fired when a request is received.
- Query: Dictionary of URL query parameters.
- Body: The raw request body (Bytes).
- Request ID: Unique token used to map the response back to this request.

### HTTP Request

**Version**: 2.0.2
**Description**: Executes a standard HTTP request (GET, POST, PUT, DELETE, etc.).
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

---
[Back to Nodes Index](Index.md)
