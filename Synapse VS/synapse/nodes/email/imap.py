import imaplib
import email
import threading
import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("IMAP Listener", "Network/Email")
class IMAPListenerNode(SuperNode):
    """
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
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.is_service = True
        self.properties["Port"] = 993
        self.properties["Folder"] = "INBOX"
        self._running = False
        self._thread = None
        
        self.define_schema()
        self.register_handler("Flow", self.start_listener)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Host": DataType.STRING,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "Filter": DataType.STRING,
            "Port": DataType.NUMBER,
            "Folder": DataType.STRING
        }
        self.output_schema = {
            "New Email": DataType.FLOW,
            "Subject": DataType.STRING,
            "Sender": DataType.STRING,
            "Body": DataType.STRING
        }

    def start_listener(self, Host=None, User=None, Password=None, Filter=None, Port=None, Folder=None, **kwargs):
        # Fallback to properties
        Host = Host or self.properties.get("Host")
        User = User or self.properties.get("User")
        Filter = Filter or self.properties.get("Filter") or "UNSEEN"
        Port = Port if Port is not None else self.properties.get("Port", 993)
        Folder = Folder or self.properties.get("Folder", "INBOX")
        
        # Provider Lookup
        if not Host:
            provider_id = self.get_provider_id("Email Provider")
            if provider_id:
                Host = Host or self.bridge.get(f"{provider_id}_Host")
                User = User or self.bridge.get(f"{provider_id}_User")
                Password = Password or self.bridge.get(f"{provider_id}_Password")

        if self._running: 
            return 
            
        if not Host or not User or not Password: 
            self.logger.error("Missing Host, User, or Password.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll, args=(Host, User, Password, Filter), daemon=True)
        self._thread.start()

    def _poll(self, host, user, password, criteria):
        last_check = set()
        while self._running:
            try:
                mail = imaplib.IMAP4_SSL(host)
                mail.login(user, password)
                mail.select(self.properties.get("Folder", "INBOX"))
                
                status, messages = mail.search(None, criteria)
                if status == "OK":
                    msg_ids = messages[0].split()
                    for num in msg_ids:
                        if num in last_check: continue 
                        last_check.add(num)
                        
                        status, data = mail.fetch(num, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = msg["subject"]
                                sender = msg["from"]
                                body = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == "text/plain":
                                            body = part.get_payload(decode=True).decode()
                                            break
                                else:
                                    body = msg.get_payload(decode=True).decode()

                                self.bridge.set(f"{self.node_id}_Subject", subject, self.name)
                                self.bridge.set(f"{self.node_id}_Sender", sender, self.name)
                                self.bridge.set(f"{self.node_id}_Body", body[:100], self.name)
                                
                                self.bridge.set(f"_TRIGGER_FIRE_{self.node_id}", True, self.name)
                mail.close()
                mail.logout()
            except Exception as e:
                self.logger.error(f"IMAP Error: {e}")
            
            # Simple sleep to check stop signal
            for _ in range(10): 
                if not self._running: break
                time.sleep(1)

    def terminate(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        super().terminate()
