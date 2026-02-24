"""
PortRegistry — Ephemeral UUID-based port identity system (v2.5.0).

Assigns stable UUIDs to ports at graph load time. UUIDs are NEVER persisted
to .syp files — they exist only as a background linking system for data routing.

Usage:
    registry = PortRegistry()
    uuid = registry.register("node-abc", "Last Image", "output", node_name="Camera")
    key  = registry.bridge_key("node-abc", "Last Image", "output")
    name = registry.resolve(uuid)  # → "Camera.Last Image"
"""
import uuid as _uuid
from synapse.utils.logger import setup_logger

logger = setup_logger("PortRegistry")


class PortRegistry:
    """
    Central registry mapping (node_id, port_name, direction) ↔ UUID.
    
    Created once per ExecutionEngine instance. Not shared across engines
    (SubGraph child engines get their own registry).
    """
    def __init__(self):
        self._ports = {}    # uuid_str → {node_id, port_name, direction, node_name}
        self._lookup = {}   # (node_id, port_name_lower, direction) → uuid_str

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, node_id, port_name, direction="output", node_name=""):
        """
        Register a port and return its UUID.  Idempotent — calling with
        the same (node_id, port_name, direction) returns the existing UUID.
        
        Args:
            node_id:   The owning node's unique ID.
            port_name: Human-readable port name (e.g. "Last Image").
            direction: "input" or "output".
            node_name: Optional human-readable node name for error messages.
        
        Returns:
            The UUID string assigned to this port.
        """
        key = (str(node_id), port_name.lower(), direction)
        existing = self._lookup.get(key)
        if existing:
            return existing

        uid = str(_uuid.uuid4())
        self._ports[uid] = {
            "node_id": str(node_id),
            "port_name": port_name,
            "direction": direction,
            "node_name": node_name or str(node_id),
        }
        self._lookup[key] = uid
        return uid

    def register_node_ports(self, node):
        """
        Bulk-register all input and output ports for a node instance.
        Reads from node.input_types / node.output_types (set by define_schema).
        """
        node_id = str(node.node_id)
        node_name = node.name

        for port_name in getattr(node, "input_types", {}):
            self.register(node_id, port_name, "input", node_name)

        for port_name in getattr(node, "output_types", {}):
            self.register(node_id, port_name, "output", node_name)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------
    def get_uuid(self, node_id, port_name, direction="output"):
        """
        Look up the UUID for a known port.  Returns None if not registered.
        """
        key = (str(node_id), port_name.lower(), direction)
        return self._lookup.get(key)

    def bridge_key(self, node_id, port_name, direction="output"):
        """
        Returns the UUID to use as a bridge key for this port.
        If the port isn't registered yet, registers it on the fly.
        
        This is the primary method used by _gather_inputs and set_output.
        """
        uid = self.get_uuid(node_id, port_name, direction)
        if uid is None:
            uid = self.register(node_id, port_name, direction)
        return uid

    def resolve(self, uid):
        """
        Resolve a UUID to a human-readable string for error/log messages.
        Returns "NodeName.PortName" or the raw UUID if not found.
        """
        info = self._ports.get(uid)
        if info:
            return f"{info['node_name']}.{info['port_name']}"
        return uid

    def resolve_key(self, bridge_key):
        """
        Resolve a bridge key (which is a UUID) to readable form.
        Falls back to the raw key if it's a legacy name-based key.
        """
        info = self._ports.get(bridge_key)
        if info:
            return f"{info['node_name']}.{info['port_name']}"
        return bridge_key

    # ------------------------------------------------------------------
    # Legacy Compatibility
    # ------------------------------------------------------------------
    def legacy_key(self, node_id, port_name):
        """
        Returns the old-style bridge key: "{node_id}_{port_name}".
        Used for backward compatibility fallback in _gather_inputs.
        """
        return f"{node_id}_{port_name}"
