from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt

class ActionsMixin:
    def create_actions(self):
        from PyQt6.QtWidgets import QStyle, QApplication
        style = QApplication.style()

        # File Actions
        self.new_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "New Graph", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_graph)
        
        self.open_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open Graph...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_graph)
        
        self.save_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "&Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_graph)
        
        self.save_all_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save All", self)
        self.save_all_action.setShortcut("Ctrl+Alt+S")
        self.save_all_action.triggered.connect(self.save_all_tabs)
        
        self.save_as_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save &As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_graph_as)
        
        self.import_subgraph_action = QAction("Import Subgraph...", self)
        self.import_subgraph_action.triggered.connect(self.import_subgraph)
        
        self.exit_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton), "E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Edit Actions
        self.undo_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft), "Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.main_undo)

        self.redo_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight), "Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.main_redo)

        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.copy_selection)

        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(self.paste_selection)
        
        self.duplicate_action = QAction("Duplicate", self)
        self.duplicate_action.setShortcut("Ctrl+D")
        self.duplicate_action.triggered.connect(self.duplicate_selection)

        self.delete_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon), "Delete", self)
        self.delete_action.setShortcut("Del")
        self.delete_action.triggered.connect(self.delete_selection)
        
        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.select_all)

        # View Actions
        self.toggle_fullscreen_action = QAction("Toggle Fullscreen", self)
        self.toggle_fullscreen_action.setShortcut("F11")
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
        self.toggle_wire_legend_action = QAction("Wire Key", self)
        self.toggle_wire_legend_action.setShortcut("F1")
        self.toggle_wire_legend_action.setCheckable(True)
        self.toggle_wire_legend_action.triggered.connect(self.toggle_wire_legend)
        
        self.zoom_fit_action = QAction("Zoom to Fit", self)
        self.zoom_fit_action.setShortcut("F2")
        self.zoom_fit_action.triggered.connect(self.zoom_to_fit)
        
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.setShortcut("PgDown")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        
        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.setShortcut("PgUp")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        
        # Output Actions
        self.clear_console_action = QAction("Clear Console", self)
        self.clear_console_action.triggered.connect(self.clear_console)
        
        self.clear_debug_action = QAction("Clear Debug", self)
        self.clear_debug_action.triggered.connect(self.clear_debug)
        
        # Tools Actions
        self.add_tool_action = QAction("Add Current Graph to Library", self)
        self.add_tool_action.triggered.connect(self.add_as_tool)

        # Run Actions
        self.run_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Run", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.run_graph)
        
        self.pause_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_MediaPause), "Pause", self)
        self.pause_action.setShortcut("F6")
        self.pause_action.triggered.connect(self.pause_graph)
        self.pause_action.setEnabled(False)
        
        self.step_action = QAction("Step In", self)
        self.step_action.setShortcut("F10")
        self.step_action.triggered.connect(self.step_in_graph)
        self.step_action.setToolTip("Step In (Execute Next Node) - F10")

        self.step_back_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Step Back", self)
        self.step_back_action.setShortcut("Shift+F11")
        self.step_back_action.triggered.connect(self.step_back_graph)
        self.step_back_action.setToolTip("Step Back (Rewind One State) - Shift+F11")
        self.step_back_action.setEnabled(False)

        self.step_over_action = QAction("Step Over", self)
        self.step_over_action.setShortcut("F11")
        self.step_over_action.triggered.connect(self.step_over_graph)
        self.step_over_action.setToolTip("Step Over (Skip Next Node) - F11")

        self.stop_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_MediaStop), "Stop", self)
        self.stop_action.setShortcut("Shift+F5")
        self.stop_action.triggered.connect(self.stop_graph)
        self.stop_action.setEnabled(False)
        
        self.stop_all_action = QAction("Stop All Graphs", self)
        self.stop_all_action.triggered.connect(self.stop_all_graphs)

        self.toggle_magnifier_action = QAction("Magnifier", self)
        self.toggle_magnifier_action.setCheckable(True)
        self.toggle_magnifier_action.setShortcut("M")
        self.toggle_magnifier_action.setToolTip("Toggle Magnifier (Spy Tool) - M")
        self.toggle_magnifier_action.triggered.connect(self.toggle_magnifier)

    def toggle_magnifier(self, checked):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'canvas') and hasattr(graph.canvas, 'set_magnifier_enabled'):
            graph.canvas.set_magnifier_enabled(checked)

    def on_magnifier_size_changed(self, value):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'canvas') and hasattr(graph.canvas, 'set_magnifier_radius'):
            graph.canvas.set_magnifier_radius(value)

    def main_undo(self):

        graph = self.get_current_graph()
        if graph and hasattr(graph, 'undo_stack'):
            graph.undo_stack.undo()

    def main_redo(self):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'undo_stack'):
            graph.undo_stack.redo()

    def copy_selection(self):
        # Check if a text widget has focus and selected text
        from PyQt6.QtWidgets import QApplication, QTextEdit, QLineEdit, QMessageBox
        
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, (QTextEdit, QLineEdit)):
            if focus_widget.textCursor().hasSelection():
                focus_widget.copy()
                return

        graph = self.get_current_graph()
        if graph and hasattr(graph, 'copy_selection'):
            graph.copy_selection()

    def paste_selection(self):
        from PyQt6.QtWidgets import QApplication, QTextEdit, QLineEdit
        
        focus_widget = QApplication.focusWidget()
        if isinstance(focus_widget, (QTextEdit, QLineEdit)):
            focus_widget.paste()
            return

        graph = self.get_current_graph()
        if graph and hasattr(graph, 'paste_selection'):
            graph.paste_selection()

    def duplicate_selection(self):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'duplicate_selection'):
            graph.duplicate_selection()

    def delete_selection(self):
        from PyQt6.QtWidgets import QMessageBox
        graph = self.get_current_graph()
        if not graph or not hasattr(graph, 'canvas'): return
        
        selected = graph.canvas.scene.selectedItems()
        if not selected: return
        
        if len(selected) > 1:
            res = QMessageBox.question(self, "Delete Items", f"Are you sure you want to delete {len(selected)} items?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res != QMessageBox.StandardButton.Yes: return
            
        graph.delete_selection()
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Deleted {len(selected)} objects", 3000)

    def select_all(self):
        graph = self.get_current_graph()
        if graph and graph.canvas and graph.canvas.scene:
            for item in graph.canvas.scene.items():
                item.setSelected(True)

    def add_as_tool(self):
        if hasattr(self, 'node_library'):
             self.node_library.add_current_graph_as_tool()

    def zoom_to_fit(self):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'canvas'):
            graph.canvas.zoom_to_fit()

    def zoom_in(self):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'canvas'):
            graph.canvas.zoom(1.1)

    def zoom_out(self):
        graph = self.get_current_graph()
        if graph and hasattr(graph, 'canvas'):
            graph.canvas.zoom(1/1.1)

    def clear_console(self):
        if hasattr(self, 'console_output'):
            self.console_output.clear()

    def clear_debug(self):
        if hasattr(self, 'debug_output'):
            self.debug_output.clear()

    def search_nodes(self):
        """Search for nodes matching the query in the search input (Cycles matches)."""
        if not hasattr(self, 'search_input'): return
        
        query = self.search_input.text().strip().lower()
        if not query: return
        
        graph = self.get_current_graph()
        if not graph or not graph.canvas or not graph.canvas.scene: return
        
        # 1. State Management for Cycling
        if not hasattr(self, '_last_search_query'): self._last_search_query = ""
        if not hasattr(self, '_search_index'): self._search_index = -1
        if not hasattr(self, '_search_results'): self._search_results = []
        
            # 2. Re-Scan if query changed or no cached results
        current_scope = "All"
        if hasattr(self, 'search_scope'):
            current_scope = self.search_scope.currentText()
            
        # Check if scope changed
        if not hasattr(self, '_last_search_scope'): self._last_search_scope = "All"
        
        if (query != self._last_search_query or 
            current_scope != self._last_search_scope or 
            not self._search_results):
            
            self._last_search_query = query
            self._last_search_scope = current_scope
            self._search_index = -1
            self._search_results = []
            
            for item in graph.canvas.scene.items():
                if hasattr(item, 'node') and item.node:
                    node = item.node
                    match = False
                    
                    # 1. Node Names Config
                    if current_scope in ["All", "Node Names"]:
                        if query in node.title.lower() or query in node.node_id.lower():
                            match = True
                            
                    # 2. Node Types Config
                    if not match and current_scope in ["All", "Nodes Type"]:
                        if query in node.type.lower():
                            match = True
                            
                    # 3. Connectors Config
                    if not match and current_scope in ["All", "Connectors"]:
                        # Check Input Ports
                        for port_name in node.input_types.keys():
                            if query in port_name.lower():
                                match = True
                                break
                        # Check Output Ports
                        if not match:
                            for port_name in node.output_types.keys():
                                if query in port_name.lower():
                                    match = True
                                    break

                    # 4. Values Config (Properties)
                    if not match and hasattr(node, 'properties'):
                        for k, v in node.properties.items():
                            k_str = str(k).lower()
                            v_str = str(v).lower()
                            
                            # If scope is Values, search ONLY values
                            if current_scope == "Values":
                                if query in v_str:
                                    match = True
                                    break
                            # If scope is All, search Keys AND Values
                            elif current_scope == "All":
                                if query in k_str or query in v_str:
                                    match = True
                                    break
                    
                    if match:
                        self._search_results.append(item)
            
            # Sort results by Y then X for logical flow order
            self._search_results.sort(key=lambda it: (it.y(), it.x()))

        # 3. Cycle & Select
        if not self._search_results:
            self.statusBar().showMessage(f"No matches found for '{query}'", 3000)
            return
            
        self._search_index = (self._search_index + 1) % len(self._search_results)
        target_item = self._search_results[self._search_index]
        
        # Select
        graph.canvas.scene.clearSelection()
        target_item.setSelected(True)
        
        # Focus/Pan
        graph.canvas.smooth_center_on(target_item)
        
        # Animation
        if hasattr(target_item, 'highlight_pulse'):
            target_item.highlight_pulse()
            
        # Status
        self.statusBar().showMessage(f"Search: Match {self._search_index + 1} of {len(self._search_results)} ('{target_item.node.title}')", 3000)

    def toggle_wire_legend(self):
        """Show/Hide the floating Wire Legend window."""
        if not hasattr(self, '_wire_legend_window'):
            from synapse.gui.wire_legend import WireLegendV2
            self._wire_legend_window = WireLegendV2(self)
            
        if self._wire_legend_window.isVisible():
            self._wire_legend_window.hide()
            self.toggle_wire_legend_action.setChecked(False)
        else:
            # Position it near the top-right of the main window
            geom = self.geometry()
            x = geom.x() + geom.width() - 280
            y = geom.y() + 120
            self._wire_legend_window.move(x, y)
            
            self._wire_legend_window.show()
            self.toggle_wire_legend_action.setChecked(True)

    def show_about(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Synapse VS",
                          "<h3>Synapse VS Architect</h3>"
                          "<p>Visual Scripting Environment for AI & Logic Flows.</p>"
                          "<p>Version: 0.2.0 (Refactored)</p>"
                          "<p>(c) 2026 Synapse Team</p>")
