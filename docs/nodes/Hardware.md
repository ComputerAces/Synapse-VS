# 🔌 Hardware & IoT

Nodes for communicating with external devices and sensors.

## Nodes

### MQTT Client

**Version**: 2.0.2
**Description**: Publishes or subscribes to MQTT topics.

Communicates with an MQTT broker registered by an 'MQTT Provider'. 
Supports publishing text payloads to specific topics.

Inputs:
- Flow: Trigger the action.
- Broker: Optional override for the broker address.
- Topic: The target topic to interact with.
- Message: The payload to publish.
- Port: Connection port (if not using provider defaults).
- Action: The operation to perform ('Publish', 'Subscribe').

Outputs:
- Flow: Pulse triggered after action completion.

### MQTT Provider

**Version**: 2.0.2
**Description**: Registers the MQTT broker connection for the graph session.

Initializes a provider context with broker address and port, allowing 
'MQTT Client' nodes to communicate with the broker without manual 
configuration for each node.

Inputs:
- Flow: Trigger the provider initialization.
- Broker: The MQTT broker hostname or IP address.
- Port: The broker's connection port (default 1883).

Outputs:
- Done: Pulse triggered once the provider settings are registered.

### Resource Monitor

**Version**: 2.0.2
**Description**: Background service that periodically captures system performance metrics.
Monitors CPU, RAM, and primary drive usage on a fixed interval.

Inputs:
- Flow: Start the monitoring service.

Outputs:
- Tick: Pulse triggered on every monitoring interval update.
- CPU Usage: Current CPU utilization percentage.
- RAM Usage: Current RAM utilization percentage.
- Disk Usage: Current primary drive utilization percentage.

### Serial Port

**Version**: 2.0.2
**Description**: Sends and receives data over a serial port.
Can discover port settings automatically if nested within a Serial Provider.

Inputs:
- Flow: Trigger the serial transaction.
- Port: The serial port to use (optional if provider is present).
- Message: The string data to send to the device.
- Baud Rate: The communication speed.

Outputs:
- Flow: Pulse triggered after the transaction completes.
- Response: The string data received back from the serial device.

### Serial Provider

**Version**: 2.0.2
**Description**: Establishes a Serial communication context (COM port/Baud rate).
Registers serial settings in the bridge for downstream Serial Port nodes.

Inputs:
- Flow: Start the Serial provider.
- Port: The hardware port identifier (e.g., 'COM3', '/dev/ttyUSB0').
- Baud Rate: The communication speed (default: 9600).

Outputs:
- Flow: Pulse triggered after the scope successfully closes.
- Provider Flow: Active pulse for nodes within this serial context.
- Provider: A dictionary containing the established port settings.

---
[Back to Nodes Index](Index.md)
