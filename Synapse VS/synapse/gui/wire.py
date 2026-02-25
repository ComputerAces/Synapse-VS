from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QPainterPath, QPen, QColor, QPainter
from PyQt6.QtCore import Qt, QPointF, QTime
from synapse.core.types import DataType, TYPE_COLORS

class Wire(QGraphicsPathItem):
    def __init__(self, start_port=None, end_port=None):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        
        self.start_pos = QPointF(0, 0)
        self.end_pos = QPointF(0, 0)
        
        # If created with ports, grab their positions and register
        if self.start_port:
            self.start_pos = self.start_port.scenePos()
            self.start_port.wires.append(self)
            
        if self.end_port:
            self.end_pos = self.end_port.scenePos()
            self.end_port.wires.append(self)
            
        self.setZValue(-1) # Draw behind nodes
        
        # Style
        self.color = QColor("#cccccc") # Default
        self.width = 3 # Thicker wires requested
        
        # Determine Color based on Port Type
        if self.start_port:
            self.update_style_from_port(self.start_port)
        elif self.end_port:
            self.update_style_from_port(self.end_port)
        
        self.pen = QPen(self.color, self.width)
        self.setPen(self.pen)
        
        self.update_path()
        self.setAcceptHoverEvents(True)

    def update_style_from_port(self, port):
        # Reset width default (Global Resize: "sized up to fit")
        self.width = 4 # Default for data wires (was 6)

        # 1. Use Typed Color if available
        if hasattr(port, 'data_type') and port.data_type in TYPE_COLORS:
             hex_col = TYPE_COLORS[port.data_type]
             self.color = QColor(hex_col)
             
             # [PROVIDER SPECIAL] Thicker Wires for Provider Flow
             if self.check_provider_scope(port):
                 self.color = QColor("#D11575") # Deep Pink
                 self.width = 6
                 return # Provider scope is final
                 
             # [ERROR FLOW CHECK]
             elif self.check_error_flow(port):
                 self.color = QColor("#8B0000") # Dark Red
                 self.width = 6
                 return
                 
             # [STANDARD FLOW CHECK] 
             # Match new vibrant green (#2ECC71) or legacy dark green
             curr_col = self.color.name().lower()
             if curr_col == "#2ecc71" or curr_col == "#006400":
                 self.width = 6
                 return
                 
             # [CRITICAL FIX] If it's ANY (Gray) but the name/class says it's Flow,
             # don't return here! Let it fall through to the heuristics.
             if port.data_type != DataType.ANY:
                 return

        # 2. Check explicit class from PortItem (Meta-Tag Support)
        if hasattr(port, 'port_class') and port.port_class != "auto":
            if port.port_class == "flow":
                if self.check_provider_scope(port):
                    self.color = QColor("#D11575") # Deep Pink
                    self.width = 6
                else:
                    self.color = QColor("#006400") # Dark Green (Inactive)
                    self.width = 6
            else:
                # Default Data
                self.color = QColor("#00008b")
                self.width = 4
            return

        # 3. Fallback to Name Heuristic (Legacy)
        name = port.name.lower()
        # Common Flow names - synced with port.py
        flow_names = ["flow", "exec", "true", "false", "loop", "in", "out", "then", "else", "scan", "completed", "success", "done", "ok", "next", "trigger", "continue", "finish", "start", "end", "run", "process", "up", "down", "left", "right", "yes", "no", "valid", "invalid"]
        error_names = ["error", "error flow", "panic", "failure", "fail", "catch"]
        
        if name in error_names or any(n in name for n in error_names):
             self.color = QColor("#8B0000") # Dark Red
             self.width = 6
        elif name in flow_names or "flow" in name or any(fn in name for fn in ["success", "done", "exec", "trigger", "next"]):
             if self.check_provider_scope(port):
                self.color = QColor("#D11575")
                self.width = 6
             else:
                self.color = QColor("#2ECC71") # Vibrant Green
                self.width = 6
        else:
             # ONLY set Blue if it's not already something else (like Green from Step 1)
             if self.color.name().lower() == "#cccccc": # Only if still default
                self.color = QColor("#00008b") # Dark Blue (Data)

    def check_error_flow(self, port):
        """Checks if a port is an error/panic flow."""
        name = port.name.lower()
        if name in ["error", "error flow", "panic", "failure", "fail", "catch"]:
            return True
        return False

    def check_provider_scope(self, port, visited=None):
        """
        Recursive check to see if this port is downstream from a Provider Flow.
        Returns True if:
        1. Port IS a Provider Flow port.
        2. Port is a Flow output and its Node has a Flow Input that is in Provider Scope.
        """
        # 1. Explicit Type Check
        if hasattr(port, 'data_type'):
            # Check Enum or String
            dt_str = str(port.data_type).lower()
            if "provider_flow" in dt_str:
                return True
                
        # Only propagation for standard Flow ports
        # If it's data, we don't color it pink. 
        # (Though user might want data wires in scope to be pink? Unlikely. Usually just flow.)
        is_flow = False
        if hasattr(port, 'port_class') and port.port_class == "flow": is_flow = True
        elif hasattr(port, 'data_type') and str(port.data_type) == str(DataType.FLOW): is_flow = True
        
        if not is_flow: return False

        # 2. Recursive Upstream Check
        node = port.parentItem() # The NodeWidget
        if not node: return False
        
        if visited is None: visited = set()
        if node in visited: return False # Cycle detected
        visited.add(node)
        
        # Check all INPUT Flow ports of this node
        # We need to find wires connected to imports that qualify.
        for input_port in node.inputs:
            # [CRITICAL UPDATE]
            # We must ignore the "Provider End" input (and Exit) because it represents the 
            # *end* of this provider's internal scope. Connecting back to it should not 
            # color the *output* Flow of this provider (unless the provider is itself nested).
            if input_port.name in ["Provider End", "Exit"]:
                continue

            # Is it a flow input?
            # Start strict: checking if input port type is flow or provider_flow
            # Actually, we just check the WIRES connected to it.
            
            for wire in input_port.wires:
                # If the wire originates from a Provider Flow, we are in scope.
                # Wire start_port is the source.
                if wire.start_port:
                    if self.check_provider_scope(wire.start_port, visited):
                        return True
                        
        return False

    def set_start_pos(self, pos):
        self.start_pos = pos
        self.update_path()

    def set_end_pos(self, pos):
        self.end_pos = pos
        self.update_path()

    def update_path(self):
        # Update positions from ports if they exist
        if self.start_port:
            self.start_pos = self.start_port.scenePos()
            self.update_style_from_port(self.start_port) # Update color if connected
            
        if self.end_port:
            self.end_pos = self.end_port.scenePos()
            if not self.start_port: # Only update from end if start is missing
                  self.update_style_from_port(self.end_port)

        self.pen.setColor(self.color)
        self.pen.setWidth(self.width) # [FIX] Ensure pen width is updated
        self.setPen(self.pen)

        path = QPainterPath()
        
        # Wire offset from port (creates a small horizontal line before the curve)
        # This makes wires visible even when behind connecting nodes
        WIRE_OFFSET = 20  # pixels
        
        # Calculate offset start and end points
        # Left side ports (inputs) offset left, right side ports (outputs) offset right
        start_offset = QPointF(self.start_pos.x() + WIRE_OFFSET, self.start_pos.y())
        end_offset = QPointF(self.end_pos.x() - WIRE_OFFSET, self.end_pos.y())
        
        # Draw straight line from port to offset point
        path.moveTo(self.start_pos)
        path.lineTo(start_offset)
        
        # Calculate Bezier Control Points
        dx = end_offset.x() - start_offset.x()
        
        # Simple curvature based on distance
        ctrl1 = QPointF(start_offset.x() + dx * 0.5, start_offset.y())
        ctrl2 = QPointF(end_offset.x() - dx * 0.5, end_offset.y())
        
        path.cubicTo(ctrl1, ctrl2, end_offset)
        
        # Draw straight line from offset point to port
        path.lineTo(self.end_pos)
        
        self.setPath(path)

    def hoverEnterEvent(self, event):
        self.pen.setWidth(self.width + 2)
        self.pen.setColor(QColor("#ff9900")) # Highlight Orange
        self.setPen(self.pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if getattr(self, "_menu_active", False):
            return
        self.pen.setWidth(self.width)
        self.pen.setColor(self.color)
        self.setPen(self.pen)
        super().hoverLeaveEvent(event)
        
    def contextMenuEvent(self, event):
        event.accept()
        self._menu_active = True
        
        # Force Highlight
        self.pen.setWidth(self.width + 2)
        self.pen.setColor(QColor("#ff9900"))
        self.setPen(self.pen)
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        delete_action = menu.addAction("Delete Wire")
        
        from PyQt6.QtGui import QCursor
        # Use QCursor.pos() for global position
        action = menu.exec(QCursor.pos())
        
        self._menu_active = False
        
        # Logic to decide if we should un-highlight
        if action == delete_action:
            self.delete_wire()
        else:
             self.pen.setWidth(self.width)
             self.pen.setColor(self.color)
             self.setPen(self.pen)
            
    def delete_wire(self):
        # Remove from ports
        if self.start_port and self in self.start_port.wires:
            self.start_port.wires.remove(self)
        if self.end_port and self in self.end_port.wires:
            self.end_port.wires.remove(self)
            
        # Remove from scene
        scene = self.scene()
        if scene:
            scene.removeItem(self)
            # Notify scene of modification
            if getattr(scene, "views", None) and scene.views():
                v = scene.views()[0]
                if hasattr(v, "modified"): v.modified.emit()

    def highlight_active(self):
        """Triggers the visual flow animation (Fade out over 1s)."""
        self._is_active = True
        self._active_start = QTime.currentTime().msecsSinceStartOfDay()
        self.update()

    def highlight_fade(self):
        """Alias for pulse animation."""
        self.highlight_active()

    def paint(self, painter, option, widget):
        ms = QTime.currentTime().msecsSinceStartOfDay()
        is_active = getattr(self, "_is_active", False)
        
        alpha = 0
        if is_active:
            start = getattr(self, "_active_start", 0)
            elapsed = ms - start
            
            # Duration 1000ms
            if elapsed < 1000:
                # Fade from 255 to 0
                factor = 1.0 - (elapsed / 1000.0)
                alpha = int(255 * factor)
            else:
                self._is_active = False
                alpha = 0
        
        # 1. Draw Base Wire (Pink Outline for Provider Flow)
        super().paint(painter, option, widget)
        
        # [PROVIDER FLOW SPECIAL] Draw Green Core
        # Check against our distinct provider color (#D11575)
        if self.color.name().upper() == "#D11575":
            # Save painter state
            painter.save()
            
            # Create Green Core Pen
            core_color = QColor("#2ECC71") # Vibrant Green (Flow)
            core_width = max(2, self.width - 4) # Thicker core (Width 8 -> Core 4)
            
            painter.setPen(QPen(core_color, core_width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path())
            
            painter.restore()

        # [ERROR FLOW SPECIAL] Draw Green Core
        # Check against our distinct error color (#8B0000)
        elif self.color.name().upper() == "#8B0000":
            # Save painter state
            painter.save()
            
            # Create Green Core Pen (Highlight on Green Wire)
            core_color = QColor("#2ECC71") # Vibrant Green (Flow)
            core_width = max(2, self.width - 4) 
            
            painter.setPen(QPen(core_color, core_width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path())
            
            painter.restore()

        # 2. Draw Overlay if active (Pulse)
        if alpha > 0:
            # [PROVIDER SPECIAL] Dual-Color Highlight
            if self.color.name().upper() == "#D11575":
                # 1. Outer Glow (Hot Pink)
                glow_pink = QColor("#FF69B4") # Hot Pink
                glow_pink.setAlpha(alpha)
                painter.setPen(QPen(glow_pink, self.width + 2))
                painter.drawPath(self.path())
                
                # 2. Inner Glow (Bright Green)
                glow_green = QColor("#00FF00") # Lime
                glow_green.setAlpha(alpha)
                core_width = max(2, self.width - 4)
                painter.setPen(QPen(glow_green, core_width))
                painter.drawPath(self.path())

            # [ERROR SPECIAL] Dual-Color Highlight
            elif self.color.name().upper() == "#8B0000":
                # 1. Outer Glow (Bright Red)
                glow_red = QColor("#FF0000") # Bright Red
                glow_red.setAlpha(alpha)
                painter.setPen(QPen(glow_red, self.width + 2))
                painter.drawPath(self.path())
                
                # 2. Inner Glow (Bright Green)
                glow_green = QColor("#00FF00") # Lime
                glow_green.setAlpha(alpha)
                core_width = max(2, self.width - 4)
                painter.setPen(QPen(glow_green, core_width))
                painter.drawPath(self.path())
                
            else:
                # Standard Pulse
                pulse_col = QColor(self.color)
                pulse_col.setAlpha(alpha)
                
                # If it's a flow wire (Dark Green base), use a more vibrant green for the pulse
                if self.color.name().lower() == "#006400": # Dark Green
                    pulse_col = QColor("#2ECC71") # Vibrant Green
                    pulse_col.setAlpha(alpha)
                    
                highlight_pen = QPen(pulse_col, self.width + 2)
                painter.setPen(highlight_pen)
                painter.drawPath(self.path())
            
            # Require next frame
            self.update()
