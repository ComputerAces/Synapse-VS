from PyQt6.QtGui import QColor, QPen, QBrush, QPainterPath, QPainter
from PyQt6.QtCore import Qt, QTime
import math

class NodeVisualsMixin:
    """
    Handles the visual appearance and painting logic for the NodeWidget.
    """
    def init_visuals(self):
        # UI Properties
        self.title_color = QColor("#2d2d30")
        self.title_text_color = QColor("#cccccc")
        self.body_color = QColor("#1e1e1e")
        self.border_color = QColor("#000000")
        self.selected_color = QColor("#007acc")
        
        # Custom Styling based on Node Type (Exact Match)
        if self.node_type == "Start Node":
            self.body_color = QColor("#006400") # Dark Green
            self.title_color = self.body_color
        elif self.node_type == "Return Node":
            self.body_color = QColor("#00008b") # Dark Blue
            self.title_color = self.body_color
        elif self.node_type == "Debug Node":
            self.body_color = QColor("#CC5500") # Dark Orange
            self.title_color = self.body_color
        elif self.node_type == "Memo":
            self.body_color = QColor("#F0E68C") # Khaki/Yellow
            self.title_color = self.body_color
            self.border_color = QColor("#BDB76B") # Dark Khaki

    def update_subgraph_status(self, found):
        if found:
            self.title_color = QColor("#00008b") # Dark Blue
        else:
            self.title_color = QColor("#4b0082") # Dark Purple
        self.update()

    def highlight_pulse(self, duration=1000):
        """Triggers a transient highlight pulse."""
        self._is_running = True
        self.update()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, self.reset_highlight)

    def reset_highlight(self):
        self._is_running = False
        self._running_since = 0
        self._is_fading = True
        self._fade_start = QTime.currentTime().msecsSinceStartOfDay()
        self.update()

    def highlight_pulse_blue(self, duration=2000):
        """Triggers a blue highlight pulse (Provider Call indicator)."""
        self._is_pulsing_blue = True
        self.update()
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, self.reset_pulse_blue)

    def reset_pulse_blue(self):
        self._is_pulsing_blue = False
        self._pulsing_blue_since = 0
        self._is_fading_blue = True
        self._fade_start_blue = QTime.currentTime().msecsSinceStartOfDay()
        self.update()

    def paint(self, painter, option, widget):
        # 1. Determine State
        is_running = getattr(self, "_is_running", False)
        is_pulsing_blue = getattr(self, "_is_pulsing_blue", False)
        is_selected = self.isSelected()
        
        is_running_service = False
        is_subgraph_active = False
        if self.node and getattr(self.node, "bridge", None):
            bridge = self.node.bridge
            is_running_service = bridge.get(f"{self.node.node_id}_IsServiceRunning")
            is_subgraph_active = bridge.get(f"{self.node.node_id}_SubGraphActivity")

        # 2. Draw Body (Always solid base)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 10, 10)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.body_color))
        painter.drawPath(path)

        # 2b. Draw Overlay Highlight
        is_fading = getattr(self, "_is_fading", False)
        is_fading_blue = getattr(self, "_is_fading_blue", False)
        
        if is_running_service or is_running or is_pulsing_blue or is_subgraph_active or is_fading or is_fading_blue or getattr(self, "_is_waiting", False) or getattr(self, "_is_error", False):
            ms = QTime.currentTime().msecsSinceStartOfDay()
            
            highlight_color = None
            alpha = 0

            # [NEW] Error State (Red Overlay) - Highest Priority
            if getattr(self, "_is_error", False):
                # Flashing Dark Red (Breathing)
                pulse = (math.sin(ms / 200.0) + 1) / 2.0
                alpha = int(40 + (100 * pulse))
                highlight_color = QColor(139, 0, 0, alpha) # Dark Red (8B0000)
                alpha = alpha # For border use

            # 1. Provider Pulse (Priority Visual)
            elif is_pulsing_blue:
                if not hasattr(self, "_pulsing_blue_since") or self._pulsing_blue_since == 0:
                    self._pulsing_blue_since = ms
                elapsed = ms - self._pulsing_blue_since
                pulse = (math.sin(elapsed / 100.0) + 1) / 2.0
                alpha = int(100 + (100 * pulse))
                highlight_color = QColor(0, 191, 255, alpha) # Blue
            
            elif is_fading_blue:
                fade_start = getattr(self, "_fade_start_blue", ms)
                fade_elapsed = ms - fade_start
                factor = max(0.0, 1.0 - (fade_elapsed / 1000.0))
                alpha = int(150 * factor)
                if factor <= 0: self._is_fading_blue = False
                highlight_color = QColor(0, 191, 255, alpha) # Blue

            # [NEW] Waiting Pulse (Yellow/Orange)
            elif getattr(self, "_is_waiting", False):
                if not hasattr(self, "_waiting_since") or self._waiting_since == 0:
                    self._waiting_since = ms
                
                # Check for duration expiry (auto-clear fallback)
                duration = getattr(self, "_waiting_duration", 0)
                elapsed = ms - self._waiting_since
                
                if duration > 0 and elapsed > duration:
                    self._is_waiting = False
                    alpha = 0
                else:
                    # Slow Pulse (Breathing)
                    pulse = (math.sin(elapsed / 300.0) + 1) / 2.0
                    alpha = int(100 + (80 * pulse))
                    highlight_color = QColor(255, 165, 0, alpha) # Orange

            # 2. Running Tracking (Heartbeat) - Secondary if blue pulse active
            elif is_running:
                if not hasattr(self, "_running_since") or self._running_since == 0:
                    self._running_since = ms
                elapsed = ms - self._running_since
                if elapsed > 1000:
                    pulse = (math.sin((elapsed - 1000) / 150.0) + 1) / 2.0
                    alpha = int(80 + (100 * pulse))
                else:
                    alpha = 120 
                highlight_color = QColor(0, 255, 0, alpha) # Green
            
            elif is_fading:
                fade_start = getattr(self, "_fade_start", ms)
                fade_elapsed = ms - fade_start
                factor = max(0.0, 1.0 - (fade_elapsed / 1000.0))
                alpha = int(120 * factor)
                if factor <= 0: self._is_fading = False
                highlight_color = QColor(0, 255, 0, alpha) # Green
            
            # 3. Service/Subgraph Baseline
            elif is_running_service:
                alpha = 120
                highlight_color = QColor(128, 0, 128, alpha) # Purple
            elif is_subgraph_active:
                alpha = 120
                highlight_color = QColor(0, 191, 255, alpha) # Blue

            if highlight_color and alpha > 0:
                painter.setBrush(QBrush(highlight_color))
                painter.drawPath(path)
        
        # 3. Draw Header
        header_path = QPainterPath()
        header_path.setFillRule(Qt.FillRule.WindingFill)
        header_path.addRoundedRect(0, 0, self.width, 30, 10, 10)
        header_path.addRect(0, 20, self.width, 10) 
        
        current_header_color = self.title_color
        if self.node:
            is_debug = getattr(self.node, "is_debug", False) or self.node.properties.get("is_debug")
            is_native = getattr(self.node, "is_native", False)
            is_service = getattr(self.node, "is_service", False)
            
            if self.node_type == "Debug Node": current_header_color = QColor("#CC5500") # Dark Orange
            elif self.node_type == "Start Node": current_header_color = QColor("#006400") # Dark Green
            elif self.node_type == "Return Node": current_header_color = QColor("#00008b") # Dark Blue
            elif is_debug: current_header_color = QColor("#CC5500")
            elif is_service: current_header_color = QColor("#B88600")
            elif is_native: current_header_color = QColor("#800080")
            elif "header_color" in self.node.properties:
                 try: current_header_color = QColor(self.node.properties["header_color"])
                 except: pass
            else:
                current_header_color = QColor("#008B8B")

        painter.setBrush(QBrush(current_header_color))
        painter.drawPath(header_path)
        
        # 3b. Draw Preview (if any)
        if hasattr(self, "draw_preview"):
            self.draw_preview(painter)
        
        # 4. Draw Border (Kinetic Aware)
        border_alpha = 255
        is_next = getattr(self, "_is_next", False)
        
        if is_fading:
            border_alpha = alpha
            
        if is_next:
            # [STEP DEBUG] Bright Orange Halo
            painter.setPen(QPen(QColor("#FF8C00"), 4))
        elif getattr(self, "_is_error", False):
            # [ERROR] Dark Red Pulsing Border
            painter.setPen(QPen(QColor(139, 0, 0), 3 if alpha < 100 else 4))
        elif is_running_service:
            painter.setPen(QPen(QColor(128, 0, 128, border_alpha), 3))
        elif is_subgraph_active:
            painter.setPen(QPen(QColor(0, 191, 255, border_alpha), 3))
        elif is_running or is_fading:
            painter.setPen(QPen(QColor(0, 255, 0, border_alpha), 3))
        elif is_selected:
            painter.setPen(QPen(self.selected_color, 4))
        else:
            painter.setPen(QPen(self.border_color, 1))
            
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)