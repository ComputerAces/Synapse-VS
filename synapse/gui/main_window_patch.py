def create_actions(self):
    # File Actions
    self.new_action = QAction("New Graph", self)
    self.new_action.triggered.connect(self.new_graph)
    
    self.open_action = QAction("Open Graph", self)
    self.open_action.triggered.connect(self.open_graph)
    
    self.save_action = QAction("Save Graph", self)
    self.save_action.setShortcut("Ctrl+S")
    self.save_action.triggered.connect(self.save_graph)
    
    self.save_as_action = QAction("Save As...", self)
    self.save_as_action.setShortcut("Ctrl+Shift+S")
    self.save_as_action.triggered.connect(self.save_graph_as)
    
    self.add_tool_action = QAction("Add as Tool...", self)
    self.add_tool_action.triggered.connect(self.add_as_tool)
    
    self.import_action = QAction("Import Subgraph", self)
    self.import_action.triggered.connect(self.import_subgraph)
    
    self.exit_action = QAction("Exit", self)
    self.exit_action.triggered.connect(self.close)

    # Edit Actions
    self.copy_action = QAction("Copy", self)
    self.copy_action.setShortcut("Ctrl+C")
    self.copy_action.triggered.connect(self.copy_selection)
    
    self.paste_action = QAction("Paste", self)
    self.paste_action.setShortcut("Ctrl+V")
    self.paste_action.triggered.connect(self.paste_selection)
    
    self.duplicate_action = QAction("Duplicate Selection", self)
    self.duplicate_action.setShortcut("Ctrl+D")
    self.duplicate_action.triggered.connect(self.duplicate_selection)
    
    self.delete_action = QAction("Delete Selection", self)
    self.delete_action.setShortcut("Del")
    self.delete_action.triggered.connect(self.delete_selection)

    # Run Actions
    self.run_action = QAction("Run Graph", self)
    self.run_action.setShortcut("F5")
    self.run_action.triggered.connect(self.run_graph)
    
    self.stop_action = QAction("Stop Execution", self)
    self.stop_action.triggered.connect(self.stop_graph)
    
    self.stop_all_action = QAction("Stop All Graphs", self)
    self.stop_all_action.triggered.connect(self.stop_all_graphs)
    
    self.pause_action = QAction("Pause Execution", self)
    self.pause_action.triggered.connect(self.pause_graph)
    
    self.step_action = QAction("Step", self)
    self.step_action.setShortcut("F10")
    self.step_action.setToolTip("Step Forward (F10)")
    self.step_action.triggered.connect(self.step_graph)

    # Output Actions
    self.clear_debug_action = QAction("Clear Debug Output", self)
    self.clear_debug_action.triggered.connect(lambda: self.debug_output.clear())
    
    self.clear_console_action = QAction("Clear Console Output", self)
    self.clear_console_action.triggered.connect(lambda: self.console_output.clear())
    
    # Window Actions
    self.zoom_action = QAction("Zoom to Fit", self)
    self.zoom_action.setShortcut("F2")
    self.zoom_action.triggered.connect(self.zoom_current_graph)
    
    self.fullscreen_action = QAction("Toggle Fullscreen", self)
    self.fullscreen_action.setShortcut("F11")
    self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
