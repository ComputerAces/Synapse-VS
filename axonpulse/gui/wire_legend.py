from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLayout, QScrollArea
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPalette

from axonpulse.core.types import DataType, TYPE_COLORS

class WireLegendV2(QWidget):
    """
    A floating tool window that shows the color key for wires and ports.
    Categorized for all AxonPulse data types.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wire & Port Key")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setMinimumWidth(220)
        self.setMaximumHeight(600)
        
        # Styling
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: #2d2d30;
                color: #cccccc;
                font-family: 'Segoe UI';
                font-size: 13px;
                border: 1px solid #444;
            }
            QLabel {
                padding: 0px;
                border: none;
                color: #cccccc;
            }
            QLabel#CategoryHeader {
                font-weight: bold;
                color: #569cd6;
                margin-top: 8px;
                border-bottom: 1px solid #444;
                padding-bottom: 2px;
                font-size: 11px;
                text-transform: uppercase;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setObjectName("MainContainer")
        container_layout = QVBoxLayout(container)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Categorized Data Types
        categories = {
            "Core Flow & Logic": [
                (DataType.FLOW, "Execution Flow"),
                (DataType.ANY, "Dynamic / Any"),
                (DataType.INT, "Number (Integer/Float)"),
                (DataType.STRING, "String (Text)"),
                (DataType.BOOLEAN, "Boolean (True/False)"),
            ],
            "Collections": [
                (DataType.LIST, "List (Array)"),
                (DataType.DICT, "Dictionary (Object)"),
            ],
            "Media & Assets": [
                (DataType.IMAGE, "Image / Texture"),
                (DataType.COLOR, "Color (RGBA)"),
                (DataType.AUDIO, "Audio Stream"),
                (DataType.BYTES, "Raw Bytes"),
            ],
            "System & Services": [
                (DataType.PROVIDER, "Service Provider"),
                (DataType.PROVIDER_FLOW, "Provider Lifecycle"),
                (DataType.DB_CONNECTION, "Database Link"),
                (DataType.FTPACTIONS, "FTP Operations"),
                (DataType.PASSWORD, "Secure Password"),
                (DataType.TRIGGER, "Event Trigger"),
            ],
            "UI & Interaction": [
                (DataType.DIALOG_MODE, "Dialog Type"),
                (DataType.MOUSEACTION, "Mouse Interaction"),
                (DataType.SENDKEY_MODE, "Keyboard Intake"),
                (DataType.WINSTATEACTION, "Window State"),
                (DataType.MSGTYPE, "Message Category"),
            ],
            "Scene & Rendering": [
                (DataType.SCENEOBJECT, "Scene Object"),
                (DataType.SCENELIST, "Scene Selection"),
                (DataType.DRAW_EFFECT, "Visual Effect"),
                (DataType.WRITE_TYPE, "Write Strategy"),
                (DataType.COMPARE_TYPE, "Comparison Rule"),
            ]
        }
        
        for cat_name, items in categories.items():
            header = QLabel(cat_name)
            header.setObjectName("CategoryHeader")
            container_layout.addWidget(header)
            
            for dtype, label in items:
                hex_color = TYPE_COLORS.get(dtype, "#AAAAAA")
                
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(2, 2, 2, 2)
                row_layout.setSpacing(8)
                
                # Color indicator (Circle)
                indicator = QLabel()
                indicator.setFixedSize(12, 12)
                indicator.setStyleSheet(f"""
                    background-color: {hex_color};
                    border-radius: 6px;
                    border: 1px solid #555555;
                """)
                
                # Label
                lbl = QLabel(label)
                lbl.setStyleSheet("font-size: 11px;")
                
                row_layout.addWidget(indicator)
                row_layout.addWidget(lbl)
                row_layout.addStretch()
                
                container_layout.addWidget(row_widget)
        
        container_layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
