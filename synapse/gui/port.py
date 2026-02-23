from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF
from synapse.core.types import DataType, TYPE_COLORS

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
        
        self.label = QGraphicsTextItem(self.name, self)
        self.label.setDefaultTextColor(QColor("#dddddd"))
        font = QFont("Consolas", 8)
        self.label.setFont(font)
        
        if self.port_type == "input":
            self.label.setPos(8, -10)
        else:
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
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.current_color = self.color
        self.update()
        super().hoverLeaveEvent(event)