from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QProcess
import json
import os
import sys
from axonpulse.utils.file_utils import smart_load, serialize_to_yaml
import multiprocessing
from axonpulse.core.bridge import AxonPulseBridge

class GraphWidget(QWidget):
    """
    Encapsulates a NodeCanvas and its associated file state.
    """
    
    # Signals
    state_changed = pyqtSignal(str)  # "RUNNING", "PAUSED", "STOPPED"
    output_received = pyqtSignal(str, str)  # (line, channel)
    modified = pyqtSignal()
    selection_changed_signal = pyqtSignal()
    
    # Execution States
    STATE_STOPPED = "STOPPED"
    STATE_RUNNING = "RUNNING"
    STATE_PAUSED = "PAUSED"
    
    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        
        # [CRITICAL FIX] Defer import to prevent circular dependency loop:
        # main_window -> graph_widget -> canvas -> serializer -> registry -> nodes -> main_window
        from axonpulse.gui.canvas import NodeCanvas
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.canvas = NodeCanvas()
        self.layout.addWidget(self.canvas)
        self.canvas.modified.connect(self.modified.emit)
        
        # Safe Signal Connection
        try:
            self.canvas.scene.selectionChanged.connect(self._on_selection_changed)
        except Exception as e:
            print(f"Warning: Failed to connect selection signal: {e}")
        
        self.file_path = None
        self.is_modified = False
        self._is_loading = False
        
        # Execution State
        self.execution_state = self.STATE_STOPPED
        self.process = None
        
        # Local Bridge for UI State
        # Use shared manager if provided to prevent process explosion
        if manager:
            self._manager = manager
        else:
            self._manager = multiprocessing.Manager()
            
        self.bridge = AxonPulseBridge(self._manager)
        
        # Output Buffers
        
        # Output Buffers
        self.console_buffer = []
        self.debug_buffer = []

        # Undo Stack
        from PyQt6.QtGui import QUndoStack
        self.undo_stack = QUndoStack(self)

        # Project Metadata
        self.project_metadata = {
            "project_name": "",
            "project_description": "",
            "project_type": "",
            "project_category": "",
            "project_version": "1.0.0",
            "project_vars": {},
            "version": "2.3.0" # Schema Version
        }
        
        # Viewport State Tracking
        self._first_view = True
        self._saved_view_state = None
        
    def _on_selection_changed(self):
        """Safely emit selection change signal."""
        try:
            self.selection_changed_signal.emit()
        except: pass

    def mark_modified(self, rect):
        if self._is_loading:
            return
        if not self.is_modified:
            self.is_modified = True
            self.modified.emit() 
        
        # [LIVE GRAPH] Update registry with current graph data
        self._update_live_registry()

    def clear_modified(self):
        self.is_modified = False

    def set_file_path(self, path):
        # [LIVE GRAPH] Unregister old path if changing
        if self.file_path and self.file_path != path:
            from axonpulse.gui import LIVE_GRAPHS
            LIVE_GRAPHS.pop(self.file_path, None)
        
        self.file_path = path
        
        # [LIVE GRAPH] Register new path
        self._update_live_registry()
    
    def _update_live_registry(self):
        """Update the LIVE_GRAPHS registry with current graph data."""
        if self.file_path and not self._is_loading:
            try:
                from axonpulse.gui import LIVE_GRAPHS
                LIVE_GRAPHS[self.file_path] = self.serialize()
            except Exception:
                pass  # Ignore serialization errors during partial edits
    
    def unregister_live_graph(self):
        """Remove from LIVE_GRAPHS registry (call when closing tab)."""
        if self.file_path:
            from axonpulse.gui import LIVE_GRAPHS
            LIVE_GRAPHS.pop(self.file_path, None)

    def on_subgraph_saved(self, file_path):
        """Refresh any nodes that use the saved file as a subgraph."""
        if not self.canvas or not self.canvas.scene:
            return
            
        from axonpulse.nodes.lib.subgraph import SubGraphNode
        from axonpulse.core.types import DataType
        
        refreshed = False
        abs_saved_path = os.path.abspath(file_path)
        
        for item in self.canvas.scene.items():
            if hasattr(item, 'node') and isinstance(item.node, SubGraphNode):
                # Robust Path Lookup
                props = item.node.properties
                node_path = props.get("Graph Path") or props.get("graph_path") or props.get("GraphPath")
                
                if node_path and os.path.normcase(os.path.abspath(node_path)) == os.path.normcase(abs_saved_path):
                    # 1. Refresh logical structure
                    item.node.rebuild_ports()
                    
                    # 2. Sync UI Inputs
                    logical_inputs = item.node.input_types # {name: type}
                    current_inputs = {p.name: p for p in item.inputs}
                    
                    # Remove old inputs (except Flow and system properties)
                    system_inputs = ["Flow", "Graph Path", "Embedded Data", "Isolated"]
                    for p_name in list(current_inputs.keys()):
                        if p_name not in logical_inputs and p_name not in system_inputs:
                            item.remove_port(p_name)
                    
                    # Add missing inputs
                    for p_name, p_type in logical_inputs.items():
                        if p_name not in current_inputs:
                            p_cls = "flow" if str(p_type) == str(DataType.FLOW) else "data"
                            item.add_input(p_name, port_class=p_cls, data_type=p_type)

                    # 3. Sync UI Outputs
                    logical_outputs = item.node.output_types # {name: type}
                    current_outputs = {p.name: p for p in item.outputs}
                    
                    # Remove old outputs (except Error Flow)
                    system_outputs = ["Error Flow"]
                    for p_name in list(current_outputs.keys()):
                        if p_name not in logical_outputs and p_name not in system_outputs:
                            item.remove_port(p_name)
                    
                    # Add missing outputs
                    for p_name, p_type in logical_outputs.items():
                        if p_name not in current_outputs:
                            p_cls = "flow" if str(p_type) == str(DataType.FLOW) else "data"
                            item.add_output(p_name, port_class=p_cls, data_type=p_type)

                    refreshed = True
        
        if refreshed:
            self.mark_modified(None)
            self.update()

    def get_file_name(self):
        if self.file_path:
            return os.path.basename(self.file_path)
        return "Untitled"

    def serialize(self):
        """Wrapper for canvas serialization."""
        # [NEW] Sync metadata from Bridge before saving
        self.project_metadata["project_name"] = self.bridge.get("ProjectMeta.project_name") or self.project_metadata.get("project_name", "")
        self.project_metadata["project_version"] = self.bridge.get("ProjectMeta.project_version") or self.project_metadata.get("project_version", "1.0.0")
        self.project_metadata["project_category"] = self.bridge.get("ProjectMeta.project_category") or self.project_metadata.get("project_category", "")
        self.project_metadata["project_description"] = self.bridge.get("ProjectMeta.project_description") or self.project_metadata.get("project_description", "")
        
        data = self.canvas.serialize()
        data.update(self.project_metadata)
        return data

    def deserialize(self, data):
        """Wrapper for canvas deserialization."""
        self._is_loading = True
        was_pruned = False
        try:
            self.canvas.scene.clear()
            was_pruned = self.canvas.deserialize(data)
            self.is_modified = False
            # ... (metadata restoration)
            # Restore metadata
            self.project_metadata["project_name"] = data.get("project_name", "")
            self.project_metadata["project_description"] = data.get("project_description", "")
            self.project_metadata["project_type"] = data.get("project_type", "")
            self.project_metadata["project_category"] = data.get("project_category", "")
            self.project_metadata["project_version"] = data.get("project_version", "1.0.0")
            self.project_metadata["project_vars"] = data.get("project_vars", {})
            self.project_metadata["version"] = data.get("version", "2.3.0")
            
            # [VIEWPORT] Capture saved state for restoration on tab activate
            if "viewport" in data:
                self._saved_view_state = data["viewport"]
            else:
                self._saved_view_state = None
        finally:
            self._is_loading = False
            
        return was_pruned

    def restore_view_state(self):
        """Restores the saved zoom and center point from file."""
        if self._saved_view_state and self._first_view:
            self.canvas.set_view_state(self._saved_view_state)
            self._first_view = False

    def get_view_state(self):
        return self.canvas.get_view_state()
        
    def set_view_state(self, state):
        # [PERSISTENCE FIX] Mark as viewed so restore_view_state doesn't overwrite with file defaults
        self._first_view = False 
        self.canvas.set_view_state(state)

    def get_selected_nodes(self):
        """Returns a list of selected NodeWidgets."""
        try:
            if not self.canvas or not self.canvas.scene:
                return []
            return [item for item in self.canvas.scene.selectedItems() if hasattr(item, 'node')]
        except RuntimeError:
            # "wrapped C/C++ object of type GraphicScene has been deleted"
            # This can happen during shutdown or tab switching
            return []

    def copy_selection(self):
        """Delegates copy to canvas."""
        self.canvas.copy_selection()

    def paste_selection(self):
        """Delegates paste to canvas."""
        self.canvas.paste_selection()

    def duplicate_selection(self):
        """Delegates duplicate to canvas."""
        self.canvas.duplicate_selection()

    def delete_selection(self):
        """Delegates delete to canvas."""
        self.canvas.delete_selection()

    def save_selection_as_snippet(self):
        """Saves selected nodes as a reusable snippet."""
        data = self.canvas.serializer.serialize_selection()
        if not data["nodes"]:
            return
            
        from PyQt6.QtWidgets import QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QComboBox
        
        # Custom Dialog for Name & Category
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Snippet")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Snippet Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        layout.addWidget(QLabel("Category:"))
        cat_input = QComboBox()
        cat_input.setEditable(True)
        # Populate with existing categories if possible, hardcode for now or fetch from registry
        cat_input.addItems(["Snippets", "Favorites", "Utility", "Logic", "Math"]) 
        layout.addWidget(cat_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            name = name_input.text().strip()
            category = cat_input.currentText().strip()
            if not category: category = "Snippets"
            
            if name:
                safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
                filename = f"{safe_name}.syp"
            snippet_dir = os.path.join(os.getcwd(), "snippets")
            if not os.path.exists(snippet_dir):
                os.makedirs(snippet_dir)
                
            path = os.path.join(snippet_dir, filename)
            
            try:
                with open(path, "w", encoding='utf-8') as f:
                    # Enrich with metadata
                    data["name"] = name
                    data["category"] = category
                    data["type"] = "snippet"
                    f.write(serialize_to_yaml(data))
                    
                QMessageBox.information(self, "Snippet Saved", f"Snippet '{name}' saved to library.")
                
                # Trigger Library Refresh via MainWindow if possible
                window = self.window()
                if hasattr(window, "node_library"):
                     window.node_library.populate_library()
                     
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save snippet: {e}")

    # Execution Control
    def run(self, run_path, delay=0.0, pause_flag_file=None, trace=True):
        if self.execution_state == self.STATE_RUNNING:
            return
            
        # [SECURITY SANDBOX]
        if getattr(self, "safe_mode", False):
            self.console_buffer.append("\n[SECURITY] Execution Blocked: Graph is in Safe Mode.")
            self.state_changed.emit("STOPPED")
            return

        self.console_buffer.clear()
        self.debug_buffer.clear()
        
        python_exe = sys.executable
        
        self.process = QProcess(self)
        self.process.setProgram(python_exe)
        
        args = ["main.py", run_path, "--speed", str(delay), "--headless"]
        if not trace:
            args.append("--no-trace")
        if pause_flag_file:
            args += ["--pause-file", pause_flag_file]
            
        stop_file = self._get_stop_file_path()
        args += ["--stop-file", stop_file]
        
        speed_control_file = self._get_speed_file_path()
        args += ["--speed-file", speed_control_file]
        
        self.set_speed(delay)
        
        self.process.setArguments(args)
        self.process.setWorkingDirectory(os.getcwd())
        
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._process_finished)
        
        self.process.start()
        self._set_state(self.STATE_RUNNING)
        
    def pause(self):
        if self.execution_state == self.STATE_RUNNING:
            pause_file = self._get_pause_file_path()
            with open(pause_file, "w") as f:
                f.write("PAUSED")
            self._set_state(self.STATE_PAUSED)
    
    def resume(self):
        """Resume a paused process by removing the flag file."""
        if self.execution_state == self.STATE_PAUSED:
            pause_file = self._get_pause_file_path()
            if os.path.exists(pause_file):
                os.remove(pause_file)
            self._set_state(self.STATE_RUNNING)
    
    def stop(self):
        """Stop the running process gracefully, with a recursive fallback for orphans."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            # 1. Soft Stop via Flag File
            stop_file = self._get_stop_file_path()
            try:
                with open(stop_file, "w") as f:
                    f.write("STOP")
            except: pass
            
            # 2. Try to get PID before wait finishes (for recursive cleanup)
            pid = self.process.processId()

            # 3. Wait for graceful exit
            if not self.process.waitForFinished(1500):
                # 4. Nuclear Cleanup: Recursive tree termination
                self._terminate_process_tree(pid)
                
                # Double-tap with QProcess kill
                self.process.kill()
                self.process.waitForFinished(1000)
        
        stop_file = self._get_stop_file_path()
        if os.path.exists(stop_file):
            try: os.remove(stop_file)
            except: pass

        pause_file = self._get_pause_file_path()
        if os.path.exists(pause_file):
            try: os.remove(pause_file)
            except: pass
            
        self._set_state(self.STATE_STOPPED)

    def _terminate_process_tree(self, pid):
        """Recursively terminates all child/grandchild processes."""
        if pid <= 0: return
        try:
            import psutil
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Terminate parent
            parent.terminate()
            
            # Wait briefly and then kill survivors
            _, alive = psutil.wait_procs(children + [parent], timeout=2)
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
        except ImportError:
            # Fallback if psutil is missing (less robust)
            pass
        except Exception as e:
            print(f"Recursive cleanup failed: {e}")
    
    def set_speed(self, delay):
        if self.execution_state == self.STATE_RUNNING:
            speed_file = self._get_speed_file_path()
            try:
                with open(speed_file, "w") as f:
                    f.write(str(delay))
            except: pass
            
    def _get_pause_file_path(self):
        graph_id = id(self)
        return os.path.join(os.getcwd(), f".pause_{graph_id}.flag")

    def _get_speed_file_path(self):
        graph_id = id(self)
        return os.path.join(os.getcwd(), f".speed_{graph_id}.txt")
    
    def _get_stop_file_path(self):
        graph_id = id(self)
        return os.path.join(os.getcwd(), f".stop_{graph_id}.flag")
    
    def _set_state(self, new_state):
        self.execution_state = new_state
        self.state_changed.emit(new_state)
    
    def _handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 1. Non-visual Logging (Always Process)
            if "[DEBUG]" in line:
                clean_line = line.replace("[DEBUG]", "").strip()
                clean_line = clean_line.replace("<br>", "\n")
                self.debug_buffer.append(clean_line)
                self.output_received.emit(clean_line, "debug")
                continue
                
            if not (line.startswith("[NODE_START]") or line.startswith("[NODE_STOP]") or 
                    line.startswith("[FLOW]") or line.startswith("[AXON_SUBGRAPH") or
                    line.startswith("[NODE_PREVIEW]") or line.startswith("[PROVIDER_PULSE]") or
                    line.startswith("[NODE_WAITING") or line.startswith("[NODE]") or
                    line.startswith("[SERVICE_START]") or line.startswith("[SERVICE_STOP]")):
                self.console_buffer.append(line)
                self.output_received.emit(line, "console")
                continue
                
            # 2. Visual State Signals (Guard against delayed event loop processing after stop)
            if getattr(self, "execution_state", None) == getattr(self, "STATE_STOPPED", -1):
                continue # Safely ignore ghost highlights arriving late
                
            # 3. Apply Visual States
            if line.startswith("[FLOW]"):
                self.output_received.emit(line, "flow")
            elif line.startswith("[NODE_START]"):
                self.output_received.emit(line, "node_start")
            elif line.startswith("[NODE_STOP]"):
                self.output_received.emit(line, "node_stop")
            elif line.startswith("[NODE]"): # Legacy Support
                self.output_received.emit(line, "node_start")
            elif line.startswith("[SERVICE_START]"):
                node_id = line.replace("[SERVICE_START]", "").strip()
                self.bridge.set(f"{node_id}_IsServiceRunning", True, "stdout_sync")
            elif line.startswith("[SERVICE_STOP]"):
                node_id = line.replace("[SERVICE_STOP]", "").strip()
                self.bridge.set(f"{node_id}_IsServiceRunning", False, "stdout_sync")
            elif line.startswith("[AXON_SUBGRAPH_ACTIVITY]"):
                node_id = line.replace("[AXON_SUBGRAPH_ACTIVITY]", "").strip()
                self.bridge.set(f"{node_id}_SubGraphActivity", True, "stdout_sync")
                self.output_received.emit(line, "subgraph_start")
            elif line.startswith("[AXON_SUBGRAPH_FINISHED]"):
                node_id = line.replace("[AXON_SUBGRAPH_FINISHED]", "").strip()
                self.bridge.set(f"{node_id}_SubGraphActivity", False, "stdout_sync")
                self.output_received.emit(line, "subgraph_stop")
            elif line.startswith("[NODE_PREVIEW]"):
                try:
                    # Format: [NODE_PREVIEW] node_id | [mode] | base64_data
                    content = line.replace("[NODE_PREVIEW]", "").strip()
                    parts = [p.strip() for p in content.split("|")]
                    
                    if len(parts) >= 2:
                        node_id = parts[0]
                        mode = "16:9" # Default
                        b64_data = ""
                        
                        if len(parts) == 2:
                            b64_data = parts[1]
                        else:
                            mode = parts[1]
                            b64_data = parts[2]
                        
                        from axonpulse.gui.node_widget.widget import NodeWidget as NW
                        target_node = None
                        if getattr(self, "canvas", None) and getattr(self.canvas, "scene", None):
                            for item in self.canvas.scene.items():
                                if isinstance(item, NW) and item.node and str(item.node.node_id) == node_id:
                                    target_node = item
                                    break
                        
                        if target_node and hasattr(target_node, "set_preview_data"):
                            target_node.set_preview_data(mode, b64_data)
                except Exception as e:
                    print(f"[Preview Error] {e}")
            elif line.startswith("[PROVIDER_PULSE]"):
                node_id = line.replace("[PROVIDER_PULSE]", "").strip()
                self.output_received.emit(node_id, "provider_pulse")
            elif line.startswith("[NODE_WAITING_PULSE]"):
                self.output_received.emit(line, "node_waiting_pulse")
            elif line.startswith("[NODE_WAITING_START]"):
                self.output_received.emit(line, "node_waiting_start")
    
    def _handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")
        for line in text.split('\n'):
            line = line.strip()
            if line:
                self.console_buffer.append(f"[ERROR] {line}")
                self.output_received.emit(f"[ERROR] {line}", "console")
    
    def _process_finished(self, exit_code, exit_status):
        pause_file = self._get_pause_file_path()
        if os.path.exists(pause_file):
            os.remove(pause_file)
            
        speed_file = self._get_speed_file_path()
        if os.path.exists(speed_file):
            try: os.remove(speed_file)
            except: pass
            
        stop_file = self._get_stop_file_path()
        if os.path.exists(stop_file):
            try: os.remove(stop_file)
            except: pass
            
        # [NEW: V2.4.5] Purge local bridge to clear stale SubGraph & Service UI flags
        if hasattr(self, 'bridge') and self.bridge:
            self.bridge.clear()
            
        self._set_state(self.STATE_STOPPED)