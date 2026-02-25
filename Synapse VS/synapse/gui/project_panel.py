from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHeaderView, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class ProjectPanel(QWidget):
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Project Category (Type)
        from PyQt6.QtWidgets import QLabel, QLineEdit, QTextEdit
        
        # Name Input
        name_label = QLabel("Project Name (for Tool List):")
        self.layout.addWidget(name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My Tool (defaults to filename)")
        self.name_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.name_edit)
        
        # Version Input
        ver_label = QLabel("Project Version:")
        self.layout.addWidget(ver_label)
        self.version_edit = QLineEdit("1.0.0")
        self.version_edit.setPlaceholderText("e.g. 1.0.0")
        self.version_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.version_edit)
        
        # Category Input
        cat_label = QLabel("Node Category (optional):")
        self.layout.addWidget(cat_label)
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g. MyNodes (defaults to Favorites)")
        self.category_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.category_edit)
        
        # Project Description
        desc_label = QLabel("Description:")
        self.layout.addWidget(desc_label)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter a brief description of this project/subgraph...")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.description_edit)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Variable")
        add_btn.clicked.connect(self.add_variable)
        btn_layout.addWidget(add_btn)
        
        del_btn = QPushButton("Remove Variable")
        del_btn.clicked.connect(self.remove_variable)
        btn_layout.addWidget(del_btn)
        
        self.layout.addLayout(btn_layout)

    def add_variable(self):
        name, ok = QInputDialog.getText(self, "New Variable", "Variable Name:")
        if ok and name:
            self._add_row(name, "", "String")

    def remove_variable(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            name_item = self.table.item(current_row, 0)
            if name_item and name_item.text() == "path":
                QMessageBox.warning(self, "Action Denied", "The 'path' variable is a System Variable and cannot be removed.")
                return
            self.table.removeRow(current_row)

    def _add_row(self, name, value, type_str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(str(value)))
        self.table.setItem(row, 2, QTableWidgetItem(type_str))

    def get_variables(self):
        variables = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            value = self.table.item(row, 1).text()
            # type_str = self.table.item(row, 2).text() # Not strictly used yet, assumed string/auto
            variables[name] = value
        return variables

    def set_variables(self, variables):
        self.table.setRowCount(0)
        for name, value in variables.items():
            self._add_row(name, value, "String")
    
    def get_description(self):
        """Get the project description."""
        return self.description_edit.toPlainText()
    
    def set_description(self, text):
        """Set the project description."""
        self.description_edit.setPlainText(text or "")

    def get_category(self):
        return self.category_edit.text()

    def set_category(self, text):
        self.category_edit.setText(text or "")

    def get_name(self):
        return self.name_edit.text()

    def set_name(self, text):
        self.name_edit.setText(text or "")

    def get_version(self):
        return self.version_edit.text()

    def set_version(self, text):
        self.version_edit.setText(text or "1.0.0")
