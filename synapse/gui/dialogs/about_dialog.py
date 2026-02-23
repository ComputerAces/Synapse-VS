from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Synapse VS")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        
        # Title
        title = QLabel("Synapse VS")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.1.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        # Copyright
        copyright_label = QLabel("Copyright © 2026 Computer Aces")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
        
        layout.addSpacing(10)
        
        # Website Link
        link_label = QLabel('<a href="http://compaces.com">http://compaces.com</a>')
        link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)
        
        # Email Link
        email_label = QLabel('<a href="mailto:compaces79@gmail.com">compaces79@gmail.com</a>')
        email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        email_label.setOpenExternalLinks(True)
        layout.addWidget(email_label)
        
        layout.addSpacing(20)
        
        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
