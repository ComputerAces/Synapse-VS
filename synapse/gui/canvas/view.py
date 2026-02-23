from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt, QVariantAnimation, QEasingCurve, pyqtSignal
from .scene import GraphicScene
from .factory import NodeFactory
from .serializer import GraphSerializer
from synapse.gui.node_widget.widget import NodeWidget

class NodeCanvas(QGraphicsView):
    modified = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = GraphicScene()
        self.setScene(self.scene)
        
        # 1. Hardware Acceleration (OpenGL Viewport)
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
        gl_viewport = QOpenGLWidget()
        # Enable multi-sampling for smooth edges
        from PyQt6.QtGui import QSurfaceFormat
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        gl_viewport.setFormat(fmt)
        self.setViewport(gl_viewport)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.factory = NodeFactory(self.scene)
        self.serializer = GraphSerializer(self.scene, self, self.factory)
        
        # 2. Magnifier (Spy Tool) State
        self._magnifier_enabled = False
        self._magnifier_pos = None # Viewport coordinates
        self._magnifier_radius = 180
        self._magnifier_zoom = 2.0


        # Tracing Support: Update minimaps on pan/scroll
        self.horizontalScrollBar().valueChanged.connect(lambda _: self.modified.emit())
        self.verticalScrollBar().valueChanged.connect(lambda _: self.modified.emit())
        
        # Connect scene changes (movements) to modified
        self.scene.changed.connect(lambda _: self.modified.emit())

    def zoom_to_fit(self):
        items = self.scene.items()
        if not items: return
        rect = self.scene.itemsBoundingRect()
        rect.adjust(-50, -50, 50, 50)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.modified.emit()

    def smooth_center_on(self, item):
        if not item: return
        target_rect = item.sceneBoundingRect()
        target_center = target_rect.center()
        current_center = self.mapToScene(self.viewport().rect().center())
        
        self.pan_animation = QVariantAnimation(self)
        self.pan_animation.setDuration(400)
        self.pan_animation.setStartValue(current_center)
        self.pan_animation.setEndValue(target_center)
        self.pan_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.pan_animation.valueChanged.connect(self.centerOn)
        self.pan_animation.start()

    def serialize(self):
        return self.serializer.serialize()

    def deserialize(self, data):
        self.serializer.deserialize(data)

    def analyze_subgraph_ports(self, data):
        return self.factory.analyze_subgraph_ports(data)

    def copy_selection(self):
        """Serializes selection and puts it in the clipboard."""
        from PyQt6.QtWidgets import QApplication
        import json
        data = self.serializer.serialize_selection()
        if data["nodes"] or data["frames"]:
            clipboard = QApplication.clipboard()
            clipboard.setText("synapse_copy:" + json.dumps(data))

    def paste_selection(self):
        """Restores selection from clipboard."""
        from PyQt6.QtWidgets import QApplication
        import json
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text.startswith("synapse_copy:"):
            try:
                data = json.loads(text.replace("synapse_copy:", ""))
                self.serializer.deserialize_selection(data)
                self.modified.emit()
            except Exception as e:
                print(f"Paste failed: {e}")

    def duplicate_selection(self):
        """Duplicates selected items without touching the clipboard."""
        from PyQt6.QtCore import QPointF
        data = self.serializer.serialize_selection()
        if data["nodes"] or data["frames"]:
            self.serializer.deserialize_selection(data, offset=QPointF(50, 50))
            self.modified.emit()

    def delete_selection(self):
        """Deletes all selected items and cleans up connections."""
        from PyQt6.QtWidgets import QGraphicsPathItem
        selected = self.scene.selectedItems()
        if not selected: return

        if len(selected) > 1:
            from PyQt6.QtWidgets import QMessageBox
            res = QMessageBox.question(self, "Delete Items", 
                                     f"Are you sure you want to delete {len(selected)} selected items?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res != QMessageBox.StandardButton.Yes:
                return
        
        # Filter for top-level items we know how to delete
        to_delete = []
        for item in selected:
            if hasattr(item, 'delete_node'): # NodeWidget
                to_delete.append(item)
            elif isinstance(item, QGraphicsPathItem) and hasattr(item, 'start_port'): # Wire
                to_delete.append(item)
            elif hasattr(item, 'delete_frame'): # FrameWidget (assuming it exists)
                to_delete.append(item)
            elif hasattr(item, 'on_delete'): # Catch-all
                to_delete.append(item)
                
        # If nothing specific found, just remove from scene (fallback)
        if not to_delete: to_delete = selected

        # Use Undo Command
        if self.parent() and hasattr(self.parent(), 'undo_stack'):
            from synapse.gui.undo_commands import DeleteItemsCommand
            command = DeleteItemsCommand(self.scene, to_delete)
            self.parent().undo_stack.push(command)
            self.modified.emit()
        else:
            # Fallback (Safety)
            for item in to_delete:
                if hasattr(item, 'delete_node'):
                    item.delete_node()
                elif hasattr(item, 'delete_frame'):
                    item.delete_frame()
                elif self.scene:
                    self.scene.removeItem(item)
            self.modified.emit()

    def configure_node_ports(self, new_node, node_type_label):
        self.factory.configure_node_ports(new_node, node_type_label)
        
    def set_magnifier_enabled(self, enabled):
        """Toggles the magnifier overlay."""
        self._magnifier_enabled = enabled
        self.setMouseTracking(enabled)
        if not enabled:
            self._magnifier_pos = None
        self.viewport().update()

    def set_magnifier_radius(self, radius):
        """Sets the magnifier circle radius (in viewport pixels)."""
        self._magnifier_radius = radius
        if self._magnifier_enabled:
            self.viewport().update()


        
    def create_standard_node(self, node_type, pos):
        if self.parent() and hasattr(self.parent(), 'undo_stack'):
            from synapse.gui.undo_commands import AddNodeCommand
            command = AddNodeCommand(self.scene, node_type, pos, self.factory)
            self.parent().undo_stack.push(command)
            return command.node_widget
        return self.factory.create_standard_node(node_type, pos)

    def create_subgraph_node(self, file_path, pos):
        if self.parent() and hasattr(self.parent(), 'undo_stack'):
            from synapse.gui.undo_commands import AddNodeCommand
            command = AddNodeCommand(self.scene, file_path, pos, self.factory)
            self.parent().undo_stack.push(command)
            return command.node_widget
        return self.factory.create_subgraph_node(file_path, pos)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dropEvent(self, event):
        payload = event.mimeData().text()
        pos = self.mapToScene(event.position().toPoint())
        if payload.startswith("subgraph:"):
            self.create_subgraph_node(payload.replace("subgraph:", "").strip(), pos)
        else:
            self.create_standard_node(payload, pos)
        self.modified.emit()
        event.acceptProposedAction()

    def zoom(self, factor):
        self.scale(factor, factor)
        self.modified.emit()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0: self.zoom(1.1)
        else: self.zoom(1/1.1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_PageUp:
            self.zoom(1.1); event.accept()
        elif event.key() == Qt.Key.Key_PageDown:
            self.zoom(1/1.1); event.accept()
        elif event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selection(); event.accept()
        elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.paste_selection(); event.accept()
        elif event.key() == Qt.Key.Key_D and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.duplicate_selection(); event.accept()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo(); event.accept()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.redo(); event.accept()
        else:
            super().keyPressEvent(event)

    def undo(self):
        # Delegate to parent GraphWidget's undo stack
        if self.parent() and hasattr(self.parent(), 'undo_stack'):
            self.parent().undo_stack.undo()
            
    def redo(self):
        if self.parent() and hasattr(self.parent(), 'undo_stack'):
            self.parent().undo_stack.redo()

    def mousePressEvent(self, event):
        self.setFocus()
        
        # Capture start positions for Move Undo
        if event.button() == Qt.MouseButton.LeftButton:
            self._move_start_positions = {}
            for item in self.scene.selectedItems():
                if isinstance(item, NodeWidget):
                    self._move_start_positions[item] = item.pos()
                    
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            from PyQt6.QtGui import QMouseEvent
            fake = QMouseEvent(event.type(), event.position(), event.globalPosition(), 
                               Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, event.modifiers())
            super().mousePressEvent(fake)
            return
            
        item = self.itemAt(event.position().toPoint())
        if item: self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else: self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Tracks cursor for magnifier if enabled."""
        if self._magnifier_enabled:
            self._magnifier_pos = event.position().toPoint()
            self.viewport().update()
        super().mouseMoveEvent(event)


    def contextMenuEvent(self, event):
        # 1. Try to let items handle it (Wires, Nodes, etc)
        super().contextMenuEvent(event)
        if event.isAccepted():
            return

        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        
        # Standard Actions
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selection)
        menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_selection)
        menu.addAction(paste_action)
        
        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Del")
        delete_action.triggered.connect(self.delete_selection)
        menu.addAction(delete_action)
        
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.duplicate_selection)
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        # Snippets
        from synapse.gui.node_widget.widget import NodeWidget
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, NodeWidget)]
        
        if selected_nodes:
             # Group Action
             group_action = QAction("Group Selection", self)
             group_action.setShortcut("Ctrl+G")
             group_action.triggered.connect(lambda: self.create_group(selected_nodes))
             menu.addAction(group_action)

             # Snippet Action
             menu.addSeparator()
             snippet_action = QAction("Save as Snippet...", self)
             
             def trigger_save():
                  p = self.parent()
                  while p:
                      if hasattr(p, "save_selection_as_snippet"):
                          p.save_selection_as_snippet()
                          break
                      p = p.parent()
             
             snippet_action.triggered.connect(trigger_save)
             menu.addAction(snippet_action)
            
        menu.exec(event.globalPos())

    def create_group(self, nodes):
        from synapse.gui.frame_widget import FrameWidget
        # Calculate center to place frame if needed, 
        # but FrameWidget constructor handles pos based on nodes.
        
        frame = FrameWidget(nodes)
        self.scene.addItem(frame)
        self.modified.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            from PyQt6.QtGui import QMouseEvent
            fake = QMouseEvent(event.type(), event.position(), event.globalPosition(), 
                               Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, event.modifiers())
            super().mouseReleaseEvent(fake)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            return
            
        super().mouseReleaseEvent(event)
        
        # Check for Move Undo
        if hasattr(self, '_move_start_positions') and self._move_start_positions:
            moved_nodes = {}
            for item, start_pos in self._move_start_positions.items():
                if item.pos() != start_pos:
                    moved_nodes[item] = (start_pos, item.pos())
            
            if moved_nodes and self.parent() and hasattr(self.parent(), 'undo_stack'):
                from synapse.gui.undo_commands import MoveNodeCommand
                command = MoveNodeCommand(self.scene, moved_nodes)
                self.parent().undo_stack.push(command)
                self.modified.emit()
            
            self._move_start_positions = {}

    def get_view_state(self):
        """Returns the current zoom and center point."""
        center = self.mapToScene(self.viewport().rect().center())
        return {
            "zoom": self.transform().m11(),
            "center_x": center.x(),
            "center_y": center.y()
        }

    def set_view_state(self, state):
        """Restores the zoom and center point."""
        if not state: return
        
        # 1. Restore Zoom
        zoom = state.get("zoom", 1.0)
        self.resetTransform()
        self.scale(zoom, zoom)
        
        # 2. Restore Center
        cx = state.get("center_x", 0)
        cy = state.get("center_y", 0)
        
        # [PERSISTENCE FIX] If viewport is invisible/0-size, centerOn might fail.
        # Use a single-shot timer to ensure it centers once the widget has size.
        if self.viewport().width() == 0:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(10, lambda: self.centerOn(cx, cy))
        else:
            self.centerOn(cx, cy)

    def drawForeground(self, painter, rect):
        """Draws the circular magnifier overlay."""
        super().drawForeground(painter, rect)
        
        if not self._magnifier_enabled or not self._magnifier_pos:
            return
            
        from PyQt6.QtGui import QPainterPath, QColor, QPen, QBrush, QTransform
        from PyQt6.QtCore import QRectF, QPointF
        
        # 1. Setup Coordinates
        # Magnifier center in viewport coords
        m_pos_v = self._magnifier_pos
        # Magnifier center in scene coords
        m_pos_s = self.mapToScene(m_pos_v)
        
        # Calculate current view scale to maintain static screen-space size
        scale = self.transform().m11()
        radius = self._magnifier_radius / scale if scale > 0 else self._magnifier_radius
        
        # Set zoom level to 1:1 relative to the screen (un-do canvas zoom)
        # Resulting scale in lens: scale * zoom = 1.0
        zoom = 1.0 / scale if scale > 0 else 1.0
        
        # 2. Render Magnified Scene to a Pixmap
        # Source rect in scene (zoomed out from center)
        src_w = (radius * 2) / zoom
        src_h = (radius * 2) / zoom
        src_rect_s = QRectF(m_pos_s.x() - src_w/2, m_pos_s.y() - src_h/2, src_w, src_h)

        
        # Draw Circle Overlay
        painter.save()
        
        # 3. Create Clip Path (Circle in scene)
        clip_path = QPainterPath()
        clip_path.addEllipse(m_pos_s, radius, radius)
        painter.setClipPath(clip_path)

        
        # Render the scene into this circle with transform
        # We want to translate and scale so m_pos_s aligns and everything is bigger.
        transform = QTransform()
        transform.translate(m_pos_s.x(), m_pos_s.y())
        transform.scale(zoom, zoom)
        transform.translate(-m_pos_s.x(), -m_pos_s.y())
        
        painter.setTransform(transform, True) # Combine with current
        
        # Render scene
        self.scene.render(painter, src_rect_s, src_rect_s)
        
        painter.restore()
        
        # 4. Draw Border & Glass Effect
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Outer Ring
        border_pen = QPen(QColor(60, 60, 60, 200), 4)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(m_pos_s, radius, radius)
        
        # Inner Gloss/Shine (Subtle)
        shine_path = QPainterPath()
        shine_path.addEllipse(m_pos_s.x() - radius*0.5, m_pos_s.y() - radius*0.8, radius, radius*0.4)
        painter.setPen(Qt.PenStyle.NoPen)
        shine_brush = QBrush(QColor(255, 255, 255, 30))
        painter.setBrush(shine_brush)
        painter.drawPath(shine_path)
        
        painter.restore()
