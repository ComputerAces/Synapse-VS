# 🌐 Networking & Remote Ops

Nodes for low-level networking, remote server management, and protocol-specific automation.

## Nodes

### Email Provider

**Version**: 2.0.2
**Description**: Provides SMTP server configuration for sending emails.

Inputs:
- Flow: Execution trigger.
- Host: SMTP server hostname (e.g., smtp.gmail.com).
- User: Username for authentication.
- Password: Password for authentication.
- Port: Connection port (default 465).

Outputs:
- Flow: Triggered when the provider is initialized.

### GRPC Provider

**Version**: 2.0.2
**Description**: Initializes a gRPC connection handle for high-performance RPC communication.
Sets up the target server address for protocol buffer-based requests.

Inputs:
- Flow: Trigger the creation of the connection handle.
- Server: The target host and port (e.g., 'localhost:50051').

Outputs:
- Flow: Triggered after handle creation.
- Handle: A ConnectionHandle object containing the gRPC configuration.

### IMAP Listener

**Version**: 2.0.2
**Description**: Monitors an IMAP email account for new incoming messages.

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

### Network Provider

**Version**: 2.0.2
**Description**: Service provider for base network configurations.
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

### REST Provider

**Version**: 2.0.2
**Description**: Initializes a REST-based connection handle for communicating with web APIs.
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

### SMTP Sender

**Version**: 2.0.2
**Description**: Sends an email using the SMTP protocol.
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

### SSH Command

**Version**: 2.0.2
**Description**: Executes a shell command on a remote server via SSH.
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

### SSH Provider

**Version**: 2.0.2
**Description**: Service provider for SSH (Secure Shell) connections.
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

### WebSocket Provider

**Version**: 2.0.2
**Description**: Initializes a WebSocket connection handle for real-time bi-directional communication.
Supports automatic reconnection settings and standard WSS protocols.

Inputs:
- Flow: Trigger the creation of the connection handle.
- URL: The full WSS endpoint URL (e.g., 'wss://echo.websocket.org').
- Reconnect: Toggles automatic reconnection on connection loss.

Outputs:
- Flow: Triggered after handle creation.
- Handle: A ConnectionHandle object containing the WebSocket configuration.

---
[Back to Nodes Index](Index.md)
