from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QLabel, QMenu, QGridLayout
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QColor, QPainter, QFont, QPen
import os

class MiniworldViewport(QWidget):
    """
    A single viewport slot in the Miniworld. 
    Can be assigned to a specific graph tab.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)
        
        # Minimap (Now takes full area)
        from synapse.gui.minimap import MinimapWidget
        self.minimap = MinimapWidget(self.main_window, parent=self)
        self.layout.addWidget(self.minimap)
        
        self.assigned_graph = None
        self.assigned_path = None
        self.is_disconnected = False
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_assignment_menu)

    def mouseDoubleClickEvent(self, event):
        """Double-click on a disconnected slot to reload the graph."""
        if self.is_disconnected and self.assigned_path:
            import os
            if os.path.exists(self.assigned_path):
                print(f"[Miniworld] Reloading offline graph: {self.assigned_path}")
                # Use main window's file opener
                if hasattr(self.main_window, 'file_ops') and hasattr(self.main_window.file_ops, 'open_file'):
                    graph = self.main_window.file_ops.open_file(self.assigned_path)
                    if graph:
                        self.assign_graph(graph)
                        return
            else:
                print(f"[Miniworld] File not found: {self.assigned_path}")
        super().mouseDoubleClickEvent(event)

    def assign_graph(self, graph):
        self.assigned_graph = graph
        self.assigned_path = graph.file_path if hasattr(graph, 'file_path') else None
        self.minimap.graph = graph
        self.is_disconnected = False
        self.update()

    def set_disconnected(self):
        self.is_disconnected = True
        self.assigned_graph = None
        self.minimap.graph = None
        self.update()

    def show_assignment_menu(self, pos: QPoint):
        menu = QMenu(self)
        
        tabs = self.main_window.central_tabs
        found_tabs = False
        for i in range(tabs.count()):
            graph = tabs.widget(i)
            from .graph_widget import GraphWidget
            if isinstance(graph, GraphWidget):
                found_tabs = True
                action = menu.addAction(tabs.tabText(i))
                action.triggered.connect(lambda checked, g=graph: self.assign_graph(g))
        
        if not found_tabs:
            menu.addAction("No tabs open").setEnabled(False)
            
        if self.assigned_graph or self.is_disconnected:
            menu.addSeparator()
            clear_act = menu.addAction("Clear Slot")
            clear_act.triggered.connect(self.clear_slot)

        menu.exec(self.mapToGlobal(pos))

    def clear_slot(self):
        self.assigned_graph = None
        self.assigned_path = None
        self.is_disconnected = False
        self.minimap.graph = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Handle Disconnected Overlay
        if self.is_disconnected:
            overlay_color = QColor(50, 0, 0, 150) # Reddish transparent
            painter.fillRect(self.rect(), overlay_color)
            
        # 2. Draw Tab Name Overlay (Top Center)
        name = "Right-click to assign"
        color = QColor(136, 136, 136) # Default gray
        
        if self.assigned_graph:
            # Check if graph is still open in any tab
            index = self.main_window.central_tabs.indexOf(self.assigned_graph)
            if index != -1:
                name = self.main_window.central_tabs.tabText(index)
                color = QColor("white")
            else:
                # Graph was closed, but we might want to keep the path to show it's 'Offline'
                if not self.is_disconnected:
                    self.set_disconnected()
                
        if self.is_disconnected:
            name = f"OFFLINE: {os.path.basename(self.assigned_path) if self.assigned_path else 'Unknown'}"
            color = QColor("#ff9999")

        # Draw Label background for legibility
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(name)
        text_height = metrics.height()
        
        bg_rect = QRectF((self.width() - text_width) / 2 - 10, 5, text_width + 20, text_height + 4)
        painter.setBrush(QColor(0, 0, 0, 160))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_rect, 5, 5)
        
        # Draw Text
        painter.setPen(QPen(color))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, name)

        # 3. Draw Filename Label (Bottom Right)
        path = self.assigned_path
        if self.assigned_graph and hasattr(self.assigned_graph, 'file_path'):
            path = self.assigned_graph.file_path

        if path:
            filename = os.path.basename(path)
            font_small = QFont("Segoe UI", 8)
            painter.setFont(font_small)
            metrics_small = painter.fontMetrics()
            tw = metrics_small.horizontalAdvance(filename)
            th = metrics_small.height()
            
            # Position at bottom right with some padding
            label_rect = QRectF(self.width() - tw - 10, self.height() - th - 10, tw + 6, th + 4)
            
            # Draw tiny background
            painter.setBrush(QColor(0, 0, 0, 120))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(label_rect, 3, 3)
            
            # Draw filename
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, filename)
            
    def update_map(self):
        if self.assigned_graph:
            if self.main_window.central_tabs.indexOf(self.assigned_graph) == -1:
                self.set_disconnected()
            else:
                self.minimap.update_minimap()
        elif self.is_disconnected:
            self.update()

class MiniworldWidget(QWidget):
    """
    Miniworld redesigned with 2 large left viewports and 4 small right viewports (2x2).
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        
        # 1. Main Splitter (3 Panels)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)
        
        self.slots = []
        
        # Panel 1: Large Slot
        slot1 = MiniworldViewport(self.main_window, parent=self)
        self.splitter.addWidget(slot1)
        self.slots.append(slot1)
        
        # Panel 2: Large Slot
        slot2 = MiniworldViewport(self.main_window, parent=self)
        self.splitter.addWidget(slot2)
        self.slots.append(slot2)
        
        # Panel 3: Grid of 4 Small Slots
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(2)
        
        for i in range(4):
            slot = MiniworldViewport(self.main_window, parent=self)
            self.grid_layout.addWidget(slot, i // 2, i % 2)
            self.slots.append(slot)
            
        self.splitter.addWidget(self.grid_container)
        
        # Set initial sizes for splitter: 1/4, 1/4, 2/4 (to give the grid its space)
        # Or better: [Big: 40%][Big: 40%][Grid: 20%]
        self.splitter.setStretchFactor(0, 2) 
        self.splitter.setStretchFactor(1, 2) 
        self.splitter.setStretchFactor(2, 1) 
            
    def refresh(self):
        for slot in self.slots:
            slot.update()

    def update_maps(self):
        for slot in self.slots:
            slot.update_map()

    def get_assignments(self):
        """Returns a list of file paths assigned to slots."""
        assignments = []
        for slot in self.slots:
            if slot.assigned_path:
                assignments.append(slot.assigned_path)
            else:
                assignments.append(None)
        return assignments

    def load_assignments(self, assignments, open_callback):
        """
        Restores assignments. 
        open_callback(path) should return the GraphWidget for that path (opening if needed).
        """
        if not assignments or not isinstance(assignments, list):
            return
            
        for i, path in enumerate(assignments):
            if i < len(self.slots) and path:
                graph = open_callback(path)
                if graph:
                    self.slots[i].assign_graph(graph)
                else:
                    # Mark as disconnected if file cannot be opened
                    self.slots[i].assigned_path = path
                    self.slots[i].set_disconnected()
