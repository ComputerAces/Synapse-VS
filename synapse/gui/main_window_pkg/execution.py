import os
import json
from PyQt6.QtCore import QTime, QTimer
from PyQt6.QtWidgets import QMessageBox

from synapse.gui.graph_widget import GraphWidget
from synapse.gui.wire import Wire
from synapse.gui.node_widget.widget import NodeWidget

class ExecutionMixin:
    def run_graph(self):
        graph = self.get_current_graph()
        if not graph: return
        if graph.execution_state == graph.STATE_PAUSED:
            graph.resume()
            self.update_execution_ui()
            return
        if graph.execution_state == graph.STATE_RUNNING: return
        
        if not graph.file_path:
            temp_path = "temp_run.json"
            with open(temp_path, "w") as f:
                json.dump(graph.serialize(), f, indent=4)
            run_path = temp_path
        else:
            self.save_graph()
            run_path = graph.file_path
            
        max_delay = 5.0
        delay = max_delay * (1.0 - (self.speed_slider.value() / 100.0))
        
        try: graph.state_changed.disconnect()
        except: pass
        try: graph.output_received.disconnect()
        except: pass
        
        graph.state_changed.connect(self.on_graph_state_changed)
        graph.output_received.connect(self.on_graph_output)
        
        # Clear buffers for a fresh run
        graph.console_buffer.clear()
        graph.debug_buffer.clear()
        self.console_output.clear()
        self.debug_output.clear()
        
        graph.run(run_path, delay, graph._get_pause_file_path(), trace=self.show_trace_checkbox.isChecked())
        self.update_execution_ui()

    def stop_graph(self):
        graph = self.get_current_graph()
        if not graph: return
        if graph.execution_state == graph.STATE_STOPPED: return
        graph.stop()
        self.console_output.append("\n[!] Execution stopped by user.")
        self.statusBar().showMessage("Execution stopped.", 3000)
        self._clear_graph_highlights(graph)
        
        # Also stop any other running graphs (subgraph tabs)
        for i in range(self.central_tabs.count()):
            widget = self.central_tabs.widget(i)
            if isinstance(widget, GraphWidget) and widget != graph:
                if widget.execution_state != widget.STATE_STOPPED:
                    widget.stop()
                    self._clear_graph_highlights(widget)
        
        self.update_execution_ui()

    def stop_all_graphs(self):
        stopped_count = 0
        for i in range(self.central_tabs.count()):
            widget = self.central_tabs.widget(i)
            if isinstance(widget, GraphWidget):
                if widget.execution_state != widget.STATE_STOPPED:
                    widget.stop()
                    stopped_count += 1
                self._clear_graph_highlights(widget)
        if stopped_count > 0:
            self.console_output.append(f"\n[!] Stopped {stopped_count} active graph(s).")
            self.statusBar().showMessage(f"Stopped {stopped_count} graphs.", 3000)
        self.update_execution_ui()
        
    def pause_graph(self):
        graph = self.get_current_graph()
        if graph and graph.execution_state == graph.STATE_RUNNING:
            graph.pause()
            self.console_output.append("\n[||] Execution paused.")
            self.statusBar().showMessage("Execution paused.", 3000)
            self.update_execution_ui()

            self.update_execution_ui()
            
    def step_in_graph(self):
        graph = self.get_current_graph()
        if not graph: return
        # Standard "Step" - Execute next node
        self.shared_manager.dict()["_SYSTEM_STEP_MODE"] = True
        self.shared_manager.dict()["_SYSTEM_STEP_TRIGGER"] = True

    def step_over_graph(self):
        graph = self.get_current_graph()
        if not graph: return
        # "skip next node" behavior
        self.shared_manager.dict()["_SYSTEM_STEP_MODE"] = True
        self.shared_manager.dict()["_SYSTEM_SKIP_NEXT"] = True
        self.shared_manager.dict()["_SYSTEM_STEP_TRIGGER"] = True
        
    def step_back_graph(self):
        graph = self.get_current_graph()
        if not graph: return
        
        # Trigger Step Back
        self.shared_manager.dict()["_SYSTEM_STEP_BACK"] = True
        
        # Ensure we are paused (Step Mode) so we don't just run forward again immediately
        self.shared_manager.dict()["_SYSTEM_STEP_MODE"] = True

    def on_graph_state_changed(self, new_state):
        source_graph = self.sender()
        if new_state == "STOPPED":
            if isinstance(source_graph, GraphWidget):
                self._clear_graph_highlights(source_graph)
        
        if source_graph == self.get_current_graph():
            self.update_execution_ui()
        self.update_tab_icons()

    def on_graph_output(self, line, channel):
        source_graph = self.sender() if isinstance(self.sender(), GraphWidget) else self.get_current_graph()

        if channel == "console": 
            # Always append for active executions to prevent log loss when switching tabs
            self.console_output.append(line)
        elif channel == "debug": 
            # Always append for logic/debug monitoring
            self.debug_output.append(line)
        elif channel == "flow": 
            self.highlight_flow_wire(line, source_graph)
        elif channel == "node_start":
            node_id = line.replace("[NODE_START]", "").strip()
            self.set_node_running_state(node_id, True, source_graph)
        elif channel == "node_stop":
            node_id = line.replace("[NODE_STOP]", "").strip()
            source_graph = self.sender() if isinstance(self.sender(), GraphWidget) else self.get_current_graph()
            
            # [USER REQUEST] All nodes should fade immediately upon stopping
            self.set_node_running_state(node_id, False, source_graph)
        elif channel == "subgraph_start":
            node_id = line.replace("[SYNP_SUBGRAPH_ACTIVITY]", "").strip()
            self.set_node_subgraph_state(node_id, True, source_graph)
        elif channel == "subgraph_stop":
            node_id = line.replace("[SYNP_SUBGRAPH_FINISHED]", "").strip()
            self.set_node_subgraph_state(node_id, False, source_graph)
        elif channel == "node_waiting_start":
            # Format: [NODE_WAITING_START] node_id | duration_ms
            content = line.replace("[NODE_WAITING_START]", "").strip()
            if "|" in content:
                node_id, duration = content.split("|", 1)
                node_id = node_id.strip()
                try: duration = int(duration.strip())
                except: duration = 1000
                self.set_node_waiting_state(node_id, True, duration, source_graph)
        elif channel == "node_waiting_pulse":
            # Format: [NODE_WAITING_PULSE] node_id | duration
            content = line.replace("[NODE_WAITING_PULSE]", "").strip()
            if "|" in content:
                node_id, duration = content.split("|", 1)
                node_id = node_id.strip()
                
                # Re-use waiting state logic + Pulse
                try: duration = int(duration.strip())
                except: duration = 1000
                self.set_node_waiting_state(node_id, True, duration, source_graph)

                target_node = self._find_node_in_graph(source_graph, node_id) if source_graph else None
                if target_node and hasattr(target_node, "highlight_pulse_blue"):
                    target_node.highlight_pulse_blue()

        elif channel == "provider_pulse":
            node_id = line.strip()
            target_node = self._find_node_in_graph(source_graph, node_id) if source_graph else None
            if target_node and hasattr(target_node, "highlight_pulse_blue"):
                target_node.highlight_pulse_blue()
        elif channel == "node_error":
            # Format: [NODE_ERROR] node_id | message
            content = line.replace("[NODE_ERROR]", "").strip()
            if "|" in content:
                node_id, msg = content.split("|", 1)
                node_id = node_id.strip()
                self.set_node_error_state(node_id, True, msg.strip(), source_graph)

    def poll_bridge_states(self):
        try:
             next_node_id = self.shared_manager.dict().get("_SYSTEM_NEXT_NODE")
             graph = self.get_current_graph()
             
             if graph:
                 canvas = graph.canvas
                 needs_update = False
                 for item in canvas.scene.items():
                     if hasattr(item, 'node') and item.node:
                         is_next = (item.node.node_id == next_node_id)
                         if getattr(item, '_is_next', None) != is_next:
                             item._is_next = is_next
                             item.update()
                             needs_update = True
                             
                             if is_next and self.auto_focus_checkbox.isChecked():
                                 canvas.smooth_center_on(item)
                                 
                 if needs_update:
                     graph.viewport().update()
        except: pass

    def highlight_flow_wire(self, flow_line, source_graph=None):
        graphs_to_search = [source_graph] if source_graph else []
        if not source_graph:
            for i in range(self.central_tabs.count()):
                w = self.central_tabs.widget(i)
                if isinstance(w, GraphWidget): graphs_to_search.append(w)
        
        try:
            parts = flow_line.replace("[FLOW]", "").strip().split(" -> ")
            if len(parts) != 2: return
            
            for graph in graphs_to_search:
                for item in graph.canvas.scene.items():
                    if isinstance(item, Wire) and item.start_port and item.end_port:
                        wire_from = f"{item.start_port.parent_node.node.node_id}:{item.start_port.name}"
                        wire_to = f"{item.end_port.parent_node.node.node_id}:{item.end_port.name}"
                        if wire_from == parts[0] and wire_to == parts[1]:
                            item.highlight_active()
                            self._trigger_aux_updates()
                            return 
        except: pass

    def set_node_running_state(self, node_id, is_running, source_graph=None):
        target_item = None
        target_graph = None
        
        if source_graph:
            target_item = self._find_node_in_graph(source_graph, node_id)
            if target_item: target_graph = source_graph
            
        if not target_item:
            for i in range(self.central_tabs.count()):
                graph = self.central_tabs.widget(i)
                if isinstance(graph, GraphWidget) and graph != source_graph:
                    target_item = self._find_node_in_graph(graph, node_id)
                    if target_item:
                        target_graph = graph
                        break
        
        if target_item:
            if is_running:
                for item in target_graph.canvas.scene.items():
                    if hasattr(item, '_is_running') and item._is_running and item != target_item:
                        item._is_running = False
                        # item._running_since = 0 # Keep for history?
                        item._is_fading = True
                        item._fade_start = QTime.currentTime().msecsSinceStartOfDay()
                        item.update()

                target_item._is_running = True
                target_item._running_since = QTime.currentTime().msecsSinceStartOfDay()
                target_item._is_fading = False 
                target_item.update()
                
                if hasattr(target_item, 'inputs'):
                    for port in target_item.inputs:
                        for wire in port.wires:
                            if hasattr(wire, 'highlight_fade'):
                                wire.highlight_fade()

                if self.auto_focus_checkbox.isChecked() and target_graph == self.get_current_graph():
                    target_graph.canvas.smooth_center_on(target_item)
            else:
                target_item._is_running = False
                target_item._is_fading = True
                target_item._fade_start = QTime.currentTime().msecsSinceStartOfDay()
                target_item.update()
                    
        self._trigger_aux_updates()

    def set_node_subgraph_state(self, node_id, is_active, source_graph=None):
        target_item = None
        if source_graph: target_item = self._find_node_in_graph(source_graph, node_id)
        
        if not target_item:
            for i in range(self.central_tabs.count()):
                graph = self.central_tabs.widget(i)
                if isinstance(graph, GraphWidget) and graph != source_graph:
                    target_item = self._find_node_in_graph(graph, node_id)
                    if target_item: break
        
        if target_item:
            target_item.update()
            
            if not is_active:
                target_item._is_running = False 
                target_item._is_fading = True
                target_item._fade_start = QTime.currentTime().msecsSinceStartOfDay()

                sub_path_raw = target_item.node.properties.get("graph_path")
                if sub_path_raw:
                    sub_path = os.path.normpath(os.path.abspath(sub_path_raw)) if sub_path_raw else None
                    for i in range(self.central_tabs.count()):
                        graph = self.central_tabs.widget(i)
                        if isinstance(graph, GraphWidget) and graph.file_path:
                            tab_path = os.path.normpath(os.path.abspath(graph.file_path))
                            if tab_path == sub_path:
                                self._clear_graph_highlights(graph)
                                break
        
        self._trigger_aux_updates()

    def set_node_waiting_state(self, node_id, is_waiting, duration=0, source_graph=None):
        target_item = None
        if source_graph: target_item = self._find_node_in_graph(source_graph, node_id)
        
        if not target_item:
            for i in range(self.central_tabs.count()):
                graph = self.central_tabs.widget(i)
                if isinstance(graph, GraphWidget) and graph != source_graph:
                    target_item = self._find_node_in_graph(graph, node_id)
                    if target_item: break
        
        if target_item:
            if is_waiting:
                target_item._is_waiting = True
                target_item._waiting_since = QTime.currentTime().msecsSinceStartOfDay()
                target_item._waiting_duration = duration
                target_item.update()
            else:
                target_item._is_waiting = False
                target_item.update()

    def set_node_error_state(self, node_id, is_error, message="", source_graph=None):
        target_item = None
        if source_graph: target_item = self._find_node_in_graph(source_graph, node_id)
        
        if not target_item:
            for i in range(self.central_tabs.count()):
                graph = self.central_tabs.widget(i)
                if isinstance(graph, GraphWidget) and graph != source_graph:
                    target_item = self._find_node_in_graph(graph, node_id)
                    if target_item: break
        
        if target_item:
            if is_error:
                target_item._is_error = True
                target_item._error_message = message
                # Clear running/waiting states to avoid visual conflict
                target_item._is_running = False
                target_item._is_waiting = False
                target_item.update()
                
                # Auto-Focus on error
                if source_graph and self.auto_focus_checkbox.isChecked():
                     source_graph.canvas.smooth_center_on(target_item)
            else:
                target_item._is_error = False
                target_item.update()

    def _find_node_in_graph(self, graph, node_id):
        s_node_id = str(node_id)
        for item in graph.canvas.scene.items():
            if isinstance(item, NodeWidget) and item.node and str(item.node.node_id) == s_node_id:
                return item
        return None

    def _clear_graph_highlights(self, graph):
        if not graph or not graph.canvas or not graph.canvas.scene: return
        
        try:
            if hasattr(graph, 'bridge') and graph.bridge:
                graph.bridge.clear()
        except (BrokenPipeError, EOFError, ConnectionResetError, OSError):
            pass

        for item in graph.canvas.scene.items():
            if hasattr(item, '_is_active'):
                 item._is_active = False 
            
            if hasattr(item, '_is_running'):
                 item._is_running = False
                 item._running_since = 0
                 # Clear ALL visual effects immediately (no fading on stop)
                 if hasattr(item, '_is_fading'): item._is_fading = False
                 if hasattr(item, '_is_fading_blue'): item._is_fading_blue = False
                 if hasattr(item, '_is_pulsing_blue'): item._is_pulsing_blue = False
                 if hasattr(item, '_is_waiting'): item._is_waiting = False
                 if hasattr(item, '_is_error'): item._is_error = False
                 if hasattr(item, '_is_next'): item._is_next = False
                 item.update()
            elif hasattr(item, 'start_port'): # Wire
                 if hasattr(item, '_is_active'): item._is_active = False
                 if hasattr(item, '_is_fading'): item._is_fading = False
                 item.update()

        if hasattr(self, '_current_running_node'):
             self._current_running_node = None
             
        self.update_tab_icons()
        self._trigger_aux_updates()

    def _trigger_aux_updates(self):
        if hasattr(self, 'minimap'): self.minimap.update()
        if hasattr(self, 'miniworld'): self.miniworld.update()

    def update_execution_ui(self):
        graph = self.get_current_graph()
        if not graph:
            self.run_action.setEnabled(True)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)
            return
        state = graph.execution_state
        state = graph.execution_state
        is_running = (state == graph.STATE_RUNNING)
        is_paused = (state == graph.STATE_PAUSED)
        is_stopped = (state == graph.STATE_STOPPED)
        
        # Run: Enabled if Stopped or Paused
        self.run_action.setEnabled(is_stopped or is_paused)
        
        # Pause: Enabled only if Running
        self.pause_action.setEnabled(is_running)
        
        # Stop: Enabled if Running or Paused
        self.stop_action.setEnabled(is_running or is_paused)
        
        # Step: Enabled if Running or Paused (User: "disabled till we run")
        # Technically 'running' usually means auto-flow, but stepping is most useful when Paused.
        # User said "disabled till we run", implying they should be enabled during execution session.
        self.step_action.setEnabled(is_running or is_paused)
        self.step_over_action.setEnabled(is_running or is_paused)
        self.step_back_action.setEnabled(is_running or is_paused)

    def update_tab_icons(self):
        from PyQt6.QtWidgets import QStyle
        from PyQt6.QtGui import QColor
        style = self.style()
        tab_bar = self.central_tabs.tabBar()
        for i in range(self.central_tabs.count()):
            widget = self.central_tabs.widget(i)
            if isinstance(widget, GraphWidget):
                if widget.execution_state == widget.STATE_RUNNING:
                    icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
                    tab_bar.setTabTextColor(i, QColor("#006400"))  # Dark Green
                elif widget.execution_state == widget.STATE_PAUSED:
                    icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPause)
                    tab_bar.setTabTextColor(i, QColor("#B8860B"))  # Dark Goldenrod
                else:
                    icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaStop)
                    tab_bar.setTabTextColor(i, QColor())  # Reset to default
                self.central_tabs.setTabIcon(i, icon)

    def update_speed(self):
        delay = 5.0 * (1.0 - (self.speed_slider.value() / 100.0))
        graph = self.get_current_graph()
        if graph: graph.set_speed(delay)

    def on_back_trace_changed(self, checked):
        """Syncs the Back Trace checkbox state to the current graph's bridge."""
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'bridge') and graph.bridge:
            graph.bridge.set("_SYSTEM_BACK_TRACE_ENABLED", checked, "MainUI")
            if not checked:
                self.statusBar().showMessage("Back Trace disabled. History cleared.", 3000)
            else:
                if hasattr(graph, 'engine') and graph.engine:
                    graph.engine.history.clear()
                self.statusBar().showMessage("Back Trace enabled.", 3000)

    def on_show_trace_changed(self, checked):
        """Syncs Global Trace flag to bridge."""
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'bridge') and graph.bridge:
            graph.bridge.set("_SYSTEM_TRACE_ENABLED", checked, "MainUI")
            self.statusBar().showMessage(f"Trace {'Enabled' if checked else 'Disabled'}.", 2000)

    def on_trace_subgraphs_changed(self, checked):
        """Syncs Sub-Graph Trace flag to bridge."""
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'bridge') and graph.bridge:
            graph.bridge.set("_SYSTEM_TRACE_SUBGRAPHS", checked, "MainUI")
            self.statusBar().showMessage(f"Sub-Graph Trace {'Enabled' if checked else 'Disabled'}.", 2000)
