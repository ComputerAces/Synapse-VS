from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

class QuickPicker(QDialog):
    node_selected = pyqtSignal(str, bool, str) # label, is_subgraph, path

    def __init__(self, parent=None, source_port=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Node Picker")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(300, 400)
        
        self.source_port = source_port
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes...")
        self.search_input.textChanged.connect(self.filter_nodes)
        self.search_input.returnPressed.connect(self.on_entered)
        layout.addWidget(self.search_input)
        
        # Tree View
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #dddddd;
                border: 1px solid #555;
            }
            QTreeWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)
        layout.addWidget(self.tree)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                border: 1px solid #007acc;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 4px;
            }
        """)
        
        self.populate_tree()
        self.search_input.setFocus()

    def populate_tree(self):
        self.tree.clear()
        
        source_type = getattr(self.source_port, 'data_type', DataType.ANY)
        port_dir = getattr(self.source_port, 'port_type', "output")
        
        is_flow_source = False
        if source_type in (DataType.FLOW, DataType.PROVIDER_FLOW):
            is_flow_source = True
        elif hasattr(self.source_port, 'port_class') and self.source_port.port_class == "flow":
            is_flow_source = True
            
        show_all = is_flow_source or source_type == DataType.ANY
        
        registry_cats = NodeRegistry.get_categories()
        sorted_cats = sorted(registry_cats.keys())
        
        for cat in sorted_cats:
            if cat == "Hidden": continue
            
            nodes = registry_cats[cat]
            cat_item = None
            
            for node_label in sorted(nodes):
                compatible = show_all
                node_cls = NodeRegistry.get_node_class(node_label)
                
                if not compatible and node_cls:
                    try:
                        # Instantiate temporary node to safely execute define_schema
                        temp = node_cls.__new__(node_cls)
                        temp.properties = {} # Mock to prevent attr errors
                        schema_inputs = None
                        schema_outputs = None
                        
                        # Newer Node Syntax (SuperNode)
                        if hasattr(temp, "define_schema"):
                            try:
                                temp.define_schema()
                                schema_inputs = getattr(temp, "input_schema", None)
                                schema_outputs = getattr(temp, "output_schema", None)
                            except: pass
                            
                        # Legacy Syntax Fallback
                        if not schema_inputs and not schema_outputs:
                            if isinstance(getattr(node_cls, 'default_inputs', None), property):
                                try: schema_inputs = temp.default_inputs
                                except: pass
                            else:
                                schema_inputs = getattr(node_cls, 'default_inputs', None)
                                
                            if isinstance(getattr(node_cls, 'default_outputs', None), property):
                                try: schema_outputs = temp.default_outputs
                                except: pass
                            else:
                                schema_outputs = getattr(node_cls, 'default_outputs', None)
                        
                        target_schema = schema_inputs if port_dir == "output" else schema_outputs
                        
                        if target_schema:
                            # Format handling
                            if isinstance(target_schema, dict):
                                # New dictionary schema {"PortName": DataType.STRING}
                                for port_name, p_type in target_schema.items():
                                    if p_type == DataType.ANY or p_type == source_type:
                                        compatible = True
                                        break
                            elif isinstance(target_schema, list):
                                # Legacy list schema [("PortName", DataType.STRING)]
                                for inp in target_schema:
                                    if isinstance(inp, tuple) and len(inp) >= 2:
                                        p_type = inp[1]
                                        if p_type == DataType.ANY or p_type == source_type:
                                            compatible = True
                                            break
                                    else:
                                        compatible = True
                                        break
                    except Exception as e:
                        pass
                
                if compatible:
                    if not cat_item:
                        cat_item = QTreeWidgetItem(self.tree)
                        cat_item.setText(0, cat)
                        cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        cat_item.setExpanded(True)
                        
                    node_item = QTreeWidgetItem(cat_item)
                    node_item.setText(0, node_label)
                    
                    is_subgraph = hasattr(node_cls, 'graph_path') and node_cls.graph_path
                    path = node_cls.graph_path if is_subgraph else ""
                    
                    node_item.setData(0, Qt.ItemDataRole.UserRole, (node_label, is_subgraph, path))

    def filter_nodes(self, text):
        search = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            visible_children = 0
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if search in child.text(0).lower():
                    child.setHidden(False)
                    visible_children += 1
                else:
                    child.setHidden(True)
            cat_item.setHidden(visible_children == 0)

    def on_entered(self):
        # Select first visible item
        for i in range(self.tree.topLevelItemCount()):
            cat = self.tree.topLevelItem(i)
            if not cat.isHidden():
                for j in range(cat.childCount()):
                    child = cat.child(j)
                    if not child.isHidden():
                        self.accept_item(child)
                        return

    def on_item_double_clicked(self, item, column):
        self.accept_item(item)

    def accept_item(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.node_selected.emit(*data)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down:
            self.tree.setFocus()
        else:
            super().keyPressEvent(event)
