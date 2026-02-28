from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtGui import QColor, QPen, QTransform
from PyQt6.QtCore import Qt, QTimer
from synapse.gui.wire import Wire
from synapse.gui.port import PortItem

class GraphicScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QColor("#f5f5f5")) # Light Gray
        
        self.drag_wire = None
        self.drag_start_port = None
        
        self._last_scene_pos = None
        
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.handle_auto_scroll)
        self.scroll_dx = 0
        self.scroll_dy = 0
        self.scroll_margin = 30
        self.scroll_speed = 20

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_size = 25
        grid_color = QColor("#d0d0d0")
        
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        painter.setPen(QPen(grid_color))
        
        y = top
        while y < rect.bottom():
             painter.drawLine(int(rect.left()), y, int(rect.right()), y)
             y += grid_size
             
        x = left
        while x < rect.right():
             painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
             x += grid_size

    def mousePressEvent(self, event):
        # 1. Start Wire Dragging if on a Port
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, PortItem):
            # We allow dragging from both inputs and outputs (logic in release handles validation)
            self.drag_start_port = item
            self.drag_wire = Wire(start_port=item)
            self.drag_wire.set_end_pos(event.scenePos())
            self.addItem(self.drag_wire)
            event.accept()
            return

        super().mousePressEvent(event)
        self.scroll_dx = 0
        self.scroll_dy = 0

    def mouseMoveEvent(self, event):
        self._last_scene_pos = event.scenePos()
        
        if self.drag_wire:
            self.drag_wire.set_end_pos(self._last_scene_pos)
            
            # Auto-scroll logic
            if self.views():
                view = self.views()[0]
                view_pos = view.mapFromScene(self._last_scene_pos)
                width = view.viewport().width()
                height = view.viewport().height()
                
                self.scroll_dx = 0
                self.scroll_dy = 0
                
                if view_pos.x() < self.scroll_margin: self.scroll_dx = -self.scroll_speed
                elif view_pos.x() > width - self.scroll_margin: self.scroll_dx = self.scroll_speed
                
                if view_pos.y() < self.scroll_margin: self.scroll_dy = -self.scroll_speed
                elif view_pos.y() > height - self.scroll_margin: self.scroll_dy = self.scroll_speed
                
                if self.scroll_dx != 0 or self.scroll_dy != 0:
                    if not self.scroll_timer.isActive(): self.scroll_timer.start(30)
                else:
                    self.scroll_timer.stop()
        
        super().mouseMoveEvent(event)

    def handle_auto_scroll(self):
        if not self.views(): return
        view = self.views()[0]
        
        h = view.horizontalScrollBar()
        v = view.verticalScrollBar()
        
        if self.scroll_dx != 0: h.setValue(h.value() + self.scroll_dx)
        if self.scroll_dy != 0: v.setValue(v.value() + self.scroll_dy)
            
        # If we are dragging a wire, update its end point to the current mouse position in scene
        if self.drag_wire and self._last_scene_pos:
            # We need to re-map from viewport to scene because view has scrolled
            cursor_pos = view.mapFromGlobal(view.cursor().pos())
            scene_pos = view.mapToScene(cursor_pos)
            self.drag_wire.set_end_pos(scene_pos)
            self._last_scene_pos = scene_pos

    def _emit_modified(self):
        if self.views():
            view = self.views()[0]
            if hasattr(view, "modified"):
                view.modified.emit()

    def mouseReleaseEvent(self, event):
        self.scroll_timer.stop()
        if self.drag_wire:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, PortItem) and item != self.drag_start_port:
                
                if item.port_type == self.drag_start_port.port_type:
                    self.removeItem(self.drag_wire)
                    self.drag_wire = None; self.drag_start_port = None
                    super().mouseReleaseEvent(event)
                    return

                def get_port_category(port):
                    if hasattr(port, 'port_class') and port.port_class == "flow": return "FLOW"
                    flow_names = ["Flow", "True", "False", "Loop", "In", "Out", "Exec", "Then", "Else", "Break", "Continue", "Completed", "Scan"]
                    if port.name in flow_names or "flow" in port.name.lower(): return "FLOW"
                    return "DATA"

                if get_port_category(self.drag_start_port) != get_port_category(item):
                    self.removeItem(self.drag_wire)
                    self.drag_wire = None; self.drag_start_port = None
                    super().mouseReleaseEvent(event)
                    return

                port_a = self.drag_start_port
                port_b = item
                final_start = port_a if port_a.port_type == "output" else port_b
                final_end = port_b if port_b.port_type == "input" else port_a
                
                if port_a.port_type == port_b.port_type:
                    self.removeItem(self.drag_wire)
                    self.drag_wire = None; self.drag_start_port = None
                    super().mouseReleaseEvent(event)
                    return

                for wire in final_start.wires:
                     if wire.end_port == final_end:
                         self.removeItem(self.drag_wire)
                         self.drag_wire = None; self.drag_start_port = None
                         super().mouseReleaseEvent(event)
                         return

                if self.drag_wire in self.drag_start_port.wires:
                     self.drag_start_port.wires.remove(self.drag_wire)
                
                self.drag_wire.start_port = final_start
                self.drag_wire.end_port = final_end
                
                
                final_start.wires.append(self.drag_wire)
                final_end.wires.append(self.drag_wire)
                
                # Use Undo Command if possible
                if self.views() and self.views()[0].parent() and hasattr(self.views()[0].parent(), 'undo_stack'):
                    from synapse.gui.undo_commands import ConnectWireCommand
                    # We remove the temp drag wire first, then let the command create the permanent one
                    self.removeItem(self.drag_wire)
                    # Remove from ports as well since command will add it
                    final_start.wires.remove(self.drag_wire)
                    final_end.wires.remove(self.drag_wire)
                    
                    command = ConnectWireCommand(self, final_start, final_end)
                    self.views()[0].parent().undo_stack.push(command)
                else:
                    self.drag_wire.update_path()
                    self.drag_wire.update_style_from_port(final_start)
                
                self.drag_wire = None
                self.drag_start_port = None
                self._emit_modified()
                super().mouseReleaseEvent(event)
                return

            # [WIRE DROP ON EMPTY CANVAS] Show type-filtered context menu
            drop_scene_pos = event.scenePos()
            source_port = self.drag_start_port
            
            self.removeItem(self.drag_wire)
            self.drag_wire = None
            self.drag_start_port = None
            
            self._show_wire_drop_menu(source_port, drop_scene_pos)
            return
            
        super().mouseReleaseEvent(event)

    # ─── Wire Drop Context Menu ───────────────────────────────────────
    def _show_wire_drop_menu(self, source_port, drop_scene_pos):
        """Shows the searchable QuickPicker dialog when a wire is dropped on empty canvas."""
        from synapse.gui.dialogs.quick_picker import QuickPicker
        
        picker = QuickPicker(parent=self.views()[0] if self.views() else None, source_port=source_port)
        
        def on_node_selected(label, is_subgraph, path):
            if not self.views(): return
            view = self.views()[0]
            
            # Create the node at the drop position
            if is_subgraph:
                new_node = view.create_subgraph_node(path, drop_scene_pos)
            else:
                new_node = view.create_standard_node(label, drop_scene_pos)
            
            if new_node:
                self._auto_wire(source_port, new_node)
                self._emit_modified()
        
        picker.node_selected.connect(on_node_selected)
        
        # Position the picker at the cursor
        if self.views():
            view = self.views()[0]
            global_pos = view.mapToGlobal(view.mapFromScene(drop_scene_pos))
            picker.move(global_pos)
            picker.exec()

    def _auto_wire(self, source_port, target_node):
        """Connects source_port to the first compatible input on target_node."""
        from synapse.core.types import DataType
        
        source_type = getattr(source_port, 'data_type', DataType.ANY)
        is_flow = (source_type == DataType.FLOW or 
                   (hasattr(source_port, 'port_class') and source_port.port_class == "flow"))
        
        best_port = None
        for port in getattr(target_node, 'inputs', []):
            if port.port_type != "input": continue
            
            inp_type = getattr(port, 'data_type', DataType.ANY)
            inp_is_flow = (inp_type == DataType.FLOW or
                          (hasattr(port, 'port_class') and port.port_class == "flow"))
            
            # Flow-to-Flow matching
            if is_flow and inp_is_flow:
                best_port = port; break
            
            # Data-to-Data matching (skip flow inputs)
            if not is_flow and not inp_is_flow:
                if inp_type == DataType.ANY or inp_type == source_type or source_type == DataType.ANY:
                    best_port = port; break
        
        if not best_port:
            return
            
        # Create wire via undo system if available
        if self.views() and self.views()[0].parent() and hasattr(self.views()[0].parent(), 'undo_stack'):
            from synapse.gui.undo_commands import ConnectWireCommand
            command = ConnectWireCommand(self, source_port, best_port)
            self.views()[0].parent().undo_stack.push(command)
        else:
            wire = Wire(source_port, best_port)
            self.addItem(wire)