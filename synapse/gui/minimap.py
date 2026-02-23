from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF, QPointF

from synapse.gui.node_widget.widget import NodeWidget
from synapse.gui.wire import Wire

class MinimapWidget(QWidget):
    """A minimap showing an overview of the current graph."""
    
    def __init__(self, main_window, graph=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.graph = graph # If None, follows main_window.get_current_graph()
        self.setMinimumHeight(100)
        self.scale_factor = 0.1
        self.offset_x = 0
        self.offset_y = 0
        self.cached_bounds = None
        
    def update_minimap(self):
        """Recalculate bounds and trigger repaint."""
        self.update()
        
    def paintEvent(self, event):
        """Draw the minimap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        
        graph = self.graph if self.graph else self.main_window.get_current_graph()
        if not graph or not graph.canvas:
            painter.setPen(QColor("#666666"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Graph")
            return
        
        scene = graph.canvas.scene
        if not scene:
            return
        
        # Calculate scene bounds (Ignore frames as requested)
        node_items = [i for i in scene.items() if isinstance(i, NodeWidget)]
        if not node_items:
            # Fallback if no nodes, maybe just wires?
            scene_rect = scene.itemsBoundingRect()
        else:
            # Union of all node bounding rects in scene coordinates
            scene_rect = node_items[0].sceneBoundingRect()
            for i in range(1, len(node_items)):
                scene_rect = scene_rect.united(node_items[i].sceneBoundingRect())
            
            # Also include wires if they exist to prevent them being clipped at edges
            for i in scene.items():
                if isinstance(i, Wire):
                    scene_rect = scene_rect.united(i.sceneBoundingRect())

        if scene_rect.isEmpty():
            return
        
        # Calculate scale to fit widget
        widget_rect = self.rect().adjusted(10, 10, -10, -10)
        scale_x = widget_rect.width() / scene_rect.width() if scene_rect.width() > 0 else 1
        scale_y = widget_rect.height() / scene_rect.height() if scene_rect.height() > 0 else 1
        self.scale_factor = min(scale_x, scale_y, 0.25) # Allow slightly more zoom for small graphs
        
        self.offset_x = widget_rect.x() - scene_rect.x() * self.scale_factor
        self.offset_y = widget_rect.y() - scene_rect.y() * self.scale_factor
        
        # Center if scaled down
        scaled_width = scene_rect.width() * self.scale_factor
        scaled_height = scene_rect.height() * self.scale_factor
        if scaled_width < widget_rect.width():
            self.offset_x += (widget_rect.width() - scaled_width) / 2
        if scaled_height < widget_rect.height():
            self.offset_y += (widget_rect.height() - scaled_height) / 2
        
        self.cached_bounds = scene_rect
        
        # Draw wires first (behind nodes)
        for item in scene.items():
            if isinstance(item, Wire):
                self._draw_wire(painter, item)
        
        # Draw nodes
        for item in scene.items():
            if isinstance(item, NodeWidget):
                self._draw_node(painter, item)
        
        # Draw viewport frame
        self._draw_viewport(painter, graph.canvas)
        
    def _draw_node(self, painter, node):
        """Draw a single node as a small rectangle."""
        # Use scenePos() for absolute coordinates (handles nodes inside frames)
        sp = node.scenePos()
        x = sp.x() * self.scale_factor + self.offset_x
        y = sp.y() * self.scale_factor + self.offset_y
        w = node.width * self.scale_factor
        h = node.height * self.scale_factor
        
        # Priority: Debug (Orange) > Service (Dim Yellow) > Native (Purple) > Standard
        is_debug = getattr(node.node, "is_debug", False) if node.node else False
        is_service = getattr(node.node, "is_service", False) if node.node else False
        is_native = getattr(node.node, "is_native", False) if node.node else False
        
        if "Debug" in node.node_type:
            color = QColor("#CC5500") # Dark Orange
        elif "Start" in node.node_type:
            color = QColor("#006400") # Dark Green
        elif "Return" in node.node_type:
            color = QColor("#00008b") # Dark Blue
        elif is_debug:
            color = QColor("#CC5500")
        elif is_service:
            color = QColor("#B88600")
        elif is_native:
            color = QColor("#800080")
        else:
            # Standard nodes (usually sub-processing) use Dark Cyan
            color = QColor("#008B8B")
        
        # [TRACE OPTIMIZATION] Check Visibility Flags
        show_trace = True
        trace_subgraphs = True
        if hasattr(self.main_window, 'show_trace_checkbox'):
            show_trace = self.main_window.show_trace_checkbox.isChecked()
        if hasattr(self.main_window, 'trace_subgraphs_checkbox'):
            trace_subgraphs = self.main_window.trace_subgraphs_checkbox.isChecked()

        is_running = False
        is_fading = False
        is_running_service = False
        is_subgraph_active = False
        is_waiting = False

        if show_trace:
            # Check if we should trace this specific graph (Sub-Graph logic)
            can_trace_this = True
            if not trace_subgraphs:
                main_graph = self.main_window.get_current_graph()
                if self.graph and self.graph != main_graph:
                    can_trace_this = False
            
            if can_trace_this:
                is_running = getattr(node, '_is_running', False)
                is_fading = getattr(node, '_is_fading', False)
                is_waiting = getattr(node, '_is_waiting', False)
                if node.node and getattr(node.node, "bridge", None):
                    is_running_service = node.node.bridge.get(f"{node.node.node_id}_IsServiceRunning")
                    is_subgraph_active = node.node.bridge.get(f"{node.node.node_id}_SubGraphActivity")

        if is_waiting:
            # Pulsing blue effect using time-based sine wave
            import math
            from PyQt6.QtCore import QTime
            ms = QTime.currentTime().msecsSinceStartOfDay()
            pulse = (math.sin(ms / 300.0) + 1.0) / 2.0  # 0.0 to 1.0
            r = int(0 + 100 * pulse)
            g = int(120 + 100 * pulse)
            b = 255
            color = QColor(r, g, b)
            painter.setPen(QPen(QColor(0, 150, 255), 2))
        elif is_running_service:
            color = QColor("#800080") # Bold Purple
            painter.setPen(QPen(QColor("#00ff00"), 2))
        elif is_subgraph_active:
            color = QColor("#00bfff") # Deep Sky Blue
            painter.setPen(QPen(QColor("#00bfff"), 2))
        elif is_running:
            color = QColor("#00ff00")
            painter.setPen(QPen(QColor("#00ff00"), 2))
        elif is_fading:
            # Dim the original color to indicate fading
            color = color.lighter(130) if color.lightness() < 128 else color.darker(130)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 128), 1))
        else:
            painter.setPen(QPen(QColor("#000000"), 1))
        
        painter.setBrush(QBrush(color))
        painter.drawRect(QRectF(x, y, max(w, 3), max(h, 3)))
        
    def _draw_wire(self, painter, wire):
        """Draw a wire as a thin line."""
        if not wire.start_port or not wire.end_port:
            return
        
        start = wire.start_port.scenePos()
        end = wire.end_port.scenePos()
        
        x1 = start.x() * self.scale_factor + self.offset_x
        y1 = start.y() * self.scale_factor + self.offset_y
        x2 = end.x() * self.scale_factor + self.offset_x
        y2 = end.y() * self.scale_factor + self.offset_y
        
        # [TRACE OPTIMIZATION] Check Visibility Flags
        show_trace = True
        trace_subgraphs = True
        if hasattr(self.main_window, 'show_trace_checkbox'):
            show_trace = self.main_window.show_trace_checkbox.isChecked()
        if hasattr(self.main_window, 'trace_subgraphs_checkbox'):
            trace_subgraphs = self.main_window.trace_subgraphs_checkbox.isChecked()

        alpha = 0
        if show_trace:
            can_trace_this = True
            if not trace_subgraphs:
                main_graph = self.main_window.get_current_graph()
                if self.graph and self.graph != main_graph:
                    can_trace_this = False
            
            if can_trace_this:
                is_active = getattr(wire, "_is_active", False)
                is_fading = getattr(wire, "_is_fading", False)
                
                if is_active:
                    alpha = 200
                elif is_fading:
                    from PyQt6.QtCore import QTime
                    ms = QTime.currentTime().msecsSinceStartOfDay()
                    fade_start = getattr(wire, "_fade_start", 0)
                    elapsed = ms - fade_start if fade_start > 0 else 9999
                    factor = max(0.0, 1.0 - (elapsed / 1000.0))
                    alpha = int(200 * factor)
                    if factor <= 0:
                        wire._is_fading = False

        if alpha > 0:
            painter.setPen(QPen(QColor(0, 255, 0, alpha), 2))
        else:
            painter.setPen(QPen(wire.color if hasattr(wire, 'color') else QColor("#cccccc"), 1))
            
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
    def _draw_viewport(self, painter, canvas):
        """Draw the current viewport as a white frame."""
        view_rect = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
        
        x = view_rect.x() * self.scale_factor + self.offset_x
        y = view_rect.y() * self.scale_factor + self.offset_y
        w = view_rect.width() * self.scale_factor
        h = view_rect.height() * self.scale_factor
        
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(x, y, w, h))
        
    def mousePressEvent(self, event):
        """Handle click to pan the main view."""
        if event.button() == Qt.MouseButton.LeftButton and self.cached_bounds:
            graph = self.graph if self.graph else self.main_window.get_current_graph()
            if not graph or not graph.canvas:
                return
            
            # Convert click position to scene coordinates
            click_x = event.position().x()
            click_y = event.position().y()
            
            scene_x = (click_x - self.offset_x) / self.scale_factor
            scene_y = (click_y - self.offset_y) / self.scale_factor
            
            # Center view on this point
            graph.canvas.centerOn(scene_x, scene_y)
            self.update()
