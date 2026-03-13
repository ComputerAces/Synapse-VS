import threading

import time

import datetime

import re

from axonpulse.nodes.lib.loop_node import LoopNode

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType, TriggerType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nGlobal Hotkey / Event Trigger Node.\n\nA specialized "Service" node that spins up a background listener\nfor Global Hotkeys, Time Intervals, or Date-based triggers.\n'

pynput_keyboard = None

def ensure_pynput():
    global pynput_keyboard
    if pynput_keyboard:
        return True
    if DependencyManager.ensure('pynput'):
        from pynput import keyboard as _k
        pynput_keyboard = _k
        return True
    return False

def _parse_hotkey(value):
    """Converts 'SendKeys' style (Ctrl+C) to pynput style (<ctrl>+c)."""
    if not value:
        return ''
    val = value.lower()
    val = val.replace('ctrl', '<ctrl>').replace('alt', '<alt>').replace('shift', '<shift>').replace('cmd', '<cmd>').replace('win', '<cmd>')
    val = val.replace(' + ', '+').replace(' +', '+').replace('+ ', '+')
    return val

def _parse_timer(value):
    """Parses time strings into seconds (float)."""
    if not value:
        return 60.0
    value = str(value).lower().strip()
    match = re.search('([\\d\\.]+)\\s*([a-z]*)', value)
    if not match:
        try:
            return float(value)
        except:
            return 60.0
    num = float(match.group(1))
    unit = match.group(2)
    if 'min' in unit:
        return num * 60
    elif 'hour' in unit:
        return num * 3600
    elif 'day' in unit:
        return num * 86400
    elif 'ms' in unit or 'milli' in unit:
        return num / 1000
    else:
        return num

class _TriggerListener:
    """Internal background listener thread."""

    def __init__(self, mode, value, callback, logger):
        self.mode = mode
        self.value = value
        self.callback = callback
        self.logger = logger
        self._running = False
        self._thread = None
        self._hotkey_listener = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, name=f'AxonPulseTrigger-Listener', daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except:
                pass
            self._hotkey_listener = None

    def _run(self):
        if self.mode == 'keyboard':
            self._run_hotkey()
        elif self.mode == 'timer':
            self._run_timer()
        elif self.mode == 'date':
            self._run_date()
        elif self.mode == 'time':
            self._run_time()

    def _run_hotkey(self):
        if not ensure_pynput():
            self.logger.error('pynput not installed.')
            return
        pynput_hotkey = _parse_hotkey(self.value)
        self.logger.info(f'Listening for hotkey: {self.value}')

        def on_activate():
            if self._running:
                self.logger.info(f'Hotkey triggered: {self.value}')
                self.callback()
        try:
            self._hotkey_listener = pynput_keyboard.GlobalHotKeys({pynput_hotkey: on_activate})
            self._hotkey_listener.start()
            while self._running:
                time.sleep(0.2)
        except Exception as e:
            self.logger.error(f'Hotkey Error: {e}')
        finally:
            if self._hotkey_listener:
                try:
                    self._hotkey_listener.stop()
                except:
                    pass

    def _run_timer(self):
        interval = _parse_timer(self.value)
        self.logger.info(f'Timer started: every {interval}s')
        while self._running:
            time.sleep(interval)
            if self._running:
                self.callback()

    def _run_date(self):
        target_str = self.value.strip('#')
        try:
            target_dt = datetime.datetime.fromisoformat(target_str)
        except:
            self.logger.error(f"Invalid date '{target_str}'. Use ISO format.")
            return
        self.logger.info(f'Waiting until Date: {target_dt.isoformat()}')
        last_fired = None
        while self._running:
            now = datetime.datetime.now()
            if now >= target_dt:
                current_day = now.date()
                if last_fired != current_day:
                    self.callback()
                    last_fired = current_day
            time.sleep(1.0)

    def _run_time(self):
        target_time_str = self.value.strip('#')
        try:
            t_parts = [int(x) for x in target_time_str.split(':')]
            target_time = datetime.time(*t_parts)
        except:
            self.logger.error(f"Invalid time '{target_time_str}'. Use HH:MM or HH:MM:SS")
            return
        self.logger.info(f'Trigger set for {target_time} daily.')
        last_fired = None
        while self._running:
            now = datetime.datetime.now()
            today_target = datetime.datetime.combine(now.date(), target_time)
            next_target = today_target if now <= today_target else today_target + datetime.timedelta(days=1)
            wait_seconds = (next_target - now).total_seconds()
            while wait_seconds > 0 and self._running:
                sleep_amt = min(wait_seconds, 2.0)
                time.sleep(sleep_amt)
                wait_seconds -= sleep_amt
            if self._running:
                current_minute = datetime.datetime.now().replace(second=0, microsecond=0)
                if last_fired != current_minute:
                    self.callback()
                    last_fired = current_minute
                time.sleep(1.1)

@NodeRegistry.register('Event Trigger', 'Flow/Triggers')
class EventTriggerNode(LoopNode):
    """
    Standardized service for listening to global system events within an ongoing Sub-Flow.
    Supports Keyboard Hotkeys, Time Intervals (Timers), and scheduled Date/Time events.
    When an event fires, it branches its execution to 'Triggered'. Once that branch finishes, 
    it returns to this node ('Continue') to wait for the next occurrence.
    
    Inputs:
    - Arm: Start the background listener sequence.
    - Disarm: Stop the background listener and exit the sub-flow.
    - End: Force kill the underlying thread immediately.
    - Value: The trigger configuration (Hotkey string, time interval, or ISO date).
    - Trigger Type: The mode of detection (Keyboard, Timer, Date, Time).
    
    Outputs:
    - Flow: Fired when explicitly stopped/disarmed.
    - Triggered: Pulse fired each time the event occurs.
    - Index: The amount of times the event has fired so far.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.is_service = True
        self._loop_body_port_name = 'Triggered'
        self.properties['Trigger Type'] = TriggerType.KEYBOARD
        self.properties['Value'] = 'Ctrl+Shift+P'
        self._listener = None
        self._event_fired = False

    def register_handlers(self):
        super().register_handlers()
        self.register_handler('Arm', self.do_work)
        self.register_handler('Disarm', self.do_work)

    def define_schema(self):
        self.input_schema = {'Arm': DataType.FLOW, 'Continue': DataType.FLOW, 'Disarm': DataType.FLOW, 'Break': DataType.FLOW, 'End': DataType.FLOW, 'Value': DataType.STRING, 'Trigger Type': DataType.TRIGGER}
        self.output_schema = {'Flow': DataType.FLOW, 'Triggered': DataType.FLOW, 'Index': DataType.INTEGER}

    def do_work(self, **kwargs):
        _trigger = kwargs.get('_trigger', 'Flow')
        if _trigger == 'Arm':
            _trigger = 'Flow'
        if _trigger == 'Disarm':
            _trigger = 'Break'
        if _trigger == 'Continue':
            self._event_fired = False
        kwargs['_trigger'] = _trigger
        if _trigger in ['Break', 'End']:
            if self._listener:
                self._listener.stop()
                self._listener = None
        return super().do_work(**kwargs)

    def _on_loop_start(self, **kwargs):
        """Called when Flow/Arm is hit to initialize the persistent Listener."""
        t_type = kwargs.get('Trigger Type')
        if t_type is None:
            t_type = self.properties.get('Trigger Type', TriggerType.KEYBOARD)
        trigger_type = t_type.value.lower() if hasattr(t_type, 'value') else str(t_type).lower()
        val = kwargs.get('Value') or self.properties.get('Value', '')
        if self._listener:
            self._listener.stop()
        self._event_fired = False

        def on_trigger():
            self._event_fired = True
        config_mode = 'keyboard'
        if 'timer' in trigger_type or 'interval' in trigger_type:
            config_mode = 'timer'
        elif 'date' in trigger_type:
            config_mode = 'date'
        elif 'time' in trigger_type:
            config_mode = 'time'
        self._listener = _TriggerListener(config_mode, val, on_trigger, self.logger)
        self._listener.start()
        self.logger.info(f'Trigger Listener Armed ({config_mode}): {val} - Waiting...')

    def _check_condition(self, index, **kwargs):
        """
        Hold execution in a soft sleep state until _event_fired becomes true.
        """
        active_key = f'{self.node_id}_loop_active'
        while self.bridge.get(active_key) and (not self._event_fired):
            time.sleep(0.1)
        if not self.bridge.get(active_key):
            return (False, None)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Triggered'], self.name)
        return (True, None)

@axon_node(category="Flow/Triggers", version="2.3.0", node_label="Service Exit Trigger")
def ServiceExitTriggerNode(Trigger_ID: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Utility node to remotely deactivate an Event Trigger service.
Targeting is done via 'Trigger ID', or all triggers if ID is empty.

Inputs:
- Flow: Execution trigger.
- Trigger ID: The ID of the specific target trigger node (optional).

Outputs:
- Flow: Triggered after the signal is sent."""
    tid = Trigger_ID if Trigger_ID is not None else kwargs.get('Trigger ID') or _node.properties.get('Trigger ID', '')
    if tid:
        _bridge.set(f'_TRIGGER_DISARM_{tid}', True, _node.name)
    else:
        _bridge.set('_TRIGGER_DISARM_ALL', True, _node.name)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
