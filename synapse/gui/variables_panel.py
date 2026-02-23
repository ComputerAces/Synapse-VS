from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit)
from PyQt6.QtCore import Qt, QTimer

class VariablesPanel(QWidget):
    """
    Real-time view of SynapseBridge variables.
    Shows current values and allows editing when paused/running.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Raw Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Connect edit signal
        self.table.cellChanged.connect(self.on_cell_changed)
        
        self.layout.addWidget(self.table)
        
        # Polling is handled by MainWindow calling 'refresh()' or specific timer?
        # Better to have own timer if valid
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        # We don't start timer automatically; MainWindow controls it via visibility
        
        self.is_updating = False

    def start_polling(self):
        self.timer.start(100) # 10Hz

    def stop_polling(self):
        self.timer.stop()

    def refresh(self):
        """Fetch bridge state and update table."""
        graph = self.main_window.get_current_graph()
        if not graph or not graph.bridge:
            self.table.setRowCount(0)
            return

        state = graph.bridge.dump_state()
        
        # Filter internal system vars?
        # Maybe show everything for debug, but sort "User" vars top?
        # The user specifically asked for global variables.
        # Everything in bridge is technically global to the graph.
        
        # We need to preserve selection and scroll pos
        
        self.is_updating = True # Block change signals
        
        # Naive approach: Rebuild table if keys change, update values if keys same.
        # This prevents scroll jumpiness.
        
        current_rows = self.table.rowCount()
        keys = sorted(state.keys())
        
        if self.table.rowCount() != len(keys):
            self.table.setRowCount(len(keys))
            
        for i, key in enumerate(keys):
            val = state[key]
            val_str = str(val)
            val_type = type(val).__name__
            
            # Key
            item_key = self.table.item(i, 0)
            if not item_key:
                item_key = QTableWidgetItem(key)
                item_key.setFlags(item_key.flags() ^ Qt.ItemFlag.ItemIsEditable) # Key read-only
                self.table.setItem(i, 0, item_key)
            else:
                if item_key.text() != key: item_key.setText(key)
            
            # Value
            item_val = self.table.item(i, 1)
            if not item_val:
                item_val = QTableWidgetItem(val_str)
                self.table.setItem(i, 1, item_val)
            else:
                # Only update if changed and NOT currently being edited?
                # QTableWidget editing is tricky with live updates.
                # If checking `self.table.state() != QAbstractItemView.EditingState`?
                if self.table.currentItem() != item_val: 
                     if item_val.text() != val_str: item_val.setText(val_str)
            
            # Type
            item_type = self.table.item(i, 2)
            if not item_type:
                item_type = QTableWidgetItem(val_type)
                item_type.setFlags(item_type.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, 2, item_type)
            else:
                if item_type.text() != val_type: item_type.setText(val_type)

        self.is_updating = False

    def on_cell_changed(self, row, col):
        if self.is_updating: return
        
        if col == 1: # Value changed
            key = self.table.item(row, 0).text()
            new_val_str = self.table.item(row, 1).text()
            
            # Try to infer type? 
            # Or just send as string and let nodes handle it?
            # Bridge stores what you give it.
            # Best effort conversion:
            val = new_val_str
            if new_val_str.lower() == "true": val = True
            elif new_val_str.lower() == "false": val = False
            elif new_val_str.isdigit(): val = int(new_val_str)
            else:
                try: val = float(new_val_str)
                except: val = new_val_str
            
            graph = self.main_window.get_current_graph()
            if graph and graph.bridge:
                graph.bridge.set(key, val, "VariablesWatch")
