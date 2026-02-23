from PyQt6.QtWidgets import QListWidget, QMenu
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.library_parent = parent

    def on_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if not item: return
        
        menu = QMenu(self)
        sort_action = menu.addAction("Sort Alphabetically")
        remove_action = menu.addAction("Remove from Quick Links")
        action = menu.exec(self.mapToGlobal(pos))
        
        if action == sort_action and self.library_parent:
            self.library_parent.quick_links.sort(key=lambda x: x.get("label", ""))
            self.library_parent.save_quick_links()
            self.library_parent.populate_quick_links()
            
        elif action == remove_action and self.library_parent:
            data = item.data(Qt.ItemDataRole.UserRole)
            self.library_parent.remove_quick_link(data)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data: return
        
        label = data["label"]
        raw_payload = data["payload"]
        
        # Prepare Payloads
        if data["type"] == "subgraph":
            payload = f"subgraph:{raw_payload}"
        else:
            payload = label

        # Create MIME data that includes BOTH internal list data and our text payload
        # This ensures dragging to Canvas works (text) AND internal reorder works (model data)
        mime_data = self.model().mimeData(self.selectedIndexes())
        mime_data.setText(payload)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Visual
        pixmap = QPixmap(150, 30)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor("white"))
        painter.setBrush(QColor("#007acc"))
        painter.drawRoundedRect(0, 0, 140, 28, 5, 5)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, label)
        painter.end()
        
        drag.setPixmap(pixmap)
        
        # Allow both Copy and Move
        drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        """Handle internal reorder and sync to parent."""
        super().dropEvent(event)
        
        # Rebuild quick_links from current order
        if self.library_parent:
            new_order = []
            for i in range(self.count()):
                item = self.item(i)
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    new_order.append(data)
            self.library_parent.quick_links = new_order
            self.library_parent.save_quick_links()