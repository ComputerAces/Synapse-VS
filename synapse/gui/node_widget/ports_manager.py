from PyQt6.QtWidgets import QGraphicsItem
from synapse.gui.port import PortItem
from synapse.core.types import DataType

class NodePortsMixin:
    """
    Handles Port creation, retrieval, and layout management.
    """
    def init_ports(self):
        self.inputs = []
        self.outputs = []

    def add_input(self, name, port_class="auto", data_type=DataType.ANY):
        if hasattr(self, 'node') and self.node:
            if name in getattr(self.node, 'hidden_ports', []): return None
            if name in getattr(self.node, 'hidden_inputs', []): return None
        port = PortItem(name, "input", self, port_class, data_type)
        self.inputs.append(port)
        self.update_layout()
        if hasattr(self, 'ports_changed'):
            self.ports_changed.emit()
        return port

    def add_output(self, name, port_class="auto", data_type=DataType.ANY):
        if hasattr(self, 'node') and self.node:
            if name in getattr(self.node, 'hidden_ports', []): return None
            if name in getattr(self.node, 'hidden_outputs', []): return None
        port = PortItem(name, "output", self, port_class, data_type)
        self.outputs.append(port)
        self.update_layout()
        if hasattr(self, 'ports_changed'):
            self.ports_changed.emit()
        return port
        
    def get_input(self, name):
        for p in self.inputs:
            if p.name.lower() == name.lower(): return p
        return None

    def get_output(self, name):
        for p in self.outputs:
            if p.name.lower() == name.lower(): return p
        return None
        
    @property
    def ports(self):
        return self.inputs + self.outputs

    def update_layout(self):
        from PyQt6.QtGui import QFontMetrics, QFont
        label_fm = QFontMetrics(QFont("Consolas", 8))
        
        # 1. Calculate Port Label Widths
        max_in_w = 0
        for p in self.inputs:
            w = label_fm.horizontalAdvance(p.name)
            if w > max_in_w: max_in_w = w
            
        max_out_w = 0
        for p in self.outputs:
            w = label_fm.horizontalAdvance(p.name)
            if w > max_out_w: max_out_w = w
            
        # 2. Calculate Title Width
        title_fm = QFontMetrics(self.title_item.font())
        title_w = title_fm.horizontalAdvance(self.name if self.show_name else self.node_type)
        
        # 3. Determine Final Width
        # (Port Icon [radius*2] + Margin [8]) + Label + Center Gap [20] + Label + (Port Icon + Margin)
        # Simplified: max_in_w + max_out_w + 40 (for ports and margins) + 20 (center gap)
        required_width = max_in_w + max_out_w + 60
        
        # Ensure it fits the title too
        required_width = max(required_width, title_w + 40)
        
        # Apply Min Width
        self.width = max(180, required_width)

        # 4. Position Ports
        y_offset = 40
        if getattr(self, "_has_preview", False):
            if getattr(self, "preview_mode", "16:9") == "square":
                preview_h = 64
            else:
                preview_h = (self.width - 20) * 9 / 16
            y_offset += preview_h + 10

        spacing = 25
        
        # [MEMO NODE SPECIAL LAYOUT]
        if self.node_type == "Memo":
            # 1. Update Memo Content
            note = self.node.properties.get("Memo Note", "") if self.node else ""
            self.memo_item.setPlainText(note)
            self.memo_item.setVisible(True)
            self.title_item.setVisible(False) # Memo is its own title
            
            # 2. Measure Memo
            memo_fm = QFontMetrics(self.memo_item.font())
            lines = note.split('\n')
            max_line_w = 0
            for line in lines:
                w = memo_fm.horizontalAdvance(line)
                if w > max_line_w: max_line_w = w
            
            # 3. Dynamic Re-sizing
            memo_w = max(100, max_line_w + 20)
            memo_h = max(60, (len(lines) * 18) + 20)
            
            self.width = max(180, memo_w)
            self.height = max(100, memo_h + 40) # Add buffer for ports/header
            
            # 4. Center Memo text
            memo_rect = self.memo_item.boundingRect()
            self.memo_item.setPos((self.width - memo_rect.width()) / 2, (self.height - memo_rect.height()) / 2 + 10)
            
            # Position regular ports if any (Memo usually has 1 in, 1 out)
            for i, port in enumerate(self.inputs):
                port.setPos(0, 35 + (i * spacing))
            for i, port in enumerate(self.outputs):
                port.setPos(self.width, 35 + (i * spacing))
        
        else:
            # Standard Layout
            self.memo_item.setVisible(False)
            self.title_item.setVisible(True)
            
            for i, port in enumerate(self.inputs):
                port.setPos(0, y_offset + (i * spacing))
            
            for i, port in enumerate(self.outputs):
                port.setPos(self.width, y_offset + (i * spacing))
                
            max_ports = max(len(self.inputs), len(self.outputs))
            required_height = y_offset + (max_ports * spacing) + 10
            if required_height > self.height:
                self.height = required_height
        
        self.prepareGeometryChange()
        self.update() # Trigger repaint

    def remove_port(self, port_name):
        port = self.get_input(port_name)
        if not port: port = self.get_output(port_name)
        if not port: return
        
        wires_to_remove = port.wires[:]
        for wire in wires_to_remove:
            if wire.scene(): wire.scene().removeItem(wire)
            if wire.start_port and wire in wire.start_port.wires: wire.start_port.wires.remove(wire)
            if wire.end_port and wire in wire.end_port.wires: wire.end_port.wires.remove(wire)
        port.wires.clear()
        
        if port.port_type == "input":
            if port in self.inputs: self.inputs.remove(port)
        else:
             if port in self.outputs: self.outputs.remove(port)
        if port.scene(): port.scene().removeItem(port)
        self.update_layout()
        if hasattr(self, 'ports_changed'):
            self.ports_changed.emit()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
             for port in self.ports:
                 for wire in port.wires:
                     wire.update_path()
             if hasattr(self, 'parent_frame') and self.parent_frame:
                 self.parent_frame.on_child_moved(self)
        return super().itemChange(change, value)