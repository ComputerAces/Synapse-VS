import sys
import os
import json
import multiprocessing

from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSignal

from synapse.gui.graph_widget import GraphWidget
from synapse.core.loader import load_favorites_into_registry
from synapse.nodes.registry import NodeRegistry

# Import Mixins
from .layout import LayoutMixin
from .actions import ActionsMixin
from .menus import MenusMixin
from .file_ops import FileOperationsMixin
from .execution import ExecutionMixin
from synapse.gui.dialogs.custom_form import CustomFormDialog # [NEW]

class MainWindow(QMainWindow, LayoutMixin, ActionsMixin, MenusMixin, FileOperationsMixin, ExecutionMixin):
    subgraph_saved = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapse VS - Architect")
        self.resize(1200, 800)
        
        # 1. Shared Manager (Process-Safe State)
        self.shared_manager = multiprocessing.Manager()
        
        # 2. UI Setup
        self.settings_file = "user_settings.json"
        self.last_settings = {}
        
        # 3. Create Actions & Menus (Order Matters)
        self.create_actions()
        self.create_menu()
        self.create_toolbar()

        # [CRITICAL FIX] Load Nodes & Plugins BEFORE Graph Restoration
        # Trigger discovery of nodes so deserialization works
        import synapse.nodes
        synapse.nodes.discover_plugins() 
        load_favorites_into_registry()
        if hasattr(self, 'node_library'):
             self.node_library.populate_library()
        
        # 4. Create Layout
        self.create_central_widget() # [NEW]
        self.create_docks()
        
        # 5. Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        self.thread_count_label = QLabel("Services: 0")
        self.env_count_label = QLabel("Environments: 0")
        self.status_bar.addPermanentWidget(self.env_count_label)
        self.status_bar.addPermanentWidget(self.thread_count_label)
        
        # 6. Load Settings & Restore Session
        settings = self.load_settings()
        self.update_recent_menu() # [NEW] Populate recent menu
        if not self.restore_session(settings):
            self.new_graph()
            
        # 7. Apply Geometry (After docks created)
        self.setAcceptDrops(True) # [NEW] Enable Drag & Drop
        if "window_geometry" in settings:
            from PyQt6.QtCore import QByteArray
            self.restoreGeometry(QByteArray.fromHex(settings["window_geometry"].encode()))
        if "window_state" in settings:
            from PyQt6.QtCore import QByteArray
            self.restoreState(QByteArray.fromHex(settings["window_state"].encode()))
            
        # [LAYOUT FIX] Ensure Bottom Dock is actually at the bottom (Overrides saved state if merged)
        # The user requested this to be moved back to the bottom.
        if hasattr(self, 'bottom_dock'):
             self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)
            
        # 8. Setup Timers
        self.setup_autosave()
        
        # Polling Timer (for Bridge State & Execution UI)
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_bridge_states)
        self.poll_timer.timeout.connect(self.check_execution_state)
        self.poll_timer.start(50) # 20Hz UI refresh


    def get_current_graph(self):
        """Helper to return the currently active GraphWidget."""
        if self.central_tabs.count() == 0:
            return None
        return self.central_tabs.currentWidget()

    def poll_bridge_states(self):
        """Polls the bridge for persistent highlights, form requests, and bubbled triggers."""
        try:
            # 0. Check for Form Requests across ALL graphs (Foreground & Background)
            # This ensures even background tabs can popup a request
            for i in range(self.central_tabs.count()):
                g = self.central_tabs.widget(i)
                if isinstance(g, GraphWidget) and hasattr(g, 'bridge') and g.bridge:
                    form_req = g.bridge.get("SHOW_FORM")
                    if form_req:
                        # Handle Form
                        req_id = form_req.get("id")
                        title = form_req.get("title", "Form")
                        schema = form_req.get("schema", [])
                        
                        # Clear request immediately so we don't open multiple
                        g.bridge.set("SHOW_FORM", None, "MainPoller") 
                        
                        # Open Dialog
                        dlg = CustomFormDialog(title, schema, self)
                        if dlg.exec():
                            data = dlg.get_data()
                        else:
                            # Cancelled -> Empty dict or None? Node handles empty.
                            data = {}
                            
                        # Send Response
                        resp_key = f"FORM_RESPONSE_{req_id}"
                        g.bridge.set(resp_key, data, "MainPoller")

                    # [NEW] Message Box Handling
                    msg_req = g.bridge.get("SHOW_MESSAGE")
                    if msg_req:
                        # Handle Message
                        req_id = msg_req.get("id")
                        title = msg_req.get("title", "Message")
                        text = msg_req.get("text", "")
                        icon_type = msg_req.get("type", "info") # info, warning, error, question
                        buttons = msg_req.get("buttons", "ok") # ok, yes_no
                        
                        # Clear request
                        g.bridge.set("SHOW_MESSAGE", None, "MainPoller")
                        
                        # Show MessageBox
                        from PyQt6.QtWidgets import QMessageBox
                        
                        icon = QMessageBox.Icon.Information
                        if icon_type == "warning": icon = QMessageBox.Icon.Warning
                        elif icon_type == "error": icon = QMessageBox.Icon.Critical
                        elif icon_type == "question": icon = QMessageBox.Icon.Question
                        
                        btns = QMessageBox.StandardButton.Ok
                        if buttons == "yes_no":
                            btns = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        elif buttons == "ok_cancel":
                            btns = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                            
                        # Run Dialog
                        res = QMessageBox.information(self, title, text, btns) if icon_type == "info" else \
                              QMessageBox.warning(self, title, text, btns) if icon_type == "warning" else \
                              QMessageBox.critical(self, title, text, btns) if icon_type == "error" else \
                              QMessageBox.question(self, title, text, btns)
                        
                        # Map Result
                        res_str = "ok"
                        if res == QMessageBox.StandardButton.Yes: res_str = "yes"
                        elif res == QMessageBox.StandardButton.No: res_str = "no"
                        elif res == QMessageBox.StandardButton.Cancel: res_str = "cancel"
                        
                        # Send Response
                        resp_key = f"MESSAGE_RESPONSE_{req_id}"
                        g.bridge.set(resp_key, res_str, "MainPoller")

                    # [NEW] Text Display Dialog Handling
                    text_req = g.bridge.get("SHOW_TEXT_DIALOG")
                    if text_req:
                        req_id = text_req.get("id")
                        title = text_req.get("title", "Text Output")
                        content = text_req.get("text", "")
                        
                        g.bridge.set("SHOW_TEXT_DIALOG", None, "MainPoller")
                        
                        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
                        
                        dlg = QDialog(self)
                        dlg.setWindowTitle(title)
                        dlg.resize(600, 400)
                        layout = QVBoxLayout(dlg)
                        
                        text_edit = QTextEdit()
                        text_edit.setPlainText(str(content))
                        text_edit.setReadOnly(True)
                        layout.addWidget(text_edit)
                        
                        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
                        btns.accepted.connect(dlg.accept)
                        layout.addWidget(btns)
                        
                        dlg.exec()
                        
                        # Response (just to unblock)
                        g.bridge.set(f"TEXT_RESPONSE_{req_id}", "ok", "MainPoller")


            graph = self.get_current_graph()
            
            # 1. Update Current Minimap for animations
            if hasattr(self, 'minimap'):
                self.minimap.update_minimap()
                
            # [NEW] Update Standalone Minimaps
            if hasattr(self, 'minimap_windows'):
                # Prune dead windows
                self.minimap_windows = [w for w in self.minimap_windows if w.isVisible()]
                for w in self.minimap_windows:
                    w.minimap_widget.update_minimap()
            
            # 2. Update Miniworld Slots
            if hasattr(self, 'miniworld'):
                self.miniworld.update_maps()

            if not graph or not hasattr(graph, 'bridge') or not graph.bridge: 
                return
            
            # 3. Pull Highlights from Bridge
            highlights = graph.bridge.get("HIGHLIGHT_NODES", [])
            if highlights:
                for node_id in highlights:
                    self.set_node_running_state(node_id, True, source_graph=graph)
                graph.bridge.set("HIGHLIGHT_NODES", [], "MainPoller")

            # 4. Update Node/Wire Visuals for animations
            if hasattr(graph, 'canvas') and graph.canvas.scene:
                for item in graph.canvas.scene.items():
                    if hasattr(item, 'node') and item.node: # [FIX] Check item.node first
                        node_id = item.node.node_id
                        
                        # Service and SubGraph states
                        if graph.bridge.get(f"{node_id}_IsServiceRunning") or graph.bridge.get(f"{node_id}_SubGraphActivity"):
                            item.update()
                        
                        # Smooth animation for running/fading nodes
                        if getattr(item, "_is_running", False) or getattr(item, "_is_fading", False) or getattr(item, "_is_waiting", False):
                            item.update()
                    elif hasattr(item, 'start_port'): # Wire
                        if getattr(item, "_is_running", False) or getattr(item, "_is_fading", False):
                            item.update()
            
            # 5. Update Thread/Service/Environment Count Labels
            if hasattr(graph, 'engine') and graph.engine:
                count = len(graph.engine.service_registry)
                self.thread_count_label.setText(f"Services: {count}")
                
            # Global Environment Count
            env_count = 0
            for i in range(self.central_tabs.count()):
                w = self.central_tabs.widget(i)
                if isinstance(w, GraphWidget) and w.execution_state == w.STATE_RUNNING:
                    env_count += 1
            
            # Plus active services/sub-processes across ALL graphs
            for i in range(self.central_tabs.count()):
                w = self.central_tabs.widget(i)
                if isinstance(w, GraphWidget) and hasattr(w, 'engine') and w.engine:
                    env_count += len(w.engine.dispatcher.active_processes)
            
            self.env_count_label.setText(f"Environments: {env_count}")
            
        except BrokenPipeError:
            # Manager likely dead or shutting down
            pass
        except Exception as e:
            # logger.error(f"Polling Error: {e}")
            pass

    def check_execution_state(self):
        # Update UI based on state changes that might happen async
        # (Though most updates are event-driven via signals in ExecutionMixin)
        pass 
        
    def closeEvent(self, event):
        """Handle application closure with individual unsaved changes check."""
        i = 0
        while i < self.central_tabs.count():
            w = self.central_tabs.widget(i)
            if isinstance(w, GraphWidget) and getattr(w, 'is_modified', False):
                # Focus the tab so user knows which one it is
                self.central_tabs.setCurrentIndex(i)
                
                name = w.project_metadata.get("project_name") 
                if not name and w.file_path: name = os.path.basename(w.file_path)
                if not name: name = "Untitled"
                
                reply = QMessageBox.question(
                    self, 
                    "Unsaved Changes", 
                    f"The graph '{name}' has unsaved changes.\nDo you want to save it before exiting?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Save
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                elif reply == QMessageBox.StandardButton.Save:
                    self.save_graph(w)
                # If discard, just continue loop
            i += 1
                
        # Save Settings (always)
        self.save_settings()
        
        # Shutdown Managers
        try:
             self.stop_all_graphs()
             self.shared_manager.shutdown()
        except: pass
        
        event.accept()
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.endswith(".syp"):
                self.open_tab(f)
                self.update_recent_menu() # Refresh menu
        event.accept()
