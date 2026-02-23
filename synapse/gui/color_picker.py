from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QColorDialog, QWidget, QGridLayout,
                              QApplication)
from PyQt6.QtGui import QColor, QPainter, QBrush, QCursor, QScreen, QPixmap
from PyQt6.QtCore import Qt, QTimer


class ColorSwatch(QWidget):
    """A clickable color swatch."""
    
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked_callback = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)
        
    def mousePressEvent(self, event):
        if self.clicked_callback:
            self.clicked_callback(self.color)


class ColorPickerDialog(QDialog):
    """Color picker with palette, custom color, and eyedropper."""
    
    # Preset colors
    PALETTE = [
        "#3a5a8a", "#5a8a3a", "#8a5a3a", "#8a3a5a", "#3a8a8a", "#8a8a3a",
        "#2d2d30", "#4a4a4a", "#6a6a6a", "#8a8a8a", "#aaaaaa", "#cccccc",
        "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#dfe6e9",
        "#ff7675", "#74b9ff", "#a29bfe", "#fd79a8", "#00b894", "#e17055"
    ]
    
    def __init__(self, initial_color=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Color")
        self.setModal(True)
        self.selected_color = QColor(initial_color) if initial_color else QColor("#3a5a8a40")
        
        self._eyedropper_active = False
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preview
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Selected:"))
        self.preview_widget = QWidget()
        self.preview_widget.setFixedSize(60, 30)
        self.preview_widget.setAutoFillBackground(True)
        self.update_preview()
        preview_layout.addWidget(self.preview_widget)
        preview_layout.addStretch()
        layout.addLayout(preview_layout)
        
        # Palette grid
        palette_group = QLabel("Quick Colors:")
        layout.addWidget(palette_group)
        
        palette_grid = QGridLayout()
        palette_grid.setSpacing(4)
        
        for i, hex_color in enumerate(self.PALETTE):
            swatch = ColorSwatch(hex_color, self)
            swatch.clicked_callback = self.set_color
            row, col = divmod(i, 6)
            palette_grid.addWidget(swatch, row, col)
            
        layout.addLayout(palette_grid)
        
        # Alpha slider note
        alpha_label = QLabel("Tip: Use 'More Colors' for transparency/alpha control")
        alpha_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(alpha_label)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        more_btn = QPushButton("More Colors...")
        more_btn.clicked.connect(self.open_full_picker)
        button_layout.addWidget(more_btn)
        
        eyedropper_btn = QPushButton("🎯 Eyedropper")
        eyedropper_btn.clicked.connect(self.start_eyedropper)
        button_layout.addWidget(eyedropper_btn)
        
        layout.addLayout(button_layout)
        
        # OK/Cancel
        action_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        action_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)
        
        layout.addLayout(action_layout)
        
    def update_preview(self):
        """Update the preview swatch."""
        pal = self.preview_widget.palette()
        pal.setColor(self.preview_widget.backgroundRole(), self.selected_color)
        self.preview_widget.setPalette(pal)
        
    def set_color(self, color):
        """Set the selected color."""
        if isinstance(color, str):
            # Preserve alpha if it's a simple hex
            alpha = self.selected_color.alpha()
            self.selected_color = QColor(color)
            self.selected_color.setAlpha(alpha)
        else:
            # QColor - preserve alpha if not set
            if color.alpha() == 255 and self.selected_color.alpha() != 255:
                color.setAlpha(self.selected_color.alpha())
            self.selected_color = color
        self.update_preview()
        
    def open_full_picker(self):
        """Open the full Qt color dialog with alpha support."""
        color = QColorDialog.getColor(
            self.selected_color, 
            self, 
            "Choose Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if color.isValid():
            self.selected_color = color
            self.update_preview()
            
    def start_eyedropper(self):
        """Start eyedropper mode to capture screen color."""
        self._eyedropper_active = True
        self.hide()
        
        # Give the dialog time to hide
        QTimer.singleShot(100, self._do_eyedropper)
        
    def _do_eyedropper(self):
        """Perform the eyedropper capture."""
        # Grab mouse for screen-wide capture
        app = QApplication.instance()
        
        # Store original cursor
        self._original_cursor = app.overrideCursor()
        app.setOverrideCursor(Qt.CursorShape.CrossCursor)
        
        # Install event filter on app to catch mouse clicks
        app.installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """Handle mouse events during eyedropper mode."""
        if self._eyedropper_active:
            if event.type() == event.Type.MouseButtonPress:
                # Capture the pixel under cursor
                cursor_pos = QCursor.pos()
                screen = QApplication.screenAt(cursor_pos)
                
                if screen:
                    # Capture 1x1 pixel at cursor position
                    pixmap = screen.grabWindow(
                        0,  # Screen/window id
                        cursor_pos.x(),
                        cursor_pos.y(),
                        1, 1
                    )
                    
                    if not pixmap.isNull():
                        image = pixmap.toImage()
                        color = QColor(image.pixel(0, 0))
                        # Preserve current alpha
                        color.setAlpha(self.selected_color.alpha())
                        self.selected_color = color
                        self.update_preview()
                
                # Cleanup
                self._eyedropper_active = False
                app = QApplication.instance()
                app.restoreOverrideCursor()
                app.removeEventFilter(self)
                self.show()
                return True
                
            elif event.type() == event.Type.KeyPress:
                # ESC to cancel
                if event.key() == Qt.Key.Key_Escape:
                    self._eyedropper_active = False
                    app = QApplication.instance()
                    app.restoreOverrideCursor()
                    app.removeEventFilter(self)
                    self.show()
                    return True
                    
        return super().eventFilter(obj, event)
    
    def get_color(self):
        """Get the selected color."""
        return self.selected_color
    
    @staticmethod
    def pick_color(initial_color=None, parent=None):
        """Static convenience method to show dialog and get color."""
        dialog = ColorPickerDialog(initial_color, parent)
        if dialog.exec():
            return dialog.get_color()
        return None
