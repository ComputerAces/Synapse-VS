from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
from PyQt6.QtCore import Qt

class SearchableConsoleWidget(QWidget):
    """
    A wrapper around QTextEdit that provides a search/filter toolbar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_history = [] # Stores full log (list of strings)
        self.filter_text = ""
        self.max_history = 2000 # Limit to prevent memory issues
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 0)
        
        lbl = QLabel("Filter:")
        toolbar.addWidget(lbl)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter logs...")
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar.addWidget(self.search_input)
        
        cls_btn = QPushButton("Clear Filter")
        cls_btn.clicked.connect(self.clear_filter)
        toolbar.addWidget(cls_btn)
        
        # Output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        # Use Monospace font
        font = self.output.font()
        font.setFamily("Consolas") # Or Monospace
        # font.setStyleHint(func=None) # Removed invalid call
        # Just use stylesheet in main app or default font.
        
        layout.addLayout(toolbar)
        layout.addWidget(self.output)
        
    def on_search_changed(self, text):
        self.filter_text = text.lower()
        self.refresh_view()
        
    def clear_filter(self):
        self.search_input.clear()
        
    def refresh_view(self):
        """Rebuilds the QTextEdit content based on filter."""
        self.output.clear()
        
        # Optimization: If many lines, maybe we should batch?
        # For now, simple join is fine for <2000 lines.
        
        if not self.filter_text:
            # Show all
            self.output.setPlainText("\n".join(self.log_history))
        else:
            # Filter
            filtered = [line for line in self.log_history if self.filter_text in line.lower()]
            self.output.setPlainText("\n".join(filtered))
            
        self.output.moveCursor(self.output.textCursor().MoveOperation.End)

    def append(self, text):
        """API compatibility with QTextEdit.append"""
        # Clean text
        text = str(text).rstrip()
        
        # Add to history
        self.log_history.append(text)
        
        # Prune if too long
        if len(self.log_history) > self.max_history:
            self.log_history.pop(0)
            
        # Update View if matches
        if not self.filter_text or self.filter_text in text.lower():
            self.output.append(text)

    def clear(self):
        """Clears both history and view."""
        self.log_history = []
        self.output.clear()

    def setReadOnly(self, val):
        self.output.setReadOnly(val)
        
    def ensureCursorVisible(self):
        self.output.ensureCursorVisible()
