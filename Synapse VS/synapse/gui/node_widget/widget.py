from PyQt6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, QRectF, pyqtSignal

from .visuals import NodeVisualsMixin
from .ports_manager import NodePortsMixin
from .actions import NodeActionsMixin
from .preview import NodePreviewMixin

class NodeWidget(NodeVisualsMixin, NodePortsMixin, NodeActionsMixin, NodePreviewMixin, QGraphicsObject):
    ports_changed = pyqtSignal()

    def __init__(self, name="Node"):
        super().__init__()
        self.node = None
        self.name = name
        self.node_type = name
        self.width = 180
        self.height = 100
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Initialize Mixins
        self.init_visuals()
        self.init_ports()
        self.init_preview()
        
        # Display Flag
        self.show_name = True
        
        # Title Item
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(self.name)
        self.title_item.setDefaultTextColor(self.title_text_color)
        self.title_item.setPos(5, 5)
        self.title_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.title_item.setAcceptHoverEvents(False)

        # Parenting Interaction
        from PyQt6.QtCore import QTimer
        self.capture_timer = QTimer()
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self._on_capture_timer_timeout)
        self._potential_parent = None
        self._is_dragging = False

        # Memo Note Item
        self.memo_item = QGraphicsTextItem(self)
        self.memo_item.setDefaultTextColor(QColor("#000000"))
        self.memo_item.setFont(QFont("Consolas", 10))
        self.memo_item.setTextWidth(160) # Default width
        self.memo_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.memo_item.setAcceptHoverEvents(False)
        self.memo_item.setVisible(False)

    def set_display_mode(self, show_name):
        self.show_name = show_name
        self.update_title()
        
    def set_user_name(self, name):
        self.name = name
        if self.node: self.node.name = name
        self.update_title()
        
    def update_title(self):
        if self.show_name:
            self.title_item.setPlainText(self.name)
        else:
            self.title_item.setPlainText(self.node_type)

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    # Note: We DO NOT override paint() here. 
    # We rely on NodeVisualsMixin.paint() being the first resolution in the MRO.

    def itemChange(self, change, value):
        # Trigger Port Updates
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
             for port in self.ports:
                 for wire in port.wires:
                     wire.update_path()
             if hasattr(self, 'parent_frame') and self.parent_frame:
                 self.parent_frame.on_child_moved(self)
             
             # Marked modified on move (removed emit from here to avoid reload spam)
             # The view/minimap can update via other signals or on mouseRelease
                      
        return super().itemChange(change, value)

    def update_connected_wires(self):
        """Forces an update of all wires connected to this node."""
        if hasattr(self, 'inputs'):
            for p in self.inputs:
                for w in p.wires:
                    w.update_path()
        if hasattr(self, 'outputs'):
            for p in self.outputs:
                for w in p.wires:
                    w.update_path()

    def mousePressEvent(self, event):
        self._is_dragging = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._is_dragging:
            self._check_for_parent_frames(event.scenePos())

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        self.capture_timer.stop()
        
        if self._potential_parent and getattr(self._potential_parent, 'is_capture_target', False):
            self._potential_parent.is_capture_target = False
            self._potential_parent.add_node(self)
            self._potential_parent.update()
        
        self._potential_parent = None
        super().mouseReleaseEvent(event)

    def _check_for_parent_frames(self, scene_pos):
        """Scan for frames under the current drag position."""
        from synapse.gui.frame_widget import FrameWidget
        
        # Search for frames at this point (excluding ourselves)
        items = self.scene().items(scene_pos)
        target_frame = None
        
        for item in items:
            if isinstance(item, FrameWidget) and item != getattr(self, 'parent_frame', None):
                target_frame = item
                break
        
        if target_frame:
            if target_frame != self._potential_parent:
                self._clear_capture()
                self._potential_parent = target_frame
                self.capture_timer.start(2000) # 2 Seconds hold
        else:
            self._clear_capture()

    def _on_capture_timer_timeout(self):
        """Highlight the frame to show it's ready to capture."""
        if self._potential_parent:
            self._potential_parent.is_capture_target = True
            self._potential_parent.update()

    def _clear_capture(self):
        """Reset capture state and timers."""
        if self._potential_parent:
            self._potential_parent.is_capture_target = False
            self._potential_parent.update()
        self.capture_timer.stop()
        self._potential_parent = None