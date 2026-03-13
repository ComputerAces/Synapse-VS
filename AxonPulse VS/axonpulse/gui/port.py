from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF
from axonpulse.core.types import DataType, TYPE_COLORS

class PortItem(QGraphicsItem):
    def __init__(self, name, port_type, parent, port_class="auto", data_type=DataType.ANY):
        super().__init__(parent)
        self.name = name
        self.port_type = port_type # "input" or "output"
        self.port_class = port_class # "flow", "data", or "auto"
        self.data_type = data_type # [TYPE SYSTEM]
        self.parent_node = parent
        
        self.radius = 6
        self.margin = 2
        
        self.color = QColor("#aaaaaa")
        self.hover_color = QColor("#ffffff")
        self.connected_color = QColor("#006400") # Dark Green
        
        self.current_color = self.color
        self.wires = [] 
        
        display_name = self.name
        
        self.label = QGraphicsTextItem(display_name, self)
        self.label.setDefaultTextColor(QColor("#dddddd"))
        font = QFont("Consolas", 8)
        self.label.setFont(font)
        
        if self.port_type == "input":
            self.label.setPos(8, -10)
        else:
            # Re-calculate width for proper alignment
            self.label.setPos(-self.label.boundingRect().width() - 8, -10)
            
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self):
        return QRectF(-self.radius - self.margin, -self.radius - self.margin, 
                      (self.radius + self.margin) * 2, (self.radius + self.margin) * 2)

    def paint(self, painter, option, widget):
        # Determine Flow status (Strict Type/Class only)
        is_flow = False
        if self.data_type == DataType.FLOW or self.data_type == DataType.PROVIDER_FLOW:
            is_flow = True
        elif self.port_class == "flow":
            is_flow = True
        
        # [TYPE SYSTEM] Outline Color
        if self.data_type and self.data_type in TYPE_COLORS and self.data_type != DataType.FLOW:
            hex_col = TYPE_COLORS[self.data_type]
            outline_color = QColor(hex_col)
        else:
            # Flow ports get Vibrant Green Outline
            # Other ports get Dark Blue Outline (if no type color)
            outline_color = QColor("#006400") if is_flow else QColor("#00008b")
        
        painter.setPen(QPen(outline_color, 2))
        painter.setBrush(QBrush(self.current_color))
        painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

    def hoverEnterEvent(self, event):
        self.current_color = self.hover_color
        self.update()
        
        # [Visual Debugger] Show Live Data Tooltip on Hover if Breakpoint Active
        try:
            from axonpulse.gui.main_window_pkg import MainWindow
            from PyQt6.QtWidgets import QToolTip
            from PyQt6.QtGui import QCursor
            
            # Find Bridge
            bridge = None
            registry = None
            parent_win = self.scene().views()[0].window()
            if isinstance(parent_win, MainWindow):
                graph = parent_win.get_current_graph()
                if graph and graph.bridge:
                    bridge = graph.bridge
                    registry = graph.port_registry

            if bridge and registry and bridge.get("_AXON_BREAKPOINT_ACTIVE"):
                node_id = self.parent_node.node.node_id
                
                # Input vs Output key resolution
                if self.port_type == "output":
                    uuid_key = registry.bridge_key(node_id, self.name, "output")
                else:
                     # For inputs, look at the connected wire if possible, or the input mirror key
                     uuid_key = registry.bridge_key(node_id, self.name, "input")
                     if not bridge.get(uuid_key) and self.wires and self.wires[0].start_port:
                          # Fallback to the upstream output port if we haven't executed this node yet
                          s_node_id = self.wires[0].start_port.parent_node.node.node_id
                          s_port_name = self.wires[0].start_port.name
                          uuid_key = registry.bridge_key(s_node_id, s_port_name, "output")
                          
                legacy_key = f"{node_id}_{self.name}"
                
                # Fetch
                val = bridge.get(uuid_key)
                if val is None:
                    val = bridge.get(legacy_key)
                    
                if val is not None:
                     # Format for tooltip
                     val_str = str(val)
                     if len(val_str) > 200: val_str = val_str[:197] + "..."
                     QToolTip.showText(QCursor.pos(), f"🔴 {self.name}:\n{val_str}")
        except:
             pass
             
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.current_color = self.color
        self.update()
        super().hoverLeaveEvent(event)