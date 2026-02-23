from PyQt6.QtWidgets import QTreeWidget, QMenu
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor

class DraggableTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setHeaderLabel("Nodes")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.library_parent = parent # Reference to NodeLibrary

    def on_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if not item: return
        if item.childCount() > 0: return # Only leaves
        
        menu = QMenu(self)
        
        # Check Favorites
        path = item.data(0, Qt.ItemDataRole.UserRole)
        is_favorite = False
        if path and self.library_parent:
             is_favorite = self.library_parent.is_favorite(path)
             
        remove_fav = None
        if is_favorite:
            remove_fav = menu.addAction("Remove from Favorites")
            
        # Add to Quick Links (Always available for leaves)
        add_quick = menu.addAction("Add to Quick Links")
            
        action = menu.exec(self.mapToGlobal(pos))
        
        if not self.library_parent: return
            
        if remove_fav and action == remove_fav:
            if path:
                self.library_parent.remove_favorite(path)
        
        if action == add_quick:
            data = {
                "label": item.text(0),
                "type": "standard", 
                "payload": path if path else item.text(0)
            }
            # Refine type logic
            if path:
                if str(path).startswith("SNIPPET:"):
                     data["type"] = "snippet"
                else:
                     data["type"] = "subgraph"
            else:
                data["type"] = "standard"
                
            self.library_parent.add_quick_link(data)
                    
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return
            
        # Only allow dragging leaves
        if item.childCount() > 0: return

        # Determine Payload
        user_data = item.data(0, Qt.ItemDataRole.UserRole)
        label = item.text(0)
        
        if user_data:
            if str(user_data).startswith("SNIPPET:"):
                payload = user_data # Already prefixed
            else:
                payload = f"subgraph:{user_data}"
        else:
            payload = label
            
        mime_data = QMimeData()
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
        drag.exec(Qt.DropAction.CopyAction)