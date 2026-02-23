from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF
from .node_widget.widget import NodeWidget
from .wire import Wire

class UndoCommandBase(QUndoCommand):
    def __init__(self, scene, description):
        super().__init__(description)
        self.scene = scene

class AddNodeCommand(UndoCommandBase):
    def __init__(self, scene, node_idx, pos, factory, node_widget=None):
        super().__init__(scene, f"Add {node_idx}")
        self.node_idx = node_idx
        self.pos = pos
        self.factory = factory
        self.node_widget = node_widget

    def redo(self):
        if not self.node_widget:
            # First run: create the node
            if self.node_idx.endswith(".syp"):
                self.node_widget = self.factory.create_subgraph_node(self.node_idx, self.pos)
            else:
                self.node_widget = self.factory.create_standard_node(self.node_idx, self.pos)
        else:
            # Re-add existing node
            self.scene.addItem(self.node_widget)
            
    def undo(self):
        if self.node_widget:
            # Just remove from scene, keep object alive
            self.scene.removeItem(self.node_widget)

class DeleteItemsCommand(UndoCommandBase):
    def __init__(self, scene, items):
        super().__init__(scene, "Delete Selection")
        self.items = items # List of (item, parent_state) tuples or just items
        self.connections = [] # Stores (start_port, end_port) for wires
        
        # Analyze items to determine structure
        self.nodes = []
        self.wires = []
        
        for item in items:
            if isinstance(item, NodeWidget):
                self.nodes.append(item)
                # Save connected wires that aren't selected explicitly
                for port in item.inputs + item.outputs:
                    for wire in port.wires:
                        if wire not in self.wires and wire not in items:
                            self.wires.append(wire)
            elif isinstance(item, Wire):
                if item not in self.wires:
                    self.wires.append(item)

    def redo(self):
        # Remove wires first
        for wire in self.wires:
            self.scene.removeItem(wire)
            if wire.start_port: 
                if wire in wire.start_port.wires: wire.start_port.wires.remove(wire)
            if wire.end_port:
                if wire in wire.end_port.wires: wire.end_port.wires.remove(wire)
                
        # Remove nodes
        for node in self.nodes:
            self.scene.removeItem(node)
            
    def undo(self):
        # Restore nodes
        for node in self.nodes:
            self.scene.addItem(node)
            
        # Restore wires
        for wire in self.wires:
            self.scene.addItem(wire)
            # Reconnect ports
            if wire.start_port: wire.start_port.wires.append(wire)
            if wire.end_port: wire.end_port.wires.append(wire)
            wire.update_path()

class MoveNodeCommand(UndoCommandBase):
    def __init__(self, scene, node_pos_map):
        super().__init__(scene, "Move Nodes")
        self.node_pos_map = node_pos_map # {node: (old_pos, new_pos)}
        
    def redo(self):
        for node, (old, new) in self.node_pos_map.items():
            node.setPos(new)
            node.update_connected_wires()
            
    def undo(self):
        for node, (old, new) in self.node_pos_map.items():
            node.setPos(old)
            node.update_connected_wires()

class ConnectWireCommand(UndoCommandBase):
    def __init__(self, scene, start_port, end_port, existing_wire=None):
        super().__init__(scene, "Connect Wire")
        self.start_port = start_port
        self.end_port = end_port
        self.wire = existing_wire
        
    def redo(self):
        if not self.wire:
            self.wire = Wire(self.start_port, self.end_port)
        
        if self.wire not in self.scene.items():
            self.scene.addItem(self.wire)
            
        if self.wire not in self.start_port.wires: self.start_port.wires.append(self.wire)
        if self.wire not in self.end_port.wires: self.end_port.wires.append(self.wire)
        
        self.wire.update_path()
        
    def undo(self):
        self.scene.removeItem(self.wire)
        if self.wire in self.start_port.wires: self.start_port.wires.remove(self.wire)
        if self.wire in self.end_port.wires: self.end_port.wires.remove(self.wire)
