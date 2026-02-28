# 🧩 Network Nodes

This document covers nodes within the **Network** core category.

## 📂 Email

### Email Provider

**Version**: `2.1.0`

Provides SMTP server configuration for sending emails.

Inputs:
- Flow: Execution trigger.
- Host: SMTP server hostname (e.g., smtp.gmail.com).
- User: Username for authentication.
- Password: Password for authentication.
- Port: Connection port (default 465).

Outputs:
- Flow: Triggered when the provider is initialized.

---

### IMAP Listener

**Version**: `2.1.0`

Monitors an IMAP email account for new incoming messages.

This node runs as a background service, polling the specified folder 
(default: INBOX) for unread emails. When a new email matches the filter criteria, 
it triggers the 'New Email' flow and outputs message metadata.

Inputs:
- Flow: Start the monitoring service.
- Host: IMAP server address (e.g., imap.gmail.com).
- User: Email address or username.
- Password: Account password or app-specific password.
- Filter: IMAP search criteria (e.g., UNSEEN, FROM "boss@work.com").

Outputs:
- New Email: Pulse triggered for each matching message found.
- Subject: The subject line of the most recent email.
- Sender: The 'From' address of the email.
- Body: A snippet of the email's plain-text content.

---

### SMTP Sender

**Version**: `2.1.0`

Sends an email using the SMTP protocol.
Supports attachments, HTML/Plain text bodies, and SSL/TLS encryption.

Inputs:
- Flow: Trigger the email sending.
- Host: SMTP server address.
- User: Authentication username (usually the full email address).
- Password: Authentication password.
- To: Recipient email address.
- Subject: Email subject line.
- Body: Email message content.
- Attachments: List of file paths to attach.

Outputs:
- Success: Triggered if the email was sent successfully.
- Error: Triggered if the sending attempt failed.

---

## 📂 Ingress

### Flask Host

**Version**: `2.1.0`

HTTP Server Provider (Flask). Launches a local web server to handle incoming network requests.

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

---

### Flask Response

**Version**: `2.1.0`

Sends an HTTP response back to a client that triggered a 'Flask Route'.

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

---

### Flask Route

**Version**: `2.1.0`

Registers an HTTP endpoint (URL path) on an active Flask server.

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

---

## 📂 Providers

### Network Provider

**Version**: `2.1.0`

Service provider for base network configurations.
Registers global settings like Base URL and Proxy in a scope for child 
nodes like HTTP Request to discover and use.

Inputs:
- Flow: Start the network provider service and enter the configuration scope.
- Base URL: The default API endpoint prefix.
- Proxy: The proxy server URL for outgoing requests.
- Headers: A dictionary of default HTTP headers.

Outputs:
- Provider Flow: Active while the configuration scope is open.
- Flow: Triggered when the service is stopped.

---

## 📂 Requests

### HTTP Request

**Version**: `2.1.0`

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

---

## 📂 SFTP

### SFTP Transfer

**Version**: `2.1.0`

Performs file transfers using the SFTP protocol.
Supports both Upload and Download operations. Can automatically 
discover credentials if nested inside an SSH Provider scope.

Inputs:
- Flow: Trigger the file transfer.
- Host: Target hostname (Optional if using SSH Provider).
- User: Username (Optional if using SSH Provider).
- Password: Password (Optional if using SSH Provider).
- Local Path: The filesystem path on the local machine.
- Remote Path: The filesystem path on the remote server.

Outputs:
- Complete: Pulse triggered when the transfer finishes successfully.
- Progress: Pulse triggered during transfer updates.

---

## 📂 SSH

### SSH Command

**Version**: `2.1.0`

Executes a shell command on a remote server via SSH.
Supports authentication via password or private key files.

Inputs:
- Flow: Trigger the command execution.
- Host: Remote server address.
- User: SSH username.
- Password: SSH password.
- Key Path: Path to an optional RSA private key file.
- Command: The shell command to execute.

Outputs:
- Flow: Triggered after command execution.
- Stdout: Standard output from the command.
- Stderr: Standard error from the command.
- Exit Code: The process return code.

---

### SSH Provider

**Version**: `2.1.0`

Service provider for SSH (Secure Shell) connections.
Registers connection parameters in a scope for child nodes like 
SSH Command and SFTP Transfer to discover and use.

Inputs:
- Flow: Start the SSH provider service and enter the connection scope.
- Host: The remote hostname or IP address (default: 127.0.0.1).
- Port: The SSH port (default: 22).
- User: The username for authentication.
- Password: The password for authentication.
- Key Path: Path to a private key file for key-based authentication.

Outputs:
- Provider Flow: Active while the connection scope is open.
- Flow: Triggered when the service is stopped.

---

## 📂 Scrapers

### HTML Parser

**Version**: `2.1.0`

Parses HTML content and extracts data using CSS Selectors.

This node takes an HTML string and applies a CSS selector (e.g., 'a', '.title', 
'#content') to find matching elements, returning their stripped text content 
as a list.

Inputs:
- Flow: Trigger the parsing process.
- HTML String: The raw HTML content to parse.
- Selector: CSS Selector string for targeting elements.

Outputs:
- Flow: Triggered after parsing completes.
- Text List: List of extracted text strings from matching elements.

---

## 📂 Sockets

### SocketIO Client Provider

**Version**: `2.1.0`

Connects to a remote SocketIO server.

Inputs:
- Flow: Establish connection and enter scope.
- URL: The server URL (Default: http://127.0.0.1:5000).

Outputs:
- Provider Flow: Active while connected.

---

### SocketIO Emit

**Version**: `2.1.0`

Emits an event to the active SocketIO Provider.

Inputs:
- Flow: Trigger emission.
- Event: The event name.
- Body: The data payload.

Outputs:
- Flow: Triggered after the event is emitted.

---

### SocketIO On Event

**Version**: `2.1.0`

Listens for a specific event on the active SocketIO Provider.

Inputs:
- Flow: Start the event watch.
- Stop: Stop the event watch and finish.
- Event: The event name to listen for.

Outputs:
- On Event: Pulse triggered when message received.
- Received Data: The data payload.
- Flow: Triggered when the service stops.

---

### SocketIO Room

**Version**: `2.1.0`

Manages client participation in SocketIO rooms.
Requires a SocketIO Server Provider.

Inputs:
- Flow: Trigger management.
- SID: Client session ID.
- Room: Room name.
- Action: 'Join' or 'Leave' (Default: Join).

Outputs:
- Flow: Triggered after the room action is performed.

---

### SocketIO Server Provider

**Version**: `2.1.0`

Hosts a SocketIO server. Can attach to an existing Flask Host.

Inputs:
- Flow: Start the server and enter scope.
- Provider End: Pulse to close scope.
- Host: (Optional) The address to bind to if standalone.
- Port: (Optional) The port to bind to if standalone (Default: 5000).

Outputs:
- Provider Flow: Active while the server is running.
- Provider ID: Unique ID for this provider.

---

## 📂 TCP

### TCP Client Provider

**Version**: `2.1.0`

Connects to a remote TCP server and provides the connection to child nodes.

Inputs:
- Flow: Establish connection and enter scope.
- Host: Server address.
- Port: Server port.

Outputs:
- Provider Flow: Active while connected.

---

### TCP Receive

**Version**: `2.1.0`

Receives data from an active TCP Provider context.

Inputs:
- Flow: Trigger receive.
- Buffer Size: Max bytes to read (Default: 4096).

Outputs:
- Flow: Pulse triggered after receiving.
- Body: The received data.

---

### TCP Send

**Version**: `2.1.0`

Sends data through an active TCP Provider context.

Inputs:
- Flow: Trigger send.
- Body: Data to send (String or Bytes).

Outputs:
- Flow: Triggered after the data is sent.

---

### TCP Server Provider

**Version**: `2.1.0`

Hosts a TCP server and provides connection handles to child nodes.

Inputs:
- Flow: Start the server and enter scope.
- Provider End: Pulse to close scope.
- Host: Interface to bind to (Default: 127.0.0.1).
- Port: Port to listen on (Default: 6000).

Outputs:
- Provider Flow: Active while the server is running.
- Provider ID: Unique ID for this provider.
- On Connection: Pulse triggered for each new client connection.
- Client Info: Address of the connected client.

---

[Back to Node Index](Index.md)
