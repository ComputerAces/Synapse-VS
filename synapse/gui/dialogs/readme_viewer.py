import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QDesktopServices

class ReadmeViewer(QDialog):
    def __init__(self, parent=None, readme_path="README.md"):
        super().__init__(parent)
        self.setWindowTitle("Synapse VS - Documentation")
        self.resize(800, 600)
        self.current_path = os.path.abspath(readme_path)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(False) 
        self.text_browser.anchorClicked.connect(self.handle_anchor)
        
        self.load_file(self.current_path)
            
        layout.addWidget(self.text_browser)
        
        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)
        layout.addLayout(footer)

    def load_file(self, file_path):
        """Loads and displays a markdown file."""
        if not os.path.exists(file_path):
            self.text_browser.setText(f"<h1>Error</h1><p>File not found: {file_path}</p>")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.current_path = os.path.abspath(file_path)
            base_url = QUrl.fromLocalFile(os.path.dirname(self.current_path) + os.sep)
            self.text_browser.document().setBaseUrl(base_url)
            self.text_browser.setMarkdown(content)
            self.setWindowTitle(f"Documentation - {os.path.basename(file_path)}")
        except Exception as e:
            self.text_browser.setText(f"<h1>Error Reading File</h1><p>{str(e)}</p>")

    def handle_anchor(self, url: QUrl):
        # Handle external links
        if url.scheme() in ("http", "https", "mailto"):
            QDesktopServices.openUrl(url)
            return

        # Resolve local path
        if url.isLocalFile():
            # QTextBrowser already helps resolve relative links against baseUrl
            path = url.toLocalFile()
        else:
            # Fallback for relative paths if not already resolved to file scheme
            target = url.toString()
            if os.path.isabs(target):
                path = target
            else:
                current_dir = os.path.dirname(self.current_path)
                path = os.path.normpath(os.path.join(current_dir, target))
        
        # Check if it's a local .md file link
        if path.lower().endswith(".md"):
            if os.path.exists(path):
                self.load_file(path)
            else:
                # Fallback to system opener
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            # For non-md files (images, pdfs, etc), use system default
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
