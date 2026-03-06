from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal

class ProjectPanel(QWidget):
    dataChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Project Metadata Section
        title = QLabel("Project Metadata")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 5px;")
        self.layout.addWidget(title)
        
        # Name Input
        self.layout.addWidget(QLabel("Project Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. My Tool")
        self.name_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.name_edit)
        
        # Version Input
        self.layout.addWidget(QLabel("Project Version:"))
        self.version_edit = QLineEdit("1.0.0")
        self.version_edit.setPlaceholderText("e.g. 1.0.0")
        self.version_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.version_edit)
        
        # Category Input
        self.layout.addWidget(QLabel("Node Category:"))
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g. MyNodes")
        self.category_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.category_edit)
        
        # Project Description
        self.layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter a brief description...")
        self.description_edit.setMaximumHeight(120)
        self.description_edit.textChanged.connect(lambda: self.dataChanged.emit())
        self.layout.addWidget(self.description_edit)
        
        # Variables Notice
        var_notice = QLabel("<i>Note: Project Variables are now managed via Get/Set nodes in the graph.</i>")
        var_notice.setWordWrap(True)
        var_notice.setStyleSheet("color: #666; margin-top: 20px;")
        self.layout.addWidget(var_notice)
        
        # Spacer to push content up
        self.layout.addStretch()

    def get_variables(self):
        """[DEPRECATED] Variables are now managed via nodes."""
        return {}

    def set_variables(self, variables):
        """[DEPRECATED] Variables are now managed via nodes."""
        pass
    
    def get_description(self):
        return self.description_edit.toPlainText()
    
    def set_description(self, text):
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
