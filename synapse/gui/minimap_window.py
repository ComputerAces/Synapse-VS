from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from synapse.gui.minimap import MinimapWidget
from synapse.gui.graph_widget import GraphWidget

class StandaloneMinimapWindow(QMainWindow):
    def __init__(self, main_window):
        # Pass None to super to detach from main_window's minimize/close OS events
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Minimap - Active Graph")
        self.resize(300, 200)
        
        # Avoid closing the entire application when this window is closed
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        # Using Qt.WindowType.Window (default) ensures it gets a taskbar icon.
        # Because we passed `None` to super().__init__(), it is completely detached 
        # from the main window's minimize events naturally.
        self.setWindowFlags(Qt.WindowType.Window)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.minimap_widget = MinimapWidget(main_window, parent=self)
        layout.addWidget(self.minimap_widget)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # 1. Follow Active Graph
        follow_action = QAction("Follow Active Graph", self)
        follow_action.setCheckable(True)
        follow_action.setChecked(self.minimap_widget.graph is None)
        follow_action.triggered.connect(lambda: self.set_target_graph(None))
        menu.addAction(follow_action)
        menu.addSeparator()
        
        # 2. Open Graphs List
        if hasattr(self.main_window, "central_tabs"):
            for i in range(self.main_window.central_tabs.count()):
                tab_widget = self.main_window.central_tabs.widget(i)
                if isinstance(tab_widget, GraphWidget):
                    tab_text = self.main_window.central_tabs.tabText(i)
                    set_graph_action = QAction(f"Track: {tab_text}", self)
                    set_graph_action.setCheckable(True)
                    set_graph_action.setChecked(self.minimap_widget.graph == tab_widget)
                    set_graph_action.triggered.connect(lambda checked, t=tab_widget, name=tab_text: self.set_target_graph(t, name))
                    menu.addAction(set_graph_action)
                
        menu.addSeparator()
        
        # 3. Open New Minimap
        new_minimap_action = QAction("New Minimap Window...", self)
        new_minimap_action.triggered.connect(self.main_window.spawn_minimap_window)
        menu.addAction(new_minimap_action)
        
        menu.exec(event.globalPos())

    def set_target_graph(self, graph, name=None):
        self.minimap_widget.graph = graph
        if graph:
            self.setWindowTitle(f"Minimap - {name}")
        else:
            self.setWindowTitle("Minimap - Active Graph")
        self.minimap_widget.update_minimap()
