import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("SMTP Sender", "Network/Email")
class SMTPSenderNode(SuperNode):
    """
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
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Port"] = 465
        
        self.define_schema()
        self.register_handler("Flow", self.send_email)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Host": DataType.STRING,
            "Port": DataType.NUMBER,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "To": DataType.STRING,
            "Subject": DataType.STRING,
            "Body": DataType.STRING,
            "Attachments": DataType.LIST
        }
        self.output_schema = {
            "Success": DataType.FLOW,
            "Error": DataType.FLOW
        }

    def send_email(self, Host=None, User=None, Password=None, To=None, Subject=None, Body=None, Attachments=None, **kwargs):
        # Fallback to properties
        Host = Host or self.properties.get("Host") or self.properties.get("Host")
        User = User or self.properties.get("User") or self.properties.get("User")
        To = To or self.properties.get("To") or self.properties.get("To")
        Subject = Subject or self.properties.get("Subject") or self.properties.get("Subject")
        
        # Provider Lookup
        if not Host:
            provider_id = self.get_provider_id("Email Provider")
            if provider_id:
                Host = Host or self.bridge.get(f"{provider_id}_Host")
                User = User or self.bridge.get(f"{provider_id}_User")
                Password = Password or self.bridge.get(f"{provider_id}_Password")

        if not Host or not User or not Password or not To:
            self.logger.error("Missing Host, User, Password, or To address.")
            return

        port_val = kwargs.get("Port") or self.properties.get("Port", 465)
        port = int(port_val)
        
        try:
            msg = MIMEMultipart()
            msg['From'] = User
            msg['To'] = To
            msg['Subject'] = Subject or ""
            msg.attach(MIMEText(Body or "", 'plain'))
            
            if Attachments:
                for fpath in Attachments:
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(fpath)}"')
                            msg.attach(part)
                            
            context = ssl.create_default_context()
            
            if port == 465:
                with smtplib.SMTP_SSL(Host, port, context=context) as server:
                    server.login(User, Password)
                    server.sendmail(User, To, msg.as_string())
            else:
                with smtplib.SMTP(Host, port) as server:
                    server.starttls(context=context)
                    server.login(User, Password)
                    server.sendmail(User, To, msg.as_string())
                    
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Success"], self.name)
            return
            
        except Exception as e:
            self.logger.error(f"SMTP Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error"], self.name)
