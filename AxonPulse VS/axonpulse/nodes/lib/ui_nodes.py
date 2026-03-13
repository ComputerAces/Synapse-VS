import sys

import json

import os

import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

try:
    from PyQt6.QtWidgets import QApplication
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

try:
    from axonpulse.core.cli_forms import render_form_cli
except ImportError:
    render_form_cli = None

@axon_node(category="UI", version="2.3.0", node_label="Custom Form", outputs=['Form Data'])
def CustomFormNode(Title: str = 'Data Input', Blocking: bool = True, Schema: list = [{'label': 'Name', 'type': 'text', 'default': ''}, {'label': 'Agree', 'type': 'boolean', 'default': False}], _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Renders a dynamic user interface form based on a matching schema.
Supports both GUI (via Bridge) and CLI rendering modes.

Inputs:
- Flow: Trigger the form display.
- Title: The window or header title for the form.
- Blocking: If True, execution waits until the user submits the form.
- Schema: A list of field definitions (label, type, default).

Outputs:
- Flow: Triggered after form submission (or immediately if non-blocking).
- Form Data: A dictionary containing the user's input values."""
    title = Title if Title is not None else kwargs.get('Title') or _node.properties.get('Title', 'Data Input')
    schema = Schema if Schema is not None else kwargs.get('Schema') or _node.properties.get('Schema', [])
    blocking = Blocking if Blocking is not None else kwargs.get('Blocking') if kwargs.get('Blocking') is not None else _node.properties.get('Blocking', True)
    is_headless = False
    if HAS_GUI:
        app = QApplication.instance()
        if not app:
            is_headless = True
        else:
            pass
    else:
        is_headless = True
    data = {}
    safe_name = title.lower().replace(' ', '_') + '.syf'
    if os.path.exists(safe_name):
        _node.logger.info(f'Automation: Found {safe_name}. Loading answers.')
        try:
            with open(safe_name, 'r') as f:
                data = json.load(f)
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        except Exception as e:
            _node.logger.error(f'Error reading {safe_name}: {e}')
        finally:
            pass
    else:
        pass
    if is_headless:
        if render_form_cli:
            _node.logger.info('Rendering CLI Form...')
            data = render_form_cli(title, schema)
        else:
            _node.logger.error('CLI Forms module missing. Using defaults.')
            data = {f['label']: f.get('default') for f in schema}
    else:
        _node.logger.info('Requesting GUI Form via Bridge...')
        req_id = f'FORM_{_node_id}_{time.time_ns()}'
        payload = {'id': req_id, 'title': title, 'schema': schema}
        _bridge.set('SHOW_FORM', payload, _node.name)
        if not blocking:
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        else:
            pass
        resp_key = f'FORM_RESPONSE_{req_id}'
        max_retries = 600
        for _ in range(max_retries):
            resp = _bridge.get(resp_key)
            if resp:
                data = resp
                _bridge.delete(resp_key)
                break
            else:
                pass
            time.sleep(0.1)
        if not data:
            _node.logger.warning('Timed out waiting for GUI Form.')
            data = {}
        else:
            pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return data


@axon_node(category="UI", version="2.3.0", node_label="Message Box")
def MessageBoxNode(Title: str = 'Message', Message: str = 'Hello World', Type: Any = 'info', Buttons: str = 'ok', Blocking: bool = True, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Displays a modal message box to the user.

Supports various types (Infor, Warning, Error) and button configurations 
(OK, Yes/No, OK/Cancel). Can block execution until the user interacts 
with the dialog.

Inputs:
- Flow: Trigger the display.
- Title: The title of the message box window.
- Message: The text content to display.
- Type: The style of the box ('info', 'warning', 'error').
- Buttons: The button layout ('ok', 'yes_no', 'ok_cancel').
- Blocking: Whether to wait for user input (default True).

Outputs:
- Flow: Pulse triggered after closure (or immediately if non-blocking).
- Result: The button clicked by the user (e.g., 'ok', 'yes', 'no')."""
    msg = Message if Message is not None else _node.properties.get('Message', 'Hello World')
    title = Title if Title is not None else _node.properties.get('Title', 'Message')
    msg_type = (Type if Type is not None else _node.properties.get('Type', 'info')).lower()
    buttons = (Buttons if Buttons is not None else _node.properties.get('Buttons', 'ok')).lower()
    blocking = Blocking if Blocking is not None else _node.properties.get('Blocking', True)
    is_headless = not HAS_GUI
    if HAS_GUI:
        app = QApplication.instance()
        if not app:
            is_headless = True
        else:
            pass
    else:
        pass
    if is_headless:
        prefix = f'[{msg_type.upper()}]'
        print(f'\n{prefix} {title}: {msg}')
        res = 'ok'
        if buttons in ['yes_no', 'ok_cancel']:
            if buttons == 'yes_no':
                ans = input(' (y/n): ').strip().lower()
                res = 'yes' if ans.startswith('y') else 'no'
            else:
                ans = input(" Press Enter to Continue (or type 'c' to cancel): ").strip().lower()
                res = 'cancel' if ans == 'c' else 'ok'
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    req_id = f'MSG_{_node_id}_{time.time_ns()}'
    payload = {'id': req_id, 'title': title, 'text': str(msg), 'type': msg_type, 'buttons': buttons}
    _bridge.set('SHOW_MESSAGE', payload, _node.name)
    if not blocking:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    resp_key = f'MESSAGE_RESPONSE_{req_id}'
    max_retries = 6000
    res = 'ok'
    for _ in range(max_retries):
        val = _bridge.get(resp_key)
        if val:
            res = val
            _bridge.delete(resp_key)
            break
        else:
            pass
        time.sleep(0.1)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return res


@axon_node(category="UI", version="2.3.0", node_label="Text Display")
def TextDisplayNode(Title: str = 'Text Output', Blocking: bool = True, Text: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Displays text content to the user in a dedicated window or console block.
Commonly used for showing long reports, logs, or multi-line data summaries.

Inputs:
- Flow: Trigger the display.
- Text: The string content to show.

Outputs:
- Flow: Pulse triggered after the window is closed or processed."""
    text_val = Text if Text is not None else kwargs.get('Text') or _node.properties.get('Text', '')
    title = Title if Title is not None else kwargs.get('Title') or _node.properties.get('Title', 'Text Output')
    blocking = Blocking if Blocking is not None else kwargs.get('Blocking') if kwargs.get('Blocking') is not None else _node.properties.get('Blocking', True)
    is_headless = not HAS_GUI
    if HAS_GUI and (not QApplication.instance()):
        is_headless = True
    else:
        pass
    if is_headless:
        print(f'\n--- {title} ---')
        print(text_val)
        print('-------------------')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    req_id = f'TXT_{_node_id}_{time.time_ns()}'
    payload = {'id': req_id, 'title': title, 'text': str(text_val)}
    _bridge.set('SHOW_TEXT_DIALOG', payload, _node.name)
    if not blocking:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    resp_key = f'TEXT_RESPONSE_{req_id}'
    max_retries = 6000
    for _ in range(max_retries):
        if _bridge.get(resp_key):
            _bridge.delete(resp_key)
            break
        else:
            pass
        time.sleep(0.1)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
