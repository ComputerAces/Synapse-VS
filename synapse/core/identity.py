class IdentityObject:
    """
    Standardized Identity Contract for Synapse OS (SCIA).
    Stored in the Identity & Session Manager (ISM) and linked to an App ID.
    """
    def __init__(self, uid=None, username="Anonymous", roles=None, origin="System"):
        self.uid = uid
        self.username = username
        self.roles = roles if roles else []
        self.auth_payload = {} # Scoped auth data (tokens, secrets)
        self.origin = origin   # Source of the identity (Web, CLI, etc.)

    def to_dict(self):
        return {
            "uid": self.uid,
            "username": self.username,
            "roles": self.roles,
            "auth_payload": self.auth_payload,
            "origin": self.origin
        }

    @classmethod
    def from_dict(cls, data):
        if not data: return None
        obj = cls(
            uid=data.get("uid"),
            username=data.get("username", "Anonymous"),
            roles=data.get("roles", []),
            origin=data.get("origin", "System")
        )
        obj.auth_payload = data.get("auth_payload", {})
        return obj
