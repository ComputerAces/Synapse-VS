from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton, QGroupBox
from PyQt6.QtCore import Qt

class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Title
        title = QLabel("Properties")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        self.layout.addWidget(title)
        
        # Placeholder for dynamic content
        self.form_container = QGroupBox("Node Settings")
        self.form_layout = QFormLayout()
        self.form_container.setLayout(self.form_layout)
        self.layout.addWidget(self.form_container)

        # Example Fields (Static for now)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Node Name")
        self.form_layout.addRow("Name:", self.name_input)
        
        self.env_input = QLineEdit()
        self.env_input.setPlaceholderText("Environment Path")
        self.form_layout.addRow("Env:", self.env_input)

        # Spacer to push content up
        self.layout.addStretch()

    def _refresh_from_widget(self):
        """Refreshes the panel if the currently loaded widget changes (e.g. ports added)."""
        if hasattr(self, 'current_widget') and self.current_widget:
            # Re-load the same widget to rebuild the form
            self.load_node(self.current_widget)

    def load_node(self, node_or_widget):
        """
        Populate the panel with data from the selected node or frame.
        Accepts NodeWidget, FrameWidget, or BaseNode.
        """
        # 1. Clear existing rows
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
            
        win = QApplication.activeWindow()
        if not node_or_widget:
            self.current_node = None
            self.current_widget = None
            self.current_frame = None
            
            # [NEW] Default to Project Properties
            if win and hasattr(win, 'get_current_graph'):
                graph = win.get_current_graph()
                if graph:
                    self.load_project_properties(graph)
                    return

            # Show Placeholder if no graph either
            placeholder = QLabel("Select a Node to see its properties.")
            placeholder.setStyleSheet("color: #666; font-style: italic; margin-top: 20px;")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.form_layout.addRow(placeholder)
            return
            
        if win and hasattr(win, 'status_bar'):
            name = node_or_widget.name if hasattr(node_or_widget, 'name') else "Unknown"
            win.status_bar.showMessage(f"PropertiesPanel: Loading {name}...", 1000)
        
        # Check for FrameWidget first
        from synapse.gui.frame_widget import FrameWidget
        if isinstance(node_or_widget, FrameWidget):
            self.current_frame = node_or_widget
            self.current_node = None
            self.current_widget = None
            self._load_frame_properties(node_or_widget)
            return
            
        self.current_frame = None
        from synapse.gui.node_widget import NodeWidget
        
        if isinstance(node_or_widget, NodeWidget):
            # Disconnect previous if any
            if hasattr(self, 'current_widget') and self.current_widget:
                try: self.current_widget.ports_changed.disconnect(self._refresh_from_widget)
                except: pass
                
            self.current_widget = node_or_widget
            self.current_node = node_or_widget.node
            
            # Connect to refresh
            self.current_widget.ports_changed.connect(self._refresh_from_widget)
        else:
            self.current_node = node_or_widget
            self.current_widget = None # Cannot infer widget from logic node easily without reverse lookup
            
        logic_node = self.current_node
        if not logic_node: 
            # Widget exists but no logic node attached yet?
            return 

        # 2. Basic Info
        # Type (Read Only)
        type_val = self.current_widget.node_type if self.current_widget else (type(logic_node).__name__ if logic_node else "Unknown")
        self.type_input = QLineEdit(type_val)
        self.type_input.setReadOnly(True)
        self.form_layout.addRow("Type:", self.type_input)

        # Name is on the Widget usually, but Logic node has name too.
        # If widget exists, bind to widget name update?
        name_val = self.current_widget.name if self.current_widget else logic_node.name
        self.name_input = QLineEdit(name_val)
        self.name_input.textChanged.connect(self.update_name)
        self.form_layout.addRow("Name:", self.name_input)
        
        # 3. Dynamic Properties 
        
        if "Python" in logic_node.name or "Script" in logic_node.name:
            self.script_input = QLineEdit()
            self.script_input.setPlaceholderText("path/to/script.py")
            self.form_layout.addRow("Script:", self.script_input)
            
            self.env_checkbox = QLineEdit("Global") 
            self.form_layout.addRow("Env:", self.env_checkbox)

        handled_keys = set()
        
        # 4. Generic Properties (from logic_node.properties dict)
        if hasattr(logic_node, 'properties'):
            # [SORTING FIX] Order properties to match visually mapped input ports
            prop_keys = list(logic_node.properties.keys())
            if self.current_widget and hasattr(self.current_widget, 'inputs'):
                port_names = [p.name for p in self.current_widget.inputs]
                def prop_sort_rank(k):
                    if k in port_names: return (0, port_names.index(k))
                    return (1, k.lower())
                prop_keys.sort(key=prop_sort_rank)

            # [REFINED] Infrastructure ports to hide from properties panel
            skip_infrastructure = [
                "Flow", "Exec", "Loop", "In", "Out", "True", "False", 
                "Then", "Else", "Break", "Continue", "Return", "Exit", 
                "Provider End", "Try", "Catch", "Panic", "Error Flow",
                "Provider ID", "Provider Id", "Provider_Flow_ID", "Provider_Flow_Id"
            ]

            for key in prop_keys:
                if key in skip_infrastructure:
                    continue
                if hasattr(logic_node, 'hidden_fields') and key in logic_node.hidden_fields:
                    continue
                if hasattr(logic_node, 'hidden_ports') and key in logic_node.hidden_ports:
                    continue
                
                value = logic_node.properties[key]
                handled_keys.add(key)
                handled_keys.add(key.lower())
                
                # Check for Enum-like properties using generic options suffix
                opt_key = key + "_options"
                if hasattr(logic_node, 'properties') and opt_key in logic_node.properties:
                    options = logic_node.properties[opt_key]
                    if isinstance(options, list):
                        self.add_dropdown_property_ui(key, value, options)
                        continue

                if key == "value" and "True/False" in logic_node.name:
                     self.add_dropdown_property_ui(key, value, ["True", "False"])
                elif key == "value" and "Boolean" in logic_node.name:
                     self.add_dropdown_property_ui(key, value, ["True", "False"])
                elif key == "Random Type":
                    self.add_dropdown_property_ui(key, value, ["Number", "Currency"])
                elif key == "condition" and "Watch" in logic_node.name:
                     self.add_dropdown_property_ui(key, value, [">", "<", "==", "!=", ">=", "<="])
                elif key == "compare_type":
                    self.add_dropdown_property_ui(key, value, ["<", "<=", ">", ">=", "==", "!="])
                elif isinstance(value, bool):
                     self.add_bool_property_ui(key, value)
                elif isinstance(value, str):
                    self.add_string_property_ui(key, value)
                elif isinstance(value, (int, float)):
                    self.add_number_property_ui(key, value)
                    
                elif isinstance(value, (int, float)):
                    self.add_number_property_ui(key, value)
                elif value is None:
                    self.add_string_property_ui(key, "")
        
        # 5. [NEW] Always show data input ports from the widget as editable properties
        #    This catches input vars not present in logic_node.properties (e.g. SubGraph dynamic inputs)
        if self.current_widget and hasattr(self.current_widget, 'inputs'):
            try:
                from synapse.core.types import DataType
                import traceback
                
                skip_infrastructure = [
                    "Flow", "Exec", "Loop", "In", "Out", "True", "False", 
                    "Then", "Else", "Break", "Continue", "Return", "Exit", 
                    "Provider End", "Try", "Catch", "Panic", "Error Flow",
                    "Provider ID", "Provider Id", "Provider_Flow_ID", "Provider_Flow_Id"
                ]
                
                input_type_map = getattr(logic_node, 'input_types', {})
                data_inputs = []
                
                # Debug logging (visible in console) -- enable if needed
                # print(f"DEBUG: Checking {len(self.current_widget.inputs)} inputs for {self.current_widget.name}")

                for p in self.current_widget.inputs:
                    if p.name in skip_infrastructure:
                        continue
                    # Skip flow-class ports
                    if hasattr(p, 'port_class') and p.port_class == "flow":
                        continue
                    if p.name in handled_keys or p.name.lower() in handled_keys:
                        continue
                    data_inputs.append(p)
                
                if data_inputs:
                    sep = QLabel("── Input Variables ──")
                    sep.setStyleSheet("color: #888; font-style: italic; margin-top: 8px;")
                    sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.form_layout.addRow(sep)
                    
                    for port in data_inputs:
                        port_name = port.name
                        # Read current value from properties if it exists, otherwise default
                        val = logic_node.properties.get(port_name, "")
                        
                        # Infer type from input_types or port data_type
                        dtype = input_type_map.get(port_name, DataType.ANY)
                        if dtype == DataType.ANY and hasattr(port, 'data_type'):
                             dtype = port.data_type

                        handled_keys.add(port_name)
                        handled_keys.add(port_name.lower())
                        
                        if isinstance(val, bool) or dtype == DataType.BOOLEAN:
                            self.add_bool_property_ui(port_name, val if isinstance(val, bool) else False)
                        elif isinstance(val, (int, float)) or dtype in [DataType.NUMBER, DataType.INTEGER, DataType.FLOAT]:
                            self.add_number_property_ui(port_name, val if isinstance(val, (int, float)) else 0)
                        else:
                            self.add_string_property_ui(port_name, str(val) if val is not None else "")
            except Exception as e:
                print(f"Properties Panel Error: {e}")
                traceback.print_exc()
        
        # 6. Start Node Output Defaults (editable default values for subgraph inputs)
        if self.current_widget and "Start" in getattr(self.current_widget, 'node_type', ''):
            skip_flow = ["Flow", "Error Flow"]
            data_outputs = [p for p in self.current_widget.outputs if p.name not in skip_flow]
            if data_outputs:
                sep = QLabel("── Output Defaults ──")
                sep.setStyleSheet("color: #888; font-style: italic; margin-top: 8px;")
                sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.form_layout.addRow(sep)
                
                for port in data_outputs:
                    out_name = port.name
                    if out_name in handled_keys or out_name.lower() in handled_keys:
                        continue
                    val = logic_node.properties.get(out_name, "")
                    self.add_string_property_ui(out_name, str(val))
                    
    def load_project_properties(self, graph_widget):
        """Displays editors for Project Metadata (Name, Category, Description)."""
        self.current_node = None
        self.current_widget = None
        self.current_frame = None
        
        sep = QLabel("── Project Metadata ──")
        sep.setStyleSheet("font-weight: bold; color: #444; margin-top: 5px;")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addRow(sep)
        
        meta = graph_widget.project_metadata
        
        # Name
        name_edit = QLineEdit(meta.get("project_name", ""))
        name_edit.textChanged.connect(lambda t: self._update_meta(graph_widget, "project_name", t))
        self.form_layout.addRow("Project Name:", name_edit)
        
        # Category
        cat_edit = QLineEdit(meta.get("project_category", ""))
        cat_edit.setPlaceholderText("e.g. Logic, File Tools...")
        cat_edit.textChanged.connect(lambda t: self._update_meta(graph_widget, "project_category", t))
        self.form_layout.addRow("Project Category:", cat_edit)
        
        # Description
        from PyQt6.QtWidgets import QTextEdit
        desc_edit = QTextEdit(meta.get("project_description", ""))
        desc_edit.setMaximumHeight(80)
        desc_edit.textChanged.connect(lambda: self._update_meta(graph_widget, "project_description", desc_edit.toPlainText()))
        self.form_layout.addRow("Description:", desc_edit)

    def _update_meta(self, graph, key, val):
        graph.project_metadata[key] = val
        graph.mark_modified(None)
                    
    def add_string_property_ui(self, key, value):
        from PyQt6.QtWidgets import QHBoxLayout, QDialog, QDialogButtonBox, QTextEdit
        from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Line Edit
        line_edit = QLineEdit(value)
        line_edit.textChanged.connect(lambda text, k=key: self.update_property(k, text))
        layout.addWidget(line_edit)
        
        # Square Button (..."Icon")
        btn = QPushButton("...")
        btn.setFixedWidth(30)
        # Optional: Set a square icon or just text
        btn.clicked.connect(lambda: self.open_multiline_editor(key, line_edit))
        layout.addWidget(btn)
        
        self.form_layout.addRow(f"{key}:", container)
        
    def update_property(self, key, value):
        if self.current_node:
            self.current_node.properties[key] = value
            
            # [FIX] Force layout refresh for Memo nodes to handle dynamic resizing
            if self.current_widget and getattr(self.current_widget, 'node_type', '') == "Memo":
                if key == "Memo Note" and hasattr(self.current_widget, 'update_layout'):
                    self.current_widget.update_layout()

    def open_multiline_editor(self, key, line_widget):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {key}")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(line_widget.text())
        layout.addWidget(text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            new_text = text_edit.toPlainText()
            line_widget.setText(new_text)
            self.update_property(key, new_text)

    def add_port_ui(self, port_type):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.port_name_input = QLineEdit()
        self.port_name_input.setPlaceholderText(f"New {port_type} Name")
        layout.addWidget(self.port_name_input)
        
        btn = QPushButton(f"Add {port_type}")
        btn.clicked.connect(lambda: self.add_port(port_type))
        layout.addWidget(btn)
        
        self.form_layout.addRow(f"Add {port_type}:", container)

    def add_port(self, port_type):
        name = self.port_name_input.text().strip()
        if not name: return
        
        if hasattr(self, 'current_node'):
            if port_type == "Input":
                self.current_node.add_input(name)
            else:
                self.current_node.add_output(name)
            
            # Clear input
            self.port_name_input.clear()
            # Force repaint/update needed? add_input calls update_layout already.

    def update_name(self, text):
        if hasattr(self, 'current_node') and self.current_node:
            self.current_node.name = text
            
        if hasattr(self, 'current_widget') and self.current_widget:
            self.current_widget.set_user_name(text) # Sync widget name and update display
            # self.current_widget.name = text # Handled by set_user_name
    
    def add_dropdown_property_ui(self, key, value, options):
        """Add a dropdown/combobox for enum-like properties."""
        from PyQt6.QtWidgets import QComboBox
        
        combo = QComboBox()
        combo.addItems(options)
        
        # Set current value
        if value in options:
            combo.setCurrentText(str(value))
        
        combo.currentTextChanged.connect(lambda text, k=key: self.update_property(k, text))
        self.form_layout.addRow(f"{key}:", combo)
    
    def add_number_property_ui(self, key, value):
        """Add a number input field for numeric properties."""
        from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox
        
        if isinstance(value, int):
            spin = QSpinBox()
            spin.setRange(-999999, 999999)
            spin.setValue(int(value))
            spin.valueChanged.connect(lambda v, k=key: self.update_property(k, v))
        else:
            spin = QDoubleSpinBox()
            spin.setRange(-999999.0, 999999.0)
            spin.setDecimals(4)
            spin.setValue(float(value))
            spin.valueChanged.connect(lambda v, k=key: self.update_property(k, v))
        
        self.form_layout.addRow(f"{key}:", spin)

    def add_bool_property_ui(self, key, value):
        from PyQt6.QtWidgets import QCheckBox
        cb = QCheckBox()
        cb.setChecked(value)
        cb.toggled.connect(lambda v, k=key: self.update_property(k, v))
        self.form_layout.addRow(f"{key}:", cb)

    def _load_frame_properties(self, frame):
        """Load properties for a FrameWidget."""
        # Type (Read Only)
        type_input = QLineEdit("Frame")
        type_input.setReadOnly(True)
        self.form_layout.addRow("Type:", type_input)
        
        # Name
        name_input = QLineEdit(frame.name)
        name_input.textChanged.connect(lambda text: self._update_frame_name(frame, text))
        self.form_layout.addRow("Name:", name_input)
        
        # Color with picker button
        from PyQt6.QtWidgets import QHBoxLayout
        color_container = QWidget()
        color_layout = QHBoxLayout(color_container)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(4)
        
        # Color preview
        self.color_preview = QWidget()
        self.color_preview.setFixedSize(30, 24)
        self.color_preview.setAutoFillBackground(True)
        pal = self.color_preview.palette()
        pal.setColor(self.color_preview.backgroundRole(), frame.color)
        self.color_preview.setPalette(pal)
        color_layout.addWidget(self.color_preview)
        
        # Hex display
        hex_str = frame.color.name(frame.color.NameFormat.HexArgb) if frame.color.alpha() < 255 else frame.color.name()
        self.color_hex = QLineEdit(hex_str)
        self.color_hex.setPlaceholderText("#RRGGBBAA")
        self.color_hex.textChanged.connect(lambda text: self._update_frame_color_from_hex(frame, text))
        color_layout.addWidget(self.color_hex)
        
        # Picker button
        picker_btn = QPushButton("🎨")
        picker_btn.setFixedWidth(30)
        picker_btn.clicked.connect(lambda: self._open_frame_color_picker(frame))
        color_layout.addWidget(picker_btn)
        
        self.form_layout.addRow("Color:", color_container)
        
        # Info about nodes
        node_count = len(frame.child_nodes)
        info_label = QLabel(f"Contains {node_count} node(s)")
        info_label.setStyleSheet("color: #666;")
        self.form_layout.addRow("", info_label)
        
    def _update_frame_name(self, frame, text):
        """Update frame name."""
        frame.set_name(text)
        
    def _update_frame_color_from_hex(self, frame, text):
        """Update frame color from hex input."""
        from PyQt6.QtGui import QColor
        text = text.strip()
        if text.startswith("#") and len(text) in [7, 9]:
            color = QColor(text)
            if color.isValid():
                frame.set_color(color)
                # Update preview
                if hasattr(self, 'color_preview'):
                    pal = self.color_preview.palette()
                    pal.setColor(self.color_preview.backgroundRole(), color)
                    self.color_preview.setPalette(pal)
                    
    def _open_frame_color_picker(self, frame):
        """Open full color picker dialog for frame."""
        from synapse.gui.color_picker import ColorPickerDialog
        
        color = ColorPickerDialog.pick_color(frame.color, self)
        if color:
            frame.set_color(color)
            # Update hex field and preview
            if hasattr(self, 'color_hex'):
                hex_str = color.name(color.NameFormat.HexArgb) if color.alpha() < 255 else color.name()
                self.color_hex.setText(hex_str)
            if hasattr(self, 'color_preview'):
                pal = self.color_preview.palette()
                pal.setColor(self.color_preview.backgroundRole(), color)
                self.color_preview.setPalette(pal)

    def clear(self):
        """Clear all properties from the panel."""
        self.current_node = None
        self.current_frame = None
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
