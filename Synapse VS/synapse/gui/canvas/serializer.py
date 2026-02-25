import json
import os
from PyQt6.QtCore import QPointF
from synapse.gui.node_widget.widget import NodeWidget
from synapse.gui.wire import Wire
from synapse.gui.frame_widget import FrameWidget
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import copy
import re

# Properties that are always allowed (system metadata)
SYSTEM_PROPERTIES = {
    "label", "provider flow id", "provider_flow_id", "singleton scope", "singleton_scope", "singletonscope", 
    "graph_path", "Graph Path", "GraphPath", "embedded data", "embedded_data", "embeddeddata", "Embedded Data", "EmbeddedData", "is_debug", "header_color",
    "additional_inputs", "additional_outputs", "additional inputs", "additional outputs", "Additional Inputs", "Additional Outputs", "cases"
}

class GraphSerializer:
    def __init__(self, scene, view, factory):
        self.scene = scene
        self.view = view
        self.factory = factory

    def serialize(self):
        nodes = []
        wires = []
        frames = []
        
        for item in self.scene.items():
            if isinstance(item, NodeWidget) and hasattr(item, 'node') and item.node:
                n_type = getattr(item, 'node_type', item.node.name)
                node_data = {
                    "id": item.node.node_id,
                    "type": n_type, 
                    "name": item.node.name,
                    "pos_x": item.scenePos().x(),
                    "pos_y": item.scenePos().y(),
                    "properties": item.node.properties
                }
                nodes.append(node_data)
                
        for item in self.scene.items():
            if isinstance(item, Wire) and item.start_port and item.end_port:
                start_node = item.start_port.parent_node
                end_node = item.end_port.parent_node
                if hasattr(start_node, 'node') and start_node.node and hasattr(end_node, 'node') and end_node.node:
                    wire_data = {
                        "from_node": start_node.node.node_id,
                        "from_port": item.start_port.name,
                        "to_node": end_node.node.node_id,
                        "to_port": item.end_port.name
                    }
                    wires.append(wire_data)
        
        for item in self.scene.items():
            if isinstance(item, FrameWidget):
                frames.append(item.serialize())
        
        center = self.view.mapToScene(self.view.rect().center())
        viewport = {
            "center_x": center.x(),
            "center_y": center.y(),
            "zoom": self.view.transform().m11()
        }
        
        embedded_subgraphs = {}
        self._collect_embedded_subgraphs(nodes, embedded_subgraphs, set())
                    
        return {"nodes": nodes, "wires": wires, "frames": frames, "viewport": viewport, "embedded_subgraphs": embedded_subgraphs}

    def serialize_selection(self):
        selection = self.scene.selectedItems()
        nodes = []
        wires = []
        frames = []
        
        # 1. Collect selected nodes and frames
        selected_node_ids = set()
        
        # Pass 1: Nodes explicitly selected
        for item in selection:
            if isinstance(item, NodeWidget) and hasattr(item, 'node') and item.node:
                n_type = getattr(item, 'node_type', item.node.name)
                nodes.append({
                    "id": item.node.node_id,
                    "type": n_type, 
                    "name": item.node.name,
                    "pos_x": item.scenePos().x(),
                    "pos_y": item.scenePos().y(),
                    "properties": copy.deepcopy(item.node.properties) # Deep copy
                })
                selected_node_ids.add(item.node.node_id)
            elif isinstance(item, FrameWidget):
                frames.append(item.serialize())
                
        # Pass 2: Ensure children of selected frames are also serialized
        for item in selection:
            if isinstance(item, FrameWidget):
                for node in item.child_nodes:
                    if hasattr(node, 'node') and node.node and node.node.node_id not in selected_node_ids:
                        n_type = getattr(node, 'node_type', node.node.name)
                        nodes.append({
                            "id": node.node.node_id,
                            "type": n_type, 
                            "name": node.node.name,
                            "pos_x": node.scenePos().x(),
                            "pos_y": node.scenePos().y(),
                            "properties": copy.deepcopy(node.node.properties)
                        })
                        selected_node_ids.add(node.node.node_id)

        # 3. Collect ALL wires connected to selected nodes (Internal and External)
        for item in self.scene.items():
            if isinstance(item, Wire) and item.start_port and item.end_port:
                start_node = item.start_port.parent_node
                end_node = item.end_port.parent_node
                if hasattr(start_node, 'node') and hasattr(end_node, 'node'):
                    s_id = start_node.node.node_id
                    e_id = end_node.node.node_id
                    # If AT LEAST ONE side is in selection, we keep the wire
                    if s_id in selected_node_ids or e_id in selected_node_ids:
                        wires.append({
                            "from_node": s_id,
                            "from_port": item.start_port.name,
                            "to_node": e_id,
                            "to_port": item.end_port.name
                        })

        return {"nodes": nodes, "wires": wires, "frames": frames}
    
    def _collect_embedded_subgraphs(self, nodes, embedded, visited):
        for node_data in nodes:
            props = node_data.get("properties", {})
            graph_path = props.get("graph_path", "")
            if graph_path and graph_path not in visited:
                visited.add(graph_path)
                if os.path.exists(graph_path):
                    try:
                        with open(graph_path, 'r') as f: subgraph_data = json.load(f)
                        embedded[graph_path] = subgraph_data
                        if "nodes" in subgraph_data:
                            self._collect_embedded_subgraphs(subgraph_data["nodes"], embedded, visited)
                    except: pass

    def deserialize(self, data):
        self.scene.clear()
        node_map = {}
        was_pruned = False
        
        if "nodes" in data:
            for n_data in data["nodes"]:
                node_type = n_data["type"]
                node_id = n_data["id"]
                node_name = n_data.get("name", node_type)
                pos = QPointF(n_data.get("pos_x", 0), n_data.get("pos_y", 0))
                
                widget = NodeWidget(node_type)
                widget.setPos(pos)
                
                node_class = NodeRegistry.get_node_class(node_type)
                
                # [FALLBACK] If type not found, but has graph_path, treat as SubGraph
                if not node_class and "properties" in n_data and ("Graph Path" in n_data["properties"] or "graph_path" in n_data["properties"]):
                    node_class = NodeRegistry.get_node_class("SubGraph Node")
                    if node_class:
                         print(f"[{node_name}] Type '{node_type}' not found. Falling back to SubGraph Node.")

                if node_class:
                    try:
                        logic = node_class(node_id, node_name, None)
                        if "properties" in n_data:
                            # [PRUNING] Load properties strictly (shared logic with loader.py)
                            loaded_props = n_data["properties"]
                            
                            # Determine allowed dynamic property keys (case-insensitive)
                            allowed_dynamic = set()
                            for k, v in loaded_props.items():
                                kl = k.lower().replace("_", " ")
                                if kl in ["additional inputs", "additional_inputs", "additionalinputs"]: 
                                    if isinstance(v, list):
                                        allowed_dynamic.update(name.lower() for name in v)
                                elif kl in ["additional outputs", "additional_outputs", "additionaloutputs"]:
                                    if isinstance(v, list):
                                        allowed_dynamic.update(name.lower() for name in v)
                                elif kl == "cases":
                                    if isinstance(v, list):
                                        allowed_dynamic.update(name.lower() for name in v)
                                
                            # We use a list of keys to safely iterate while deleting from the dict
                            DYNAMIC_PATTERNS = [
                                r"item \d+", r"case \d+", r"image [a-z]", r"last image", r"user present", 
                                r"var \d+", r"port \d+", r"input \d+", r"output \d+", r"camera index",
                                r"var.*", r"arg.*", r"param.*", r"last .* image", r"curr.* image", r"prev.* image"
                            ]

                            for k in list(loaded_props.keys()):
                                v = loaded_props[k]
                                k_lower = k.lower()
                                k_normalized = k_lower.replace("_", " ")
                                
                                # 1. Direct match with initialized properties
                                if k in logic.properties:
                                    logic.properties[k] = v
                                    continue
                                
                                # 2. System properties / Metadata
                                if k_lower in SYSTEM_PROPERTIES or k_normalized in SYSTEM_PROPERTIES:
                                    logic.properties[k] = v
                                    continue
                                
                                # 3. Dynamic Port properties (Start/Return/Calculated)
                                if k_lower in allowed_dynamic or k_normalized in allowed_dynamic:
                                    logic.properties[k] = v
                                    continue
                                
                                # 4. Case-Insensitive port match (against input_types/output_types)
                                matched = False
                                for port_map_name in ["input_types", "output_types"]:
                                    port_map = getattr(logic, port_map_name, {})
                                    for port_name in port_map:
                                        if k_lower == port_name.lower() or k_normalized == port_name.lower().replace("_", " "):
                                            logic.properties[k] = v
                                            matched = True
                                            break
                                    if matched: break
                                
                                # 5. [PROTECTION] Dynamic Port Pattern Match (for nodes that allow dynamic expansion)
                                if not matched and (getattr(logic, "allow_dynamic_inputs", False) or getattr(logic, "allow_dynamic_outputs", False)):
                                    for pattern in DYNAMIC_PATTERNS:
                                        if re.fullmatch(pattern, k_normalized):
                                            # It looks like a dynamic port, keep it even if not in the additional_inputs list
                                            logic.properties[k] = v
                                            matched = True
                                            break

                                if not matched:
                                    print(f"[GUI Repair] [{node_name}] Removed dead property '{k}'")
                                    loaded_props.pop(k) # Remove from JSON data
                                    was_pruned = True

                            # [MIGRATION] Legacy Write Mode Conversion
                            if node_type in ["Write File", "Write Mode Enum"]:
                                if "mode" in logic.properties:
                                    val = logic.properties["mode"]
                                    if val == "w": logic.properties["mode"] = "Overwrite"
                                    elif val == "a": logic.properties["mode"] = "Append"
                                if "value" in logic.properties:
                                    val = logic.properties["value"]
                                    if val == "w": logic.properties["value"] = "Overwrite"
                                    elif val == "a": logic.properties["value"] = "Append"

                        widget.node = logic
                        widget.name = node_name
                        widget.update_title()
                        
                        # SubGraph Repair Logic
                        has_graph_path = "Graph Path" in logic.properties or "graph_path" in logic.properties or getattr(node_class, "graph_path", None)
                        is_subgraph = widget.name.startswith("SubGraph") or widget.name == node_type or node_type == "SubGraph Node"
                        if is_subgraph and has_graph_path:
                             try:
                                 path = logic.properties.get("Graph Path") or logic.properties.get("graph_path") or getattr(node_class, "graph_path", "")
                                 abs_path = os.path.abspath(path) if os.path.exists(path) else path
                                 name = None
                                 if os.path.exists(abs_path):
                                      with open(abs_path, 'r') as f:
                                          name = json.load(f).get("project_name", "").strip()
                                 if not name: name = os.path.splitext(os.path.basename(path))[0]
                                 widget.set_user_name(name)
                                 
                                 widget.update_subgraph_status(os.path.exists(abs_path))
                                 
                                 # [FIX] Force a port rebuild and property cleanup on load
                                 if hasattr(logic, 'rebuild_ports'):
                                     logic.rebuild_ports()
                             except: pass
                    except: pass
                
                self.factory.configure_node_ports(widget, node_type, node_instance=widget.node)
                
                if widget.node:
                     # Check both Title Case and legacy lowercase for dynamic ports
                     dyn_outputs = widget.node.properties.get("Additional Outputs") or widget.node.properties.get("additional_outputs", [])
                     for p_name in dyn_outputs:
                         if p_name not in [p.name for p in widget.ports]: widget.add_output(p_name, port_class="data")
                     dyn_inputs = widget.node.properties.get("Additional Inputs") or widget.node.properties.get("additional_inputs", [])
                     for p_name in dyn_inputs:
                         if p_name not in [p.name for p in widget.ports]: widget.add_input(p_name, port_class="data")
                     for p_name in widget.node.properties.get("Cases") or widget.node.properties.get("cases", []):
                         if p_name not in [p.name for p in widget.ports]: widget.add_output(p_name, port_class="flow")
                         
                widget.update_layout()
                self.scene.addItem(widget)
                node_map[node_id] = widget

        if "wires" in data:
            for w_data in data["wires"]:
                from_id = w_data["from_node"]; to_id = w_data["to_node"]
                start_widget = node_map.get(from_id); end_widget = node_map.get(to_id)
                if start_widget and end_widget:
                    if not start_widget.get_output(w_data["from_port"]):
                        # Robust Flow Detection on name during recovery
                        p_name = w_data["from_port"]
                        p_cls = "flow" if p_name.lower() in ["flow", "exec", "out", "then", "else"] else "data"
                        d_type = DataType.FLOW if p_cls == "flow" else DataType.ANY
                        start_widget.add_output(p_name, port_class=p_cls, data_type=d_type)
                        
                    if not end_widget.get_input(w_data["to_port"]):
                        p_name = w_data["to_port"]
                        p_cls = "flow" if p_name.lower() in ["flow", "exec", "in", "trigger"] else "data"
                        d_type = DataType.FLOW if p_cls == "flow" else DataType.ANY
                        end_widget.add_input(p_name, port_class=p_cls, data_type=d_type)
                        
                    start_port = start_widget.get_output(w_data["from_port"])
                    end_port = end_widget.get_input(w_data["to_port"])
                    
                    if start_port and end_port:
                        wire = Wire(start_port); wire.end_port = end_port
                        if wire not in start_port.wires: start_port.wires.append(wire)
                        if wire not in end_port.wires: end_port.wires.append(wire)
                        self.scene.addItem(wire); wire.update_style_from_port(start_port); wire.update_path()

        if "frames" in data:
            for frame_data in data["frames"]:
                frame = FrameWidget.deserialize(frame_data, node_map)
                if frame: self.scene.addItem(frame)

        if "viewport" in data:
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            vp = data["viewport"]
            self.view.resetTransform()
            zoom = vp.get("zoom", 1.0)
            self.view.scale(zoom, zoom)
            self.view.centerOn(vp.get("center_x", 0), vp.get("center_y", 0))
            
        return was_pruned

    def deserialize_selection(self, data, offset=QPointF(30, 30)):
        import uuid
        old_to_new = {}
        node_map = {}
        new_items = []
        
        # 1. Clear Selection (User likely wants to select the NEWLY pasted items)
        self.scene.clearSelection()

        # 2. Create Nodes with NEW IDs
        if "nodes" in data:
            for n_data in data["nodes"]:
                node_type = n_data["type"]
                old_id = n_data["id"]
                new_id = str(uuid.uuid4())
                old_to_new[old_id] = new_id
                
                node_name = n_data.get("name", node_type)
                pos = QPointF(n_data.get("pos_x", 0), n_data.get("pos_y", 0)) + offset
                
                widget = NodeWidget(node_type)
                widget.setPos(pos)
                
                node_class = NodeRegistry.get_node_class(node_type)
                
                # [FALLBACK]
                if not node_class and "properties" in n_data and ("Graph Path" in n_data["properties"] or "graph_path" in n_data["properties"]):
                    node_class = NodeRegistry.get_node_class("SubGraph Node")

                if node_class:
                    try:
                        logic = node_class(new_id, node_name, None)
                        if "properties" in n_data: 
                            logic.properties = copy.deepcopy(n_data["properties"])
                        widget.node = logic
                        widget.name = node_name
                        widget.update_title()
                        
                        if hasattr(logic, 'rebuild_ports'):
                            logic.rebuild_ports()
                    except: pass
                
                self.factory.configure_node_ports(widget, node_type, node_instance=widget.node)
                
                # Restore dynamic ports if present in properties
                if widget.node:
                     dyn_outputs = widget.node.properties.get("Additional Outputs") or widget.node.properties.get("additional_outputs", [])
                     for p_name in dyn_outputs:
                         if p_name not in [p.name for p in widget.ports]: widget.add_output(p_name, port_class="data")
                     dyn_inputs = widget.node.properties.get("Additional Inputs") or widget.node.properties.get("additional_inputs", [])
                     for p_name in dyn_inputs:
                         if p_name not in [p.name for p in widget.ports]: widget.add_input(p_name, port_class="data")
                     for p_name in widget.node.properties.get("Cases") or widget.node.properties.get("cases", []):
                         if p_name not in [p.name for p in widget.ports]: widget.add_output(p_name, port_class="flow")

                widget.update_layout()
                self.scene.addItem(widget)
                widget.setSelected(True) # Select pasted item
                node_map[new_id] = widget
                new_items.append(widget)

        # 3. Restore Wires (Relink to NEW or EXISTING nodes)
        if "wires" in data:
            # Helper to find a widget in the scene by its node ID
            def find_in_scene(node_id):
                for item in self.scene.items():
                    if isinstance(item, NodeWidget) and hasattr(item, 'node') and item.node:
                        if item.node.node_id == node_id:
                            return item
                return None

            for w_data in data["wires"]:
                old_from = w_data["from_node"]
                old_to = w_data["to_node"]
                
                # Check if endpoints are new or external
                start_widget = node_map.get(old_to_new.get(old_from)) or find_in_scene(old_from)
                end_widget = node_map.get(old_to_new.get(old_to)) or find_in_scene(old_to)
                
                if start_widget and end_widget:
                    start_port = start_widget.get_output(w_data["from_port"])
                    end_port = end_widget.get_input(w_data["to_port"])
                    
                    if start_port and end_port:
                        wire = Wire(start_port); wire.end_port = end_port
                        if wire not in start_port.wires: start_port.wires.append(wire)
                        if wire not in end_port.wires: end_port.wires.append(wire)
                        self.scene.addItem(wire); wire.update_style_from_port(start_port); wire.update_path()

        # 4. Frames
        if "frames" in data:
            for frame_data in data["frames"]:
                # Remap node IDs in frame's internal list
                if "node_ids" in frame_data:
                    frame_data["node_ids"] = [old_to_new.get(oid) for oid in frame_data["node_ids"] if oid in old_to_new]
                
                # Deserialize frame (it expects a node_map containing the NEW widgets)
                frame = FrameWidget.deserialize(frame_data, node_map)
                if frame:
                    pos = QPointF(frame_data.get("pos_x", 0), frame_data.get("pos_y", 0)) + offset
                    frame.setPos(pos)
                    self.scene.addItem(frame)
                    frame.setSelected(True)
                    new_items.append(frame)

        # 5. Viewport-Aware Correction
        if new_items and self.view:
            from PyQt6.QtCore import QRectF
            # Calculate bounding box of all newly pasted items
            pasted_rect = QRectF()
            for item in new_items:
                if pasted_rect.isNull():
                    pasted_rect = item.sceneBoundingRect()
                else:
                    pasted_rect = pasted_rect.united(item.sceneBoundingRect())

            # Get current visible area in scene coordinates
            viewport_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
            
            # Check if any part of the pasted group is visible
            if not viewport_rect.intersects(pasted_rect):
                # If entirely off-screen, shift the group to the center of the viewport
                shift_x = viewport_rect.center().x() - pasted_rect.center().x()
                shift_y = viewport_rect.center().y() - pasted_rect.center().y()
                
                for item in new_items:
                    item.moveBy(shift_x, shift_y)
                
                # Also move wires (they don't moveBy with nodes automatically if not children)
                for item in self.scene.items():
                    if isinstance(item, Wire):
                        item.update_path()
