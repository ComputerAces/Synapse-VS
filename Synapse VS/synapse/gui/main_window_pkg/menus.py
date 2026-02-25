from PyQt6.QtWidgets import QMenu, QToolBar, QSlider, QLabel, QCheckBox, QLineEdit, QSizePolicy, QWidget, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

class MenusMixin:
    def create_menu(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        
        self.recent_menu = file_menu.addMenu("Open &Recent") # [NEW]
        
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_all_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.import_subgraph_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.duplicate_action)
        edit_menu.addAction(self.delete_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.select_all_action)
        
        # View Menu
        self.view_menu = menubar.addMenu("&View")
        self.view_menu.addAction(self.toggle_fullscreen_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.zoom_fit_action)
        self.view_menu.addAction(self.zoom_in_action)
        self.view_menu.addAction(self.zoom_out_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.toggle_wire_legend_action)
        self.view_menu.addSeparator()
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.add_tool_action)
        
        # Output Menu
        output_menu = menubar.addMenu("&Output")
        output_menu.addAction(self.clear_console_action)
        output_menu.addAction(self.clear_debug_action)
        
        # Run Menu
        run_menu = menubar.addMenu("&Run")
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.pause_action)
        run_menu.addSeparator()
        run_menu.addAction(self.step_back_action)
        run_menu.addAction(self.step_action)
        run_menu.addAction(self.step_over_action)
        run_menu.addSeparator()
        run_menu.addAction(self.stop_action)
        run_menu.addSeparator()
        run_menu.addAction(self.stop_all_action)
        
        # Help Menu [NEW]
        help_menu = menubar.addMenu("&Help")
        
        readme_action = QAction("&Readme", self)
        readme_action.triggered.connect(self.show_readme)
        help_menu.addAction(readme_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("Abou&t", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        from synapse.gui.dialogs.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def show_readme(self):
        from synapse.gui.dialogs.readme_viewer import ReadmeViewer
        import os
        # Assume README.md is in project root
        # We are in synapse/gui/main_window_pkg/menus.py
        # Root is ../../../
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        readme_path = os.path.join(root_dir, "README.md")
        
        self.readme_viewer = ReadmeViewer(self, readme_path)
        self.readme_viewer.show() # Non-modal for reading


    def update_recent_menu(self):
        """Populates the Open Recent menu from settings."""
        if not hasattr(self, 'recent_menu') or not hasattr(self, 'last_settings'): return
        
        self.recent_menu.clear()
        last_graphs = self.last_settings.get("last_graphs", [])
        
        # Deduplicate and filter existing
        import os
        valid_graphs = []
        seen = set()
        for path in last_graphs:
            if path not in seen and os.path.exists(path):
                valid_graphs.append(path)
                seen.add(path)
        
        for path in valid_graphs[:10]: # Limit to 10
            action = QAction(os.path.basename(path), self)
            action.setToolTip(path)
            # Use partial to capture the specific path variable
            from functools import partial
            action.triggered.connect(partial(self.open_tab, path))
            self.recent_menu.addAction(action)
            
        if not valid_graphs:
            self.recent_menu.setEnabled(False)
        else:
            self.recent_menu.setEnabled(True)

    def create_toolbar(self):
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setObjectName("MainToolbar")
        from PyQt6.QtCore import QSize
        size = int(self.style().pixelMetric(self.style().PixelMetric.PM_SmallIconSize, None, self) * 1.5)
        self.main_toolbar.setIconSize(QSize(size, size))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        
        self.main_toolbar.addAction(self.new_action)
        self.main_toolbar.addAction(self.open_action)
        self.main_toolbar.addAction(self.save_action)
        # Context Menu for Save Button
        save_btn = self.main_toolbar.widgetForAction(self.save_action)
        if save_btn:
            save_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            save_btn.customContextMenuRequested.connect(self.show_save_context_menu)
            
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.run_action)
        self.main_toolbar.addAction(self.pause_action)
        self.main_toolbar.addAction(self.stop_action)
        self.main_toolbar.addSeparator()
        
        self.main_toolbar.addAction(self.step_back_action)
        self.main_toolbar.addAction(self.step_action)
        self.main_toolbar.addAction(self.step_over_action)
        self.main_toolbar.addSeparator()
        
        # Spacer to push items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(spacer)


        
        # Speed Slider
        self.main_toolbar.addWidget(QLabel(" Speed: "))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100) 
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.setToolTip("Execution Speed (Right=Fast, Left=Slow)")
        self.main_toolbar.addWidget(self.speed_slider)
        self.speed_slider.valueChanged.connect(self.update_speed)
        
        self.main_toolbar.addSeparator()
        
        # Checkboxes
        self.hide_tooltips_checkbox = QCheckBox("Hide Tooltips")
        self.hide_tooltips_checkbox.toggled.connect(self.on_hide_tooltips_changed)
        self.main_toolbar.addWidget(self.hide_tooltips_checkbox)
        
        self.main_toolbar.addSeparator()
        self.show_names_checkbox = QCheckBox("Show Names")
        self.show_names_checkbox.setChecked(True)
        self.show_names_checkbox.toggled.connect(self.toggle_node_names)
        self.main_toolbar.addWidget(self.show_names_checkbox)
        
        self.main_toolbar.addSeparator()
        self.auto_focus_checkbox = QCheckBox("Auto Focus")
        self.auto_focus_checkbox.setChecked(True)
        self.main_toolbar.addWidget(self.auto_focus_checkbox)
        
        self.main_toolbar.addSeparator()
        self.show_trace_checkbox = QCheckBox("Show Trace")
        self.show_trace_checkbox.setChecked(True)
        self.show_trace_checkbox.setToolTip("Enable visual node highlighting (Trace)")
        self.main_toolbar.addWidget(self.show_trace_checkbox)
        self.show_trace_checkbox.toggled.connect(self.on_show_trace_changed)

        self.trace_subgraphs_checkbox = QCheckBox("Trace Sub Graphs")
        self.trace_subgraphs_checkbox.setChecked(True)
        self.trace_subgraphs_checkbox.setToolTip("Enable trace visualization inside sub-graphs")
        self.main_toolbar.addWidget(self.trace_subgraphs_checkbox)
        self.trace_subgraphs_checkbox.toggled.connect(self.on_trace_subgraphs_changed)

        self.main_toolbar.addSeparator()
        self.auto_save_checkbox = QCheckBox("Auto Save")
        self.auto_save_checkbox.setChecked(False)
        self.auto_save_checkbox.setToolTip("Automatically save changes")
        self.main_toolbar.addWidget(self.auto_save_checkbox)

        self.main_toolbar.addSeparator()
        self.back_trace_checkbox = QCheckBox("Back Trace")
        self.back_trace_checkbox.setChecked(False)
        self.back_trace_checkbox.setToolTip("Enable Time-Travel Debugging (Performance Tax Warning)")
        self.main_toolbar.addWidget(self.back_trace_checkbox)
        self.back_trace_checkbox.toggled.connect(self.on_back_trace_changed)

        # Magnifier Section (Moved to far right of content area)
        self.main_toolbar.addSeparator()
        size_lbl = QLabel("  Size  ")
        self.main_toolbar.addWidget(size_lbl)
        
        self.magnifier_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.magnifier_size_slider.setRange(50, 600)
        self.magnifier_size_slider.setValue(180)
        self.magnifier_size_slider.setFixedWidth(100)
        self.magnifier_size_slider.setToolTip("Magnifier Circle Radius")
        self.magnifier_size_slider.valueChanged.connect(self.on_magnifier_size_changed)
        self.main_toolbar.addWidget(self.magnifier_size_slider)
        
        self.main_toolbar.addAction(self.toggle_magnifier_action)


        # Right-aligned Search Box
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.main_toolbar.addWidget(spacer)
        
        self.main_toolbar.addWidget(QLabel(" Scope: "))
        self.search_scope = QComboBox()
        self.search_scope.addItems(["All", "Node Names", "Nodes Type", "Connectors", "Values"])
        self.search_scope.setToolTip("Filter search scope")
        self.main_toolbar.addWidget(self.search_scope)
        
        self.main_toolbar.addWidget(QLabel(" Search: "))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes or properties...")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self.search_nodes) 
        self.main_toolbar.addWidget(self.search_input)

    def show_save_context_menu(self, point):
        btn = self.main_toolbar.widgetForAction(self.save_action)
        if not btn: return
        
        menu = QMenu(self)
        menu.addAction(self.save_action)
        menu.addAction(self.save_as_action)
        menu.addAction(self.save_all_action)
        
        menu.exec(btn.mapToGlobal(point))
