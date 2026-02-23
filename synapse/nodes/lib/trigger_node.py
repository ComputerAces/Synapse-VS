"""
Global Hotkey / Event Trigger Node.

A specialized "Service" node that spins up a background listener
for Global Hotkeys, Time Intervals, or Date-based triggers.
"""
import threading
import time
import datetime
import re
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager


# Lazy Global
pynput_keyboard = None

def ensure_pynput():
    global pynput_keyboard
    if pynput_keyboard: return True
    if DependencyManager.ensure("pynput"):
        from pynput import keyboard as _k; pynput_keyboard = _k; return True
    return False


def _parse_hotkey(value):
    """Converts 'SendKeys' style (Ctrl+C) to pynput style (<ctrl>+c)."""
    if not value:
        return ""
    val = value.lower()
    val = val.replace("ctrl", "<ctrl>").replace("alt", "<alt>").replace("shift", "<shift>").replace("cmd", "<cmd>").replace("win", "<cmd>")
    val = val.replace(" + ", "+").replace(" +", "+").replace("+ ", "+")
    return val


def _parse_timer(value):
    """Parses time strings into seconds (float)."""
    if not value: return 60.0
    value = str(value).lower().strip()
    match = re.search(r"([\d\.]+)\s*([a-z]*)", value)
    if not match:
        try: return float(value)
        except: return 60.0
    num = float(match.group(1))
    unit = match.group(2)
    if "min" in unit: return num * 60
    elif "hour" in unit: return num * 3600
    elif "day" in unit: return num * 86400
    elif "ms" in unit or "milli" in unit: return num / 1000
    else: return num


class _TriggerListener:
    """Internal background listener thread."""
    def __init__(self, mode, value, callback, logger):
        self.mode = mode          # "keyboard", "timer", "date", "time"
        self.value = value        # raw string value
        self.callback = callback  # called when event fires
        self.logger = logger
        self._running = False
        self._thread = None
        self._hotkey_listener = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._run, name=f"SynapseTrigger-Listener", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hotkey_listener:
            try: self._hotkey_listener.stop()
            except: pass
            self._hotkey_listener = None

    def _run(self):
        if self.mode == "keyboard": self._run_hotkey()
        elif self.mode == "timer": self._run_timer()
        elif self.mode == "date": self._run_date()
        elif self.mode == "time": self._run_time()

    def _run_hotkey(self):
        if not ensure_pynput():
            self.logger.error("pynput not installed.")
            return

        pynput_hotkey = _parse_hotkey(self.value)
        self.logger.info(f"Listening for hotkey: {self.value}")

        def on_activate():
            if self._running:
                self.logger.info(f"Hotkey triggered: {self.value}")
                self.callback()

        try:
            self._hotkey_listener = pynput_keyboard.GlobalHotKeys({pynput_hotkey: on_activate})
            self._hotkey_listener.start()
            while self._running:
                time.sleep(0.2)
        except Exception as e:
            self.logger.error(f"Hotkey Error: {e}")
        finally:
            if self._hotkey_listener:
                try: self._hotkey_listener.stop()
                except: pass

    def _run_timer(self):
        interval = _parse_timer(self.value)
        self.logger.info(f"Timer started: every {interval}s")
        while self._running:
            time.sleep(interval)
            if self._running:
                self.callback()

    def _run_date(self):
        target_str = self.value.strip("#")
        try:
            target_dt = datetime.datetime.fromisoformat(target_str)
        except:
            self.logger.error(f"Invalid date '{target_str}'. Use ISO format.")
            return

        self.logger.info(f"Waiting until Date: {target_dt.isoformat()}")
        while self._running:
            if datetime.datetime.now() >= target_dt:
                self.callback()
                break
            time.sleep(1.0)

    def _run_time(self):
        target_time_str = self.value.strip("#")
        try:
            t_parts = [int(x) for x in target_time_str.split(":")]
            target_time = datetime.time(*t_parts)
        except:
             self.logger.error(f"Invalid time '{target_time_str}'. Use HH:MM or HH:MM:SS")
             return

        self.logger.info(f"Trigger set for {target_time} daily.")
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
                self.callback()
                time.sleep(1.1)


@NodeRegistry.register("Event Trigger", "Flow/Triggers")
class EventTriggerNode(SuperNode):
    """
    Standardized service for listening to global system events.
    Supports Keyboard Hotkeys, Time Intervals (Timers), and scheduled Date/Time events.
    Must be 'Armed' to start listening and 'Disarmed' to stop.
    
    Inputs:
    - Arm: Start the background listener.
    - Disarm: Stop the background listener.
    - Value: The trigger configuration (Hotkey string, time interval, or ISO date).
    - Trigger Type: The mode of detection (Keyboard, Timer, Date, Time).
    
    Outputs:
    - Flow: Triggered when armed/disarmed.
    - Trigger: Pulse fired when the event occurs.
    - Stop: Pulse fired when disarmed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.is_service = True
        self.properties["Trigger Type"] = "Keyboard"  
        self.properties["Value"] = "Ctrl+Shift+P"
        self._listener = None
        self.define_schema()
        self.register_handler("Arm", self.arm_trigger)
        self.register_handler("Disarm", self.disarm_trigger)

    def define_schema(self):
        self.input_schema = {
            "Arm": DataType.FLOW,
            "Disarm": DataType.FLOW,
            "Value": DataType.STRING,
            "Trigger Type": DataType.TRIGGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Trigger": DataType.FLOW,
            "Stop": DataType.FLOW
        }

    def disarm_trigger(self, **kwargs):
        self.logger.info("Disarming trigger...")
        if self._listener:
            self._listener.stop()
            self._listener = None
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Stop"], self.name)
        return True

    def arm_trigger(self, Value=None, **kwargs):
        trigger_type = kwargs.get("Trigger Type") or self.properties.get("Trigger Type", "Keyboard").lower()
        val = Value if Value else kwargs.get("Value") or self.properties.get("Value", "")
        
        if self._listener:
            self._listener.stop()
            
        def on_trigger():
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Trigger"], self.name)
            self.bridge.set(f"_TRIGGER_FIRE_{self.node_id}", True, self.name)

        config_mode = "keyboard"
        if "timer" in trigger_type or "interval" in trigger_type: config_mode = "timer"
        elif "date" in trigger_type: config_mode = "date"
        elif "time" in trigger_type: config_mode = "time"
        
        self._listener = _TriggerListener(config_mode, val, on_trigger, self.logger)
        self._listener.start()
        
        self.logger.info(f"Armed ({config_mode}): {val}")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None


@NodeRegistry.register("Service Exit Trigger", "Flow/Triggers")
class ServiceExitTriggerNode(SuperNode):
    """
    Utility node to remotely deactivate an Event Trigger service.
    Targeting is done via 'Trigger ID', or all triggers if ID is empty.
    
    Inputs:
    - Flow: Execution trigger.
    - Trigger ID: The ID of the specific target trigger node (optional).
    
    Outputs:
    - Flow: Triggered after the signal is sent.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Trigger ID"] = ""
        self.define_schema()
        self.register_handler("Flow", self.signal_exit)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Trigger ID": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def signal_exit(self, Trigger_ID=None, **kwargs):
        tid = Trigger_ID if Trigger_ID is not None else kwargs.get("Trigger ID") or self.properties.get("Trigger ID", "")
        if tid:
            self.bridge.set(f"_TRIGGER_DISARM_{tid}", True, self.name)
        else:
            self.bridge.set("_TRIGGER_DISARM_ALL", True, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
