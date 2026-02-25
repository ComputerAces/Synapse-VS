from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPalette

from synapse.core.types import DataType, TYPE_COLORS

class WireLegendV2(QWidget):
    """
    A floating tool window that shows the color key for wires and ports.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wire & Port Key")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                color: #cccccc;
                font-family: 'Segoe UI';
                font-size: 13px;
                border: 1px solid #444;
            }
            QLabel {
                padding: 0px;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        
        # Header
        # layout.addWidget(QLabel("Wire Types:"))
        
        # Dynamic Legend Items from synapse.core.types
        # Map DataType to readable name
        type_names = {
            DataType.FLOW: "Flow (Execution)",
            DataType.STRING: "String (Text)",
            DataType.NUMBER: "Number (Int/Float)",
            DataType.BOOLEAN: "Boolean (True/False)",
            DataType.LIST: "List (Array)",
            DataType.DICT: "Dict (Object)",
            DataType.IMAGE: "Image (Texture)",
            DataType.ANY: "Any (Dynamic)",
        }

        # Order of display
        display_order = [
            DataType.FLOW, 
            DataType.STRING, 
            DataType.NUMBER, 
            DataType.BOOLEAN, 
            DataType.LIST, 
            DataType.DICT, 
            DataType.IMAGE, 
            DataType.ANY
        ]
        
        for dtype in display_order:
            if dtype in TYPE_COLORS:
                hex_color = TYPE_COLORS[dtype]
                name = type_names.get(dtype, str(dtype.value).capitalize())
                
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(4)
                
                # Color indicator (Circle)
                indicator = QLabel()
                indicator.setFixedSize(16, 16)
                indicator.setStyleSheet(f"""
                    background-color: {hex_color};
                    border-radius: 8px;
                    border: 1px solid #555555;
                """)
                
                # Label
                lbl = QLabel(name)
                
                row_layout.addWidget(indicator)
                row_layout.addWidget(lbl)
                row_layout.addStretch()
                
                layout.addWidget(row_widget)
        
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
