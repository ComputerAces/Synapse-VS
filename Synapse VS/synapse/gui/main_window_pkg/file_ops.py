import os
import json
import uuid
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt6.QtCore import QTimer

from synapse.gui.graph_widget import GraphWidget
from synapse.gui.node_widget.widget import NodeWidget
from synapse.nodes.registry import NodeRegistry

class FileOperationsMixin:
    def new_graph(self):
        new_tab = GraphWidget()
        def create_node(type_name, x, y):
            node_class = NodeRegistry.get_node_class(type_name)
            if node_class:
                widget = NodeWidget(type_name)
                widget.setPos(x, y)
                logic = node_class(str(uuid.uuid4()), type_name, None)
                widget.node = logic
                new_tab.canvas.configure_node_ports(widget, type_name)
                new_tab.canvas.scene.addItem(widget)
        create_node("Start Node", -400, 0)
        create_node("Return Node", 400, 0)
        new_tab.modified.connect(self.broadcast_graph_modified)
        if hasattr(self, 'subgraph_saved'):
            self.subgraph_saved.connect(new_tab.on_subgraph_saved)
        index = self.central_tabs.addTab(new_tab, "Untitled")
        self.central_tabs.setCurrentIndex(index)
        self.update_tab_icons()
        self.update_execution_ui()
        self.statusBar().showMessage("New Graph Created")
        
        # [FIX] Save settings immediately so this tab is remembered
        self.save_settings()

    def open_graph(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Graph", "", "Synapse Project (*.syp);;JSON Files (*.json)")
        if file_path:
            self.open_tab(file_path)

    def open_tab(self, file_path):
        # Helper to open a tab (internal or external)
        file_path = os.path.abspath(file_path)
        
        for i in range(self.central_tabs.count()):
            widget = self.central_tabs.widget(i)
            if isinstance(widget, GraphWidget) and widget.file_path:
                if os.path.abspath(widget.file_path) == file_path:
                    self.central_tabs.setCurrentIndex(i)
                    return widget
        try:
            with open(file_path, "r") as f:
                raw_data = f.read()
                data = json.loads(raw_data)
            
            # [SCHEMA VALIDATION & MIGRATION]
            from synapse.core.schema import validate_graph, migrate_graph
            is_valid, error = validate_graph(data)
            if not is_valid:
                QMessageBox.warning(self, "Invalid Graph", f"Graph validation failed: {error}")
                return None
 
            data, was_modified = migrate_graph(data)
 
            # [UI FIX] Create tab WITHOUT parent first to avoid ghosting if load fails
            new_tab = GraphWidget(None, manager=self.shared_manager)
            try:
                new_tab.set_file_path(file_path)
                was_pruned = new_tab.deserialize(data)
                new_tab.modified.connect(self.broadcast_graph_modified)
                if hasattr(self, 'subgraph_saved'):
                    self.subgraph_saved.connect(new_tab.on_subgraph_saved)
                
                # [SAFETY CHECK] Detect Load Failure
                node_count = len([i for i in new_tab.canvas.scene.items() if hasattr(i, 'node')])
                if node_count == 0 and len(raw_data) > 500:
                    print(f"[ERROR] Graph Loaded 0 Nodes from {len(raw_data)} bytes! Disabling Auto-Save.")
                    self.statusBar().showMessage("⚠️ Critical: Graph failed to load nodes. Auto-save disabled.", 10000)
                    new_tab.is_modified = False 
                    new_tab._auto_save_disabled = True # Flag to block save
                    was_modified = False 
                    was_pruned = False
                
                if was_modified or was_pruned:
                    new_tab.is_modified = True
                    
                    filename = os.path.basename(file_path)
                    msg = f"The graph '{filename}' was automatically patched during load."
                    
                    reasons = []
                    if was_modified:
                        reasons.append(f"• Migrated to schema v{data.get('version', '2.1.0')}")
                    if was_pruned:
                        reasons.append("• Removed dead properties (cleanup)")
                    
                    msg += "\n\n" + "\n".join(reasons)
                    msg += "\n\nIt is recommended to save the graph now to maintain these changes."
                    
                    self.statusBar().showMessage(f"Graph Repaired: {', '.join(reasons).replace('• ', '')}", 5000)
                    
                    res = QMessageBox.information(self, "Graph Repair & Migration", msg,
                        QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Ignore)
                    
                    if res == QMessageBox.StandardButton.Save:
                        QTimer.singleShot(500, lambda: self.save_graph(new_tab))
                
                # [UI FIX] Set parent ONLY when adding to central widget
                new_tab.setParent(self)
                index = self.central_tabs.addTab(new_tab, os.path.basename(file_path))
                self.central_tabs.setTabToolTip(index, file_path)
                self.central_tabs.setCurrentIndex(index)
                
                QTimer.singleShot(100, new_tab.clear_modified)
                self.save_settings()
                return new_tab

            except Exception as e:
                # Cleanup if logic failed
                new_tab.deleteLater()
                raise e
                
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Graph Format Error", f"The file '{os.path.basename(file_path)}' contains invalid JSON.\n\nError: {e}")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to open '{os.path.basename(file_path)}':\n\n{str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def save_graph(self, graph=None):
        if not graph: graph = self.get_current_graph()
        if not graph: return
        
        # [SAFETY] Check for disabled save (load failure)
        if getattr(graph, '_auto_save_disabled', False):
            res = QMessageBox.warning(self, "Potential Data Loss", 
                "This graph failed to load correctly (0 nodes found vs file size).\n"
                "Saving now will OVERWRITE the file with an empty graph.\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res != QMessageBox.StandardButton.Yes:
                return
            # Allow save only if user explicitly confirms
            graph._auto_save_disabled = False

        if not graph.file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Graph", "", "Synapse Project (*.syp)")
            if not file_path: return
            graph.set_file_path(file_path)
        data = graph.serialize()
        try:
            from synapse.utils.file_utils import safe_save_graph
            if safe_save_graph(graph.file_path, data):
                graph.clear_modified()
            
            # [HOT RELOAD] Notify other tabs that this subgraph was updated
            if hasattr(self, 'subgraph_saved'):
                self.subgraph_saved.emit(os.path.abspath(graph.file_path))
                
            self.statusBar().showMessage(f"Saved to {graph.file_path}", 3000)
            project_name = graph.project_metadata.get("project_name", "").strip()
            display_name = project_name if project_name else os.path.basename(graph.file_path)
            idx = self.central_tabs.indexOf(graph)
            if idx != -1: self.central_tabs.setTabText(idx, display_name)
            self.setWindowTitle(f"Synapse VS - Architect - {display_name}")
            if hasattr(self, 'node_library'):
                if self.node_library.is_favorite(graph.file_path):
                    self.node_library.populate_library()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def save_graph_as(self):
        graph = self.get_current_graph()
        if not graph: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Graph As", "", "Synapse Project (*.syp)")
        if not file_path: return
        old_path = graph.file_path
        graph.set_file_path(file_path)
        # Clear disable flag for Save As (new file)
        if getattr(graph, '_auto_save_disabled', False):
             graph._auto_save_disabled = False
        self.save_graph(graph=graph)
        
        # [REMAP] Update Node Library (Favorites/Quick Links)
        if hasattr(self, 'node_library') and old_path:
            self.node_library.update_path(old_path, file_path)

    def import_subgraph(self):
        graph = self.get_current_graph()
        if not graph: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Subgraph", "", "Synapse Project (*.syp);;JSON Files (*.json)")
        if not file_path: return
        
        # 1. Register it temporarily so it behaves like a library node
        name = os.path.splitext(os.path.basename(file_path))[0]
        # Avoid collisions by adding a unique suffix if needed, but for now we'll just use the name
        
        # 2. Add to scene via the standard placement logic (or simulation of it)
        # We'll use the SubGraph Node base and configure it.
        node_class = NodeRegistry.get_node_class("SubGraph Node")
        if not node_class:
            QMessageBox.warning(self, "Error", "SubGraph Node class not found.")
            return

        node_id = str(uuid.uuid4())
        
        # Create Widget
        widget = NodeWidget(name)
        # Place at center or mouse pos? Standard is 0,0 or center of view.
        # Let's use center of view.
        view_center = graph.canvas.view.mapToScene(graph.canvas.view.rect().center())
        widget.setPos(view_center)
        
        # Create Logic
        logic = node_class(node_id, name, getattr(graph, 'bridge', None))
        logic.properties["graph_path"] = file_path
        
        # Rebuild ports from file
        try:
            logic.rebuild_ports() # This extracts ports from the .syp
        except Exception as e:
            print(f"Error rebuilding ports for {name}: {e}")

        widget.node = logic
        
        # Use the logic's own ports (which are now populated)
        graph.canvas.configure_node_ports(widget, "SubGraph Node")
        
        # Optional: update titles
        try:
            with open(file_path, 'r') as f:
                p_name = json.load(f).get("project_name", "").strip()
                if p_name: 
                    widget.set_user_name(p_name)
                    logic.name = p_name
        except: pass

        graph.canvas.scene.addItem(widget)
        graph.is_modified = True
        self.statusBar().showMessage(f"Imported Subgraph: {widget.name}", 3000)

    def save_all_tabs(self):
        saved_count = 0
        for i in range(self.central_tabs.count()):
            w = self.central_tabs.widget(i)
            if isinstance(w, GraphWidget):
                self.save_graph(w)
                saved_count += 1
        
        self.statusBar().showMessage(f"Save All: {saved_count} tabs saved.", 5000)

    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.autosave_timeout)

    def autosave_timeout(self):
        # [AUTO-SAVE CHECK]
        if hasattr(self, 'auto_save_checkbox') and not self.auto_save_checkbox.isChecked():
            return

        graph = self.get_current_graph()
        if graph and graph.file_path and not getattr(graph, '_auto_save_disabled', False): 
            # Only save if modified to prevent redundant writes (though timer is triggered by modify)
            if getattr(graph, 'is_modified', False):
                self.save_graph(graph)

    def load_settings(self):
        if not os.path.exists(self.settings_file): return {}
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            self.last_settings = settings
            if hasattr(self, 'speed_slider'):
                self.speed_slider.setValue(settings.get("speed", 100))
            
            # [UI STATE PERSISTENCE] Restore Toolbar Checkboxes
            if hasattr(self, 'hide_tooltips_checkbox'):
                self.hide_tooltips_checkbox.setChecked(settings.get("hide_tooltips", False))
                
            if hasattr(self, 'show_names_checkbox'):
                self.show_names_checkbox.setChecked(settings.get("show_names", True))
                
            if hasattr(self, 'auto_focus_checkbox'):
                self.auto_focus_checkbox.setChecked(settings.get("auto_focus", True))
                
            if hasattr(self, 'show_trace_checkbox'):
                self.show_trace_checkbox.setChecked(settings.get("show_trace", True))

            if hasattr(self, 'auto_save_checkbox'):
                self.auto_save_checkbox.setChecked(settings.get("auto_save", False))
                
            return settings
        except: return {}

    def broadcast_graph_modified(self):
        graph = self.get_current_graph()
        if not graph:
            self.setWindowTitle("Synapse VS - Architect")
            return
            
        is_modified = getattr(graph, 'is_modified', False)
        mod_mark = "*" if is_modified else ""
        
        project_name = graph.project_metadata.get("project_name", "")
        if not project_name and graph.file_path:
            project_name = os.path.basename(graph.file_path)
        if not project_name:
            project_name = "Untitled"
            
        self.setWindowTitle(f"Synapse VS - Architect - {project_name}{mod_mark}")
        
        # Update tab text
        idx = self.central_tabs.indexOf(graph)
        if idx != -1:
            self.central_tabs.setTabText(idx, f"{project_name}{mod_mark}")
            
        # Update Minimap
        if hasattr(self, 'minimap'):
            self.minimap.update_minimap()
        if hasattr(self, 'miniworld'):
            self.miniworld.update_maps()
            
        # [AUTO-SAVE] Trigger Timer
        if is_modified and hasattr(self, 'autosave_timer'):
            # Only start timer if enabled (efficient) or just let timer run and check in callback
            # Let's start it always, and check in callback (simpler logic)
            if not self.autosave_timer.isActive():
                 self.autosave_timer.start(3000) # 3 Seconds

    def save_settings(self):
        try:
            last_graphs = []
            session_state = {} # [SESSION RESTORE]
            
            for i in range(self.central_tabs.count()):
                widget = self.central_tabs.widget(i)
                if isinstance(widget, GraphWidget) and widget.file_path:
                    last_graphs.append(widget.file_path)
                    # Capture View State (Zoom/Pan)
                    if hasattr(widget, 'get_view_state'):
                        session_state[widget.file_path] = widget.get_view_state()
            
            settings = {
                "speed": self.speed_slider.value() if hasattr(self, 'speed_slider') else 100,
                "hide_tooltips": getattr(self.hide_tooltips_checkbox, 'isChecked', lambda: False)(),
                "show_names": getattr(self.show_names_checkbox, 'isChecked', lambda: True)(),
                "auto_focus": getattr(self.auto_focus_checkbox, 'isChecked', lambda: True)(),
                "show_trace": getattr(self.show_trace_checkbox, 'isChecked', lambda: True)(),
                "auto_save": getattr(self.auto_save_checkbox, 'isChecked', lambda: False)(),
                "last_graphs": last_graphs,
                "session_state": session_state, # Save View States
                "current_tab": max(0, self.central_tabs.currentIndex()),
                "miniworld_assignments": self.miniworld.get_assignments() if hasattr(self, 'miniworld') and hasattr(self.miniworld, 'get_assignments') else [],
                "window": {
                    "x": self.pos().x(), "y": self.pos().y(),
                    "width": self.size().width(), "height": self.size().height(),
                    "maximized": self.isMaximized()
                },
                "window_geometry": self.saveGeometry().toHex().data().decode(),
                "window_state": self.saveState().toHex().data().decode()
            }
            with open(self.settings_file, 'w') as f: json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def restore_session(self, settings):
        last_graphs = settings.get("last_graphs", [])
        session_state = settings.get("session_state", {}) # [SESSION RESTORE]
        
        missing_graphs = []
        restored_graphs = []
        
        for path in last_graphs:
            if os.path.exists(path):
                widget = self.open_tab(path)
                restored_graphs.append(path)
                # Restore View State
                if widget and hasattr(widget, 'set_view_state') and path in session_state:
                    widget.set_view_state(session_state[path])
            else:
                missing_graphs.append(path)
                
        if missing_graphs:
            from PyQt6.QtWidgets import QMessageBox
            names = [os.path.basename(p) for p in missing_graphs]
            msg = "The following graphs from your last session were missing and have been removed:\n\n" + "\n".join(names)
            QMessageBox.information(self, "Session Cleanup", msg)
            
            # update setting and save
            settings["last_graphs"] = restored_graphs
            for path in missing_graphs:
                if path in session_state:
                    del session_state[path]
            self.save_settings()
        
        # Restore active tab
        current_tab = settings.get("current_tab", 0)
        if 0 <= current_tab < self.central_tabs.count():
            self.central_tabs.setCurrentIndex(current_tab)
        
        # Restore Miniworld
        mini_assignments = settings.get("miniworld_assignments")
        if mini_assignments and hasattr(self, 'miniworld') and hasattr(self.miniworld, 'load_assignments'):
            def sync_open(path):
                # Check if already open
                for i in range(self.central_tabs.count()):
                    w = self.central_tabs.widget(i)
                    if isinstance(w, GraphWidget) and w.file_path == path:
                        return w
                
                # [FIX] Do NOT open_tab() here. If it was closed, it stays closed.
                # The miniworld slot will simply show as 'Offline'.
                return None
                
            self.miniworld.load_assignments(mini_assignments, sync_open)
            
        return self.central_tabs.count() > 0
