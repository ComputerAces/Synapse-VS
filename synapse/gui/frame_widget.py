from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QApplication, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QCursor, QPainter
from PyQt6.QtCore import Qt, QRectF, QPointF


class FrameWidget(QGraphicsRectItem):
    """
    Visual frame that groups nodes together.
    Supports manual resizing, stable movement via manual delta propagation (to fix Z-order),
    and distinct header selection logic.
    """
    
    def __init__(self, nodes=None, parent=None):
        super().__init__(parent)
        
        self.name = "Group"
        self.color = QColor(58, 90, 138, 64)  # Semi-transparent blue
        self.border_color = QColor(58, 90, 138, 180)
        self.padding = 15
        self.header_height = 30
        self.child_nodes = []
        
        # Resizing State
        self._is_resizing = False
        self._resize_start_rect = None
        self._resize_start_mouse = None
        self._grip_size = 15
        self.manual_size = False # True if user resized manually
        self._is_fitting = False # Re-entrancy guard
        self.is_capture_target = False # True if a node is being dragged over for parenting
        
        # Make frame selectable and movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Lower Z value so frame is behind nodes AND wires
        # Wires use -1, so let's use -100 for frame
        self.setZValue(-100)
        
        # Title label
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(self.name)
        self.title_item.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        self.title_item.setFont(font)
        self.title_item.setPos(5, 2)
        
        self.setAcceptHoverEvents(True)
        
        # Initial Setup
        self.setRect(0, 0, 300, 200)
        
        if nodes:
            for node in nodes:
                self.add_node(node)
            self.auto_fit_nodes()
    
    def set_name(self, name):
        self.name = name
        self.title_item.setPlainText(name)
        
    def set_color(self, color):
        if isinstance(color, str):
            if len(color) == 9:  # #RRGGBBAA
                self.color = QColor(color[:7])
                self.color.setAlpha(int(color[7:9], 16))
            else:
                self.color = QColor(color)
                if self.color.alpha() == 255:
                    self.color.setAlpha(64)
        else:
            self.color = color
            
        self.border_color = QColor(self.color)
        self.border_color.setAlpha(min(255, self.color.alpha() + 120))
        self.update()
        
    def add_node(self, node):
        """Add a node to this frame and manage its grouping."""
        if node not in self.child_nodes:
            # If node was in another frame, remove it first
            if hasattr(node, 'parent_frame') and node.parent_frame and node.parent_frame != self:
                node.parent_frame.remove_node(node)
            
            self.child_nodes.append(node)
            node.parent_frame = self
            
            # [Z-ORDER FIX] DO NOT use setParentItem(self).
            # Keeping nodes in the scene allows separate Z-values for Wires vs Frames.
            # Nodes stay at Z=0, Wires at Z=-1, Frame at Z=-100.
            
            if not self.manual_size:
                self.auto_fit_nodes()
            
    def remove_node(self, node):
        if node in self.child_nodes:
            self.child_nodes.remove(node)
            node.parent_frame = None
            
            if not self.manual_size:
                self.auto_fit_nodes()
            
    def auto_fit_nodes(self):
        """Resize frame to fit items in scene coordinates."""
        if self._is_fitting or not self.child_nodes:
            return
            
        self._is_fitting = True
        try:
            # Nodes are NOT children, so we use their scene positions
            min_x = float('inf')
            min_y = float('inf')
            max_x = float('-inf')
            max_y = float('-inf')
            
            for node in self.child_nodes:
                sp = node.scenePos()
                # Calculate local coordinates relative to the frame's origin (self.pos())
                local_x = sp.x() - self.pos().x()
                local_y = sp.y() - self.pos().y()
                
                min_x = min(min_x, local_x)
                min_y = min(min_y, local_y)
                max_x = max(max_x, local_x + node.width)
                max_y = max(max_y, local_y + node.height)
                
            padding = self.padding
            target_rect = QRectF(
                min_x - padding,
                min_y - padding - self.header_height,
                max(200, (max_x - min_x) + (padding * 2)),
                max(100, (max_y - min_y) + (padding * 2) + self.header_height)
            )
            
            self.setRect(target_rect)
            
            # Position title relative to current top-left of rect
            self.title_item.setPos(target_rect.x() + 5, target_rect.y() + 2)
            
            self.update()
            if self.scene():
                self.scene().update()
            
            self._is_fitting = False
        except Exception as e:
            self._is_fitting = False
            print(f"Auto-fit failed: {e}")

    def paint(self, painter, option, widget):
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw Shadow/Glow if selected
        if self.isSelected():
            painter.setPen(QPen(QColor("#007acc"), 2))
            painter.setBrush(QBrush(QColor(0, 122, 204, 20)))
            painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 10, 10)
        elif self.is_capture_target:
            # Bright blue highlight for interactive parenting
            painter.setPen(QPen(QColor("#00bfff"), 4))
            painter.setBrush(QBrush(QColor(0, 191, 255, 30)))
            painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4), 10, 10)

        # Draw background
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw header
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), self.header_height)
        painter.setBrush(QBrush(self.border_color))
        painter.drawRoundedRect(header_rect, 8, 8)
        # Square off bottom
        painter.drawRect(QRectF(rect.x(), rect.y() + self.header_height/2, rect.width(), self.header_height/2))
        
        # Draw border
        painter.setPen(QPen(self.border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Resize Grip
        grip_rect = self._get_resize_grip_box()
        painter.setPen(QPen(self.border_color, 1))
        # Draw 3 small diagonal lines for grip
        for i in range(3):
            off = i * 4
            painter.drawLine(
                int(grip_rect.right() - 4 - off), int(grip_rect.bottom() - 2),
                int(grip_rect.right() - 2), int(grip_rect.bottom() - 4 - off)
            )

    def _get_resize_grip_box(self):
        r = self.rect()
        return QRectF(r.right() - self._grip_size, r.bottom() - self._grip_size, self._grip_size, self._grip_size)

    def mousePressEvent(self, event):
        if self._get_resize_grip_box().contains(event.pos()):
            self._is_resizing = True
            self._resize_start_rect = self.rect() 
            self._resize_start_mouse = event.scenePos()
            event.accept()
        else:
            # Prevent canvas scrolling during move
            view = event.widget().parent() if event.widget() else None
            from PyQt6.QtWidgets import QGraphicsView
            if isinstance(view, QGraphicsView):
                self._old_anchor = view.transformationAnchor()
                view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

            # Header click logic for properties
            if event.pos().y() <= self.rect().y() + self.header_height:
                win = QApplication.activeWindow()
                if win and hasattr(win, 'properties_panel'):
                    win.properties_panel.load_node(self)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            delta = event.scenePos() - self._resize_start_mouse
            new_w = max(150, self._resize_start_rect.width() + delta.x())
            new_h = max(80, self._resize_start_rect.height() + delta.y())
            self.setRect(self.rect().x(), self.rect().y(), new_w, new_h)
            self.manual_size = True
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        
        # Restore anchor
        if hasattr(self, '_old_anchor'):
            view = event.widget().parent() if event.widget() else None
            from PyQt6.QtWidgets import QGraphicsView
            if isinstance(view, QGraphicsView):
                view.setTransformationAnchor(self._old_anchor)
            del self._old_anchor
            
        super().mouseReleaseEvent(event)
        
    def hoverMoveEvent(self, event):
        if self._get_resize_grip_box().contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif event.pos().y() <= self.rect().y() + self.header_height:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)

    def on_child_moved(self, child):
        """Called when a child node's position changes."""
        if not self.manual_size and not self._is_resizing:
            # We must refit to handle both growth and shrinking
            self.auto_fit_nodes()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Manual propagation of movement to nodes (since they are no longer children)
            # value is the new QPointF
            new_pos = value
            old_pos = self.pos()
            delta = new_pos - old_pos
            
            if not self._is_fitting and not self._is_resizing:
                for node in self.child_nodes:
                    # If multiple items are selected, QGraphicsView already moves them all.
                    # We only manually move nodes that are NOT currently selected.
                    if not node.isSelected():
                        node.setPos(node.pos() + delta)
                    
                    # Force update wires for all nodes in group (wires depend on scenePos)
                    if hasattr(node, 'ports'):
                        for port in node.ports:
                            for wire in port.wires:
                                wire.update_path()

        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        
        auto_action = menu.addAction("Reset to Auto-Size")
        auto_action.setCheckable(True)
        auto_action.setChecked(not self.manual_size)
        
        delete_action = menu.addAction("Delete Frame")
        
        action = menu.exec(event.screenPos())
        
        if action == auto_action:
            self.manual_size = False
            self.auto_fit_nodes()
        elif action == delete_action:
            self.delete_frame()
            
    def delete_frame(self):
        # Remove from scene
        # First, un-reference nodes
        nodes = self.child_nodes[:]
        for node in nodes:
            self.remove_node(node)
            
        if self.scene():
            self.scene().removeItem(self)

    def serialize(self):
        return {
            "name": self.name,
            "color": self.color.name(QColor.NameFormat.HexArgb),
            "manual_size": self.manual_size,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rect": [self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height()],
            "node_ids": [node.node.node_id for node in self.child_nodes if hasattr(node, 'node') and node.node]
        }
    
    @staticmethod
    def deserialize(data, node_map):
        nodes = []
        for nid in data.get("node_ids", []):
            if nid in node_map:
                nodes.append(node_map[nid])
        
        # Create frame without nodes initially to avoid early auto-fit triggers
        frame = FrameWidget()
        frame.set_name(data.get("name", "Group"))
        frame.set_color(data.get("color", "#3a5a8a40"))
        frame.setPos(data.get("x", 0), data.get("y", 0))
        
        if data.get("manual_size"):
            frame.manual_size = True
            r = data.get("rect", [0, 0, 300, 200])
            frame.setRect(r[0], r[1], r[2], r[3])
            frame.title_item.setPos(r[0] + 5, r[1] + 2)
            
        # Add nodes (will reparent them correctly)
        for node in nodes:
            frame.add_node(node)
            
        # If not manual, final fit
        if not frame.manual_size:
            frame.auto_fit_nodes()
            
        return frame
