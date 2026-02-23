import base64
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QRectF

class NodePreviewMixin:
    """
    Handles thumbnail preview display on the node face.
    """
    def init_preview(self):
        self.preview_pixmap = None
        self.preview_rect = QRectF(10, 40, 0, 0)
        self.preview_mode = "16:9" # Default mode
        self._has_preview = False

    def set_preview_data(self, mode: str, b64_data: str):
        """Sets the preview image and mode."""
        try:
            self.preview_mode = mode
            image_data = base64.b64decode(b64_data)
            image = QImage.fromData(image_data)
            if not image.isNull():
                self.preview_pixmap = QPixmap.fromImage(image)
                self._has_preview = True
                
                # Expand node if needed (Square mode is smaller)
                if self.preview_mode == "square":
                    if self.width < 120: self.width = 120
                    if self.height < 120: self.height = 120
                else:
                    if self.width < 220: self.width = 220
                    if self.height < 160: self.height = 160
                
                self.update_layout()
                self.update()
        except Exception as e:
            print(f"Error setting preview: {e}")

    def draw_preview(self, painter: QPainter):
        if not self._has_preview or not self.preview_pixmap:
            return

        if self.preview_mode == "square":
            target_w = 64
            target_h = 64
            self.preview_rect = QRectF(10, 40, target_w, target_h)
            
            # Draw background
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawRect(self.preview_rect)
            
            # Draw Pixmap with aspect ratio preservation
            pix_w = self.preview_pixmap.width()
            pix_h = self.preview_pixmap.height()
            
            scale = min(target_w / pix_w, target_h / pix_h)
            draw_w = int(pix_w * scale)
            draw_h = int(pix_h * scale)
            
            x_off = (target_w - draw_w) / 2
            y_off = (target_h - draw_h) / 2
            
            draw_rect = QRectF(self.preview_rect.left() + x_off, self.preview_rect.top() + y_off, draw_w, draw_h)
            painter.drawPixmap(draw_rect.toRect(), self.preview_pixmap)
        else:
            # 16:9 mode
            target_w = self.width - 20
            target_h = int(target_w * 9 / 16)
            self.preview_rect = QRectF(10, 40, target_w, target_h)
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawRect(self.preview_rect)
            painter.drawPixmap(self.preview_rect.toRect(), self.preview_pixmap)
        
        # Border
        from PyQt6.QtGui import QPen, QColor
        painter.setPen(QPen(QColor("#404040"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.preview_rect, 2, 2)
