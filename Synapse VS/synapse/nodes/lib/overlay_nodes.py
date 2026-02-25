from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import threading
import time

@NodeRegistry.register("Overlay Highlighter", "UI/Overlays")
class OverlayHighlighterNode(SuperNode):
    """
    Spawns a temporary visual highlight on the screen at specified coordinates.
    Useful for guiding user attention or debugging UI element positions.
    
    Inputs:
    - Flow: Trigger the overlay display.
    - Rect: The [x, y, w, h] coordinates for the highlight.
    - Color: The [r, g, b, a] color of the highlight.
    
    Outputs:
    - Flow: Pulse triggered after the overlay thread starts.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Duration Ms"] = 1500
        self.properties["Thickness"] = 3
        self.properties["Rect"] = [0, 0, 100, 100]
        self.properties["Color"] = [255, 0, 0, 128]
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Rect": DataType.LIST,
            "Color": DataType.LIST,
            "Duration Ms": DataType.NUMBER,
            "Thickness": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, Rect=None, Color=None, **kwargs):
        Rect = Rect if Rect is not None else kwargs.get("Rect") or self.properties.get("Rect", [0, 0, 100, 100])
        Color = Color if Color is not None else kwargs.get("Color") or self.properties.get("Color", [255, 0, 0, 128])
        
        if not Rect or not isinstance(Rect, list) or len(Rect) < 4:
            self.logger.error("Rect must be [x, y, w, h].")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        x, y, w, h = int(Rect[0]), int(Rect[1]), int(Rect[2]), int(Rect[3])
        if w <= 0 or h <= 0:
            self.logger.error(f"Invalid rect dimensions {Rect}.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Default to red if no color
        if not Color or not isinstance(Color, list) or len(Color) < 3:
            r, g, b, a = 255, 0, 0, 128
        else:
            r = int(Color[0])
            g = int(Color[1])
            b = int(Color[2])
            a = int(Color[3]) if len(Color) > 3 else 128

        r, g, b, a = r, g, b, a

        duration_ms = int(kwargs.get("Duration Ms") or self.properties.get("Duration Ms", 1500))
        thickness = int(kwargs.get("Thickness") or self.properties.get("Thickness", 3))

        # Launch overlay in a separate thread to avoid blocking execution
        overlay_thread = threading.Thread(
            target=self._show_overlay,
            args=(x, y, w, h, r, g, b, a, duration_ms, thickness),
            daemon=True
        )
        overlay_thread.start()

        self.logger.info(f"Overlay at ({x},{y}) {w}x{h} for {duration_ms}ms")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


    def _show_overlay(self, x, y, w, h, r, g, b, a, duration_ms, thickness):
        """Spawns a temporary transparent overlay using PyQt6."""
        try:
            from PyQt6.QtWidgets import QWidget, QApplication
            from PyQt6.QtCore import Qt, QTimer, QRect
            from PyQt6.QtGui import QPainter, QColor, QPen

            # Check if QApplication exists
            app = QApplication.instance()
            if not app:
                self.logger.warning("No QApplication — cannot show overlay (headless mode?).")
                return

            class OverlayWidget(QWidget):
                """Internal PyQt widget for the visual highlight."""
                def __init__(self, rect, color, pen_width, duration):
                    super().__init__()
                    self._rect = rect
                    self._color = color
                    self._pen_width = pen_width

                    self.setWindowFlags(
                        Qt.WindowType.FramelessWindowHint |
                        Qt.WindowType.WindowStaysOnTopHint |
                        Qt.WindowType.Tool |
                        Qt.WindowType.WindowTransparentForInput
                    )
                    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                    self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

                    pad = pen_width
                    self.setGeometry(
                        rect.x() - pad,
                        rect.y() - pad,
                        rect.width() + pad * 2,
                        rect.height() + pad * 2
                    )

                    QTimer.singleShot(duration, self.close)

                def paintEvent(self, event):
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                    fill_color = QColor(
                        self._color[0], self._color[1],
                        self._color[2], self._color[3] // 3
                    )
                    painter.fillRect(self.rect(), fill_color)

                    border_color = QColor(
                        self._color[0], self._color[1],
                        self._color[2], self._color[3]
                    )
                    pen = QPen(border_color, self._pen_width)
                    painter.setPen(pen)
                    painter.drawRect(
                        self._pen_width // 2,
                        self._pen_width // 2,
                        self.width() - self._pen_width,
                        self.height() - self._pen_width
                    )
                    painter.end()

            from PyQt6.QtCore import QMetaObject, Q_ARG
            import functools

            target_rect = QRect(x, y, w, h)
            color_tuple = (r, g, b, a)

            def create_and_show():
                overlay = OverlayWidget(target_rect, color_tuple, thickness, duration_ms)
                overlay.show()
                if not hasattr(app, '_synapse_overlays'):
                    app._synapse_overlays = []
                app._synapse_overlays.append(overlay)
                QTimer.singleShot(duration_ms + 500, lambda: self._cleanup_overlay(app, overlay))

            QTimer.singleShot(0, create_and_show)

        except ImportError:
            self.logger.error("PyQt6 not available for overlay.")
        except Exception as e:
            self.logger.error(f"Overlay Error: {e}")

    @staticmethod
    def _cleanup_overlay(app, overlay):
        """Remove overlay reference to allow garbage collection."""
        try:
            if hasattr(app, '_synapse_overlays') and overlay in app._synapse_overlays:
                app._synapse_overlays.remove(overlay)
        except Exception:
            pass
