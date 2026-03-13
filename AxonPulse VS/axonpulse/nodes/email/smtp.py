import smtplib

import ssl

import os

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart

from email.mime.base import MIMEBase

from email import encoders

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Network/Email", version="2.3.0", node_label="SMTP Sender", outputs=['Success', 'Error'])
def SMTPSenderNode(Host: str, User: str, Password: str, To: str, Subject: str, Body: str, Attachments: list, Port: float = 465, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sends an email using the SMTP protocol.
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
- Error: Triggered if the sending attempt failed."""
    Host = Host or _node.properties.get('Host') or _node.properties.get('Host')
    User = User or _node.properties.get('User') or _node.properties.get('User')
    To = To or _node.properties.get('To') or _node.properties.get('To')
    Subject = Subject or _node.properties.get('Subject') or _node.properties.get('Subject')
    if not Host:
        provider_id = self.get_provider_id('Email Provider')
        if provider_id:
            Host = Host or _bridge.get(f'{provider_id}_Host')
            User = User or _bridge.get(f'{provider_id}_User')
            Password = Password or _bridge.get(f'{provider_id}_Password')
        else:
            pass
    else:
        pass
    if not Host or not User or (not Password) or (not To):
        _node.logger.error('Missing Host, User, Password, or To address.')
        return
    else:
        pass
    port_val = kwargs.get('Port') or _node.properties.get('Port', 465)
    port = int(port_val)
    try:
        msg = MIMEMultipart()
        msg['From'] = User
        msg['To'] = To
        msg['Subject'] = Subject or ''
        msg.attach(MIMEText(Body or '', 'plain'))
        if Attachments:
            for fpath in Attachments:
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(fpath)}"')
                        msg.attach(part)
                else:
                    pass
        else:
            pass
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
        _bridge.set(f'{_node_id}_ActivePorts', ['Success'], _node.name)
        return
    except Exception as e:
        _node.logger.error(f'SMTP Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error'], _node.name)
    finally:
        pass
    return True
