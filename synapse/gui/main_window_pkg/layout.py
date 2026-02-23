from PyQt6.QtWidgets import QDockWidget, QTabWidget, QTextEdit, QVBoxLayout, QWidget, QCheckBox, QSlider, QLabel, QApplication, QHBoxLayout
from PyQt6.QtCore import Qt
from synapse.gui.node_library.widget import NodeLibrary
from synapse.gui.properties_panel import PropertiesPanel
from synapse.gui.project_panel import ProjectPanel
from synapse.gui.minimap import MinimapWidget
from synapse.gui.miniworld import MiniworldWidget
from synapse.gui.console_widget import SearchableConsoleWidget

class LayoutMixin:
    def create_docks(self):
        # 1. Node Library Dock (Left)
        self.library_dock = QDockWidget("Node Library", self)
        self.library_dock.setObjectName("LibraryDock")
        self.library_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.node_library = NodeLibrary()
        self.library_dock.setWidget(self.node_library)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.library_dock)
        
        # 2. Properties Dock (Right)
        self.props_dock = QDockWidget("Project/Properties", self)
        self.props_dock.setObjectName("PropertiesDock")
        self.props_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Create Tab Widget for Properties & Project
        self.right_tabs = QTabWidget()
        
        self.properties_panel = PropertiesPanel()
        self.right_tabs.addTab(self.properties_panel, "Node")
        
        self.project_panel = ProjectPanel(self)
        self.project_panel.dataChanged.connect(self.on_project_data_changed)
        self.right_tabs.addTab(self.project_panel, "Project")
        
        self.props_dock.setWidget(self.right_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.props_dock)

        # 3. Bottom Dock (Console, Debug, Minimap)
        self.bottom_dock = QDockWidget("Output & Tools", self)
        self.bottom_dock.setObjectName("BottomDock")
        self.bottom_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)
        self.setup_bottom_dock()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)
        
        # self.tabifyDockWidget(self.library_dock, self.bottom_dock) # Just in case, but usually bottom is separate 
        # Make Library active by default
        self.library_dock.raise_()

        # Add View Actions if menu exists
        if hasattr(self, 'view_menu'):
            self.view_menu.addAction(self.library_dock.toggleViewAction())
            self.view_menu.addAction(self.props_dock.toggleViewAction())
            self.view_menu.addAction(self.bottom_dock.toggleViewAction())

    def create_central_widget(self):
        self.central_tabs = QTabWidget()
        self.central_tabs.setTabsClosable(True)
        self.central_tabs.setMovable(True)
        self.setCentralWidget(self.central_tabs)
        
        # Connect tab close
        self.central_tabs.tabCloseRequested.connect(self.close_tab)
        self.central_tabs.currentChanged.connect(self.on_tab_changed)
        
        # Context Menu for Tabs
        self.central_tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.central_tabs.customContextMenuRequested.connect(self.show_tab_context_menu)

    def show_tab_context_menu(self, point):
        index = self.central_tabs.tabBar().tabAt(point)
        if index == -1: return
        
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Others", self)
        def close_others():
             # Close in reverse order to keep index validity for lower indices, 
             # but simpler to just identify widgets to close first
             to_close = []
             for i in range(self.central_tabs.count()):
                 if i != index:
                     to_close.append(self.central_tabs.widget(i))
             for w in to_close:
                 idx = self.central_tabs.indexOf(w)
                 self.close_tab(idx)
        close_others_action.triggered.connect(close_others)
        menu.addAction(close_others_action)
        
        menu.addSeparator()
        
        copy_path_action = QAction("Copy Full Path", self)
        def copy_path():
            w = self.central_tabs.widget(index)
            if hasattr(w, 'file_path') and w.file_path:
                QApplication.clipboard().setText(w.file_path)
        copy_path_action.triggered.connect(copy_path)
        menu.addAction(copy_path_action)
        
        menu.exec(self.central_tabs.mapToGlobal(point))

    def close_tab(self, index):
        widget = self.central_tabs.widget(index)
        if widget:
            # Check for unsaved changes
            if getattr(widget, 'is_modified', False):
                 from PyQt6.QtWidgets import QMessageBox
                 res = QMessageBox.question(self, "Unsaved Changes", 
                                          "This graph has unsaved changes. Save before closing?",
                                          QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
                 if res == QMessageBox.StandardButton.Cancel:
                     return
                 if res == QMessageBox.StandardButton.Save:
                     self.save_graph(widget)
            
            if hasattr(widget, 'unregister_live_graph'):
                widget.unregister_live_graph()
            
            self.central_tabs.removeTab(index)
            widget.deleteLater()
            
            # [FIX] Save settings immediately so closed tabs stay closed
            if hasattr(self, 'save_settings'):
                self.save_settings()
            
    def on_tab_changed(self, index):
        # 1. Disconnect old signal safely
        if hasattr(self, '_current_graph_conn') and self._current_graph_conn:
            try:
                old_conn = self._current_graph_conn
                
                # Try to get signal safely
                if hasattr(old_conn, 'node_selection_changed'):
                     sig = old_conn.node_selection_changed
                     if sig and hasattr(sig, 'disconnect'):
                        try:
                            sig.disconnect(self.update_properties)
                        except (TypeError, RuntimeError, AttributeError):
                            pass 
                elif hasattr(old_conn, 'canvas') and hasattr(old_conn.canvas.scene, 'selectionChanged'):
                     # Fallback to direct scene connection if widget signal missing
                     try:
                         old_conn.canvas.scene.selectionChanged.disconnect(self.update_properties)
                     except: pass
            except (RuntimeError, AttributeError):
                pass # old_conn might be half-destroyed
            
            self._current_graph_conn = None
            
        # 2. Connect new signal safely
        widget = self.central_tabs.widget(index)
        
        if hasattr(self, 'show_names_checkbox'):
            show_names = self.show_names_checkbox.isChecked()
            if hasattr(widget, 'canvas') and widget.canvas.scene:
                for item in widget.canvas.scene.items():
                    if hasattr(item, 'set_display_mode'):
                        item.set_display_mode(show_names)
        
        if hasattr(self, 'toggle_magnifier_action'):
            mag_checked = self.toggle_magnifier_action.isChecked()
            if hasattr(widget, 'canvas') and hasattr(widget.canvas, 'set_magnifier_enabled'):
                widget.canvas.set_magnifier_enabled(mag_checked)
                
            # Sync Slider Value
            if hasattr(self, 'magnifier_size_slider'):
                radius = self.magnifier_size_slider.value()
                if hasattr(widget, 'canvas') and hasattr(widget.canvas, 'set_magnifier_radius'):
                    widget.canvas.set_magnifier_radius(radius)



        from synapse.gui.graph_widget import GraphWidget
        if isinstance(widget, GraphWidget):
            try:
                connected = False
                if hasattr(widget, 'node_selection_changed'):
                    sig = widget.node_selection_changed
                    if hasattr(sig, 'connect'):
                        try:
                            sig.connect(self.update_properties)
                            self._current_graph_conn = widget
                            connected = True
                        except (TypeError, RuntimeError, AttributeError):
                            pass
                
                # Fallback to direct scene connection if top-level signal failed
                if not connected and hasattr(widget, 'canvas') and hasattr(widget.canvas.scene, 'selectionChanged'):
                    try:
                        widget.canvas.scene.selectionChanged.connect(self.update_properties)
                        self._current_graph_conn = widget
                    except: pass

                # Restore view state
                if hasattr(widget, 'restore_view_state'):
                    widget.restore_view_state()

            except (RuntimeError, AttributeError):
                pass
            except Exception:
                pass
            
        self.broadcast_graph_modified()
        self.update_execution_ui()
        self.update_tab_icons()
        self.update_properties()
        self.update_project_panel() # [NEW] Sync Project Panel

    def update_properties(self):
        graph = self.get_current_graph()
        if not graph:
            self.properties_panel.load_node(None)
            return

        selected = graph.get_selected_nodes()
        if len(selected) == 1:
            self.properties_panel.load_node(selected[0])  # Pass widget, not just logic node
        else:
            self.properties_panel.load_node(None)

    def update_project_panel(self):
        """Syncs the Project Panel with the current graph's metadata."""
        graph = self.get_current_graph()
        if not graph:
            # Clear or disable?
            return
            
        if not hasattr(graph, 'project_metadata'):
            graph.project_metadata = {}
            
        meta = graph.project_metadata
        
        # Block signals to prevent feedback loop
        self.project_panel.blockSignals(True)
        try:
            self.project_panel.set_name(meta.get("project_name", ""))
            self.project_panel.set_version(meta.get("project_version", "1.0.0"))
            self.project_panel.set_category(meta.get("project_category", ""))
            self.project_panel.set_description(meta.get("project_description", ""))
            # Variables?
            # meta.get("variables", {}) ? Or are global variables stored elsewhere?
            # Usually variables involved in the graph are in graph.bridge or graph.variables?
            # ProjectPanel seems to edit 'project metadata' variables, which might be distinct 
            # from runtime variables. Let's assume they are meta-variables for now or 
            # initial global values.
            # checks project_panel.py -> it has a table.
            self.project_panel.set_variables(meta.get("variables", {}))
        except Exception as e:
            print(f"Error updating project panel: {e}")
        finally:
            self.project_panel.blockSignals(False)

    def setup_bottom_dock(self):
        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_widget)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # -- Tabs --
        self.tabs = QTabWidget()
        
        # Console Tab (Searchable)
        self.console_output = SearchableConsoleWidget()
        self.tabs.addTab(self.console_output, "Console")
        
        # Debug Tab (HTML supported)
        self.debug_output = QTextEdit()
        self.debug_output.setReadOnly(True)
        self.tabs.addTab(self.debug_output, "Debug")
        
        # Minimap Tab
        self.minimap = MinimapWidget(self)
        self.tabs.addTab(self.minimap, "Minimap")
        
        # Miniworld Tab
        self.miniworld = MiniworldWidget(self)
        self.tabs.addTab(self.miniworld, "Miniworld")
        
        self.bottom_layout.addWidget(self.tabs)
        self.bottom_dock.setWidget(self.bottom_widget)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            if hasattr(self, '_prev_dock_states'):
                for dock, was_visible in self._prev_dock_states.items():
                    dock.setVisible(was_visible)
            if hasattr(self, '_prev_toolbar_visible'):
                self.main_toolbar.setVisible(self._prev_toolbar_visible)
            self.statusBar().show()
        else:
            self._prev_dock_states = {
                self.library_dock: self.library_dock.isVisible(),
                self.props_dock: self.props_dock.isVisible(),
                self.bottom_dock: self.bottom_dock.isVisible()
            }
            self._prev_toolbar_visible = self.main_toolbar.isVisible()
            for dock in self._prev_dock_states:
                dock.setVisible(False)
            self.main_toolbar.setVisible(False)
            self.statusBar().hide()
            self.showFullScreen()

    def toggle_node_names(self, checked):
        from synapse.gui.node_widget.widget import NodeWidget
        for i in range(self.central_tabs.count()):
            widget = self.central_tabs.widget(i)
            # Check for canvas attribute safely
            if hasattr(widget, 'canvas') and widget.canvas and widget.canvas.scene:
                for item in widget.canvas.scene.items():
                    if isinstance(item, NodeWidget):
                        item.set_display_mode(checked)

    def on_hide_tooltips_changed(self, checked):
        # Update styling or global setting for tooltips
        pass

    def on_project_data_changed(self):
        # This is called when the USER edits the panel. We write TO the graph.
        graph = self.get_current_graph()
        if graph:
            if not hasattr(graph, 'project_metadata'):
                graph.project_metadata = {}
            
            # Pull from Panel
            graph.project_metadata["project_name"] = self.project_panel.get_name()
            graph.project_metadata["project_version"] = self.project_panel.get_version()
            graph.project_metadata["project_category"] = self.project_panel.get_category()
            graph.project_metadata["project_description"] = self.project_panel.get_description()
            graph.project_metadata["variables"] = self.project_panel.get_variables()
            
            graph.is_modified = True
            # We need to trigger title update, which broadcast_graph_modified does
            if hasattr(self, 'broadcast_graph_modified'):
                self.broadcast_graph_modified()
