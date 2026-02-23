from PyQt6.QtWidgets import QMenu, QInputDialog, QMessageBox, QApplication
from PyQt6.QtCore import QPointF

import copy

class NodeActionsMixin:
    """
    Handles User Interaction, Context Menus, and logical actions (Delete, Duplicate, Sync).
    """
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        # Safe selection check
        selected_items = []
        if self.scene():
            selected_items = [i for i in self.scene().selectedItems() if hasattr(i, 'node_type')]
            
        group_action = None
        ungroup_action = None
        open_graph = None
        
        if len(selected_items) > 1:
            group_action = menu.addAction("Group Nodes")
            
        if hasattr(self, 'parent_frame') and self.parent_frame:
            ungroup_action = menu.addAction("Remove from Group")
            
        if group_action or ungroup_action:
            menu.addSeparator()
        
        # Dynamic Port Actions
        if "Switch" in self.node_type:
            add_case = menu.addAction("Add Case (Output)")
            remove_case = menu.addAction("Remove Case")
        elif "Sender" in self.node_type:
            add_input = menu.addAction("Add Data Input")
            remove_input = menu.addAction("Remove Input")
        elif "Receiver" in self.node_type:
            add_output = menu.addAction("Add Data Output")
            remove_output = menu.addAction("Remove Output")
        elif "Start" in self.node_type:
            self.add_out_action = menu.addAction("Add Output")
            self.rem_out_action = menu.addAction("Remove Output")
        elif "Return" in self.node_type:
            self.add_in_action = menu.addAction("Add Input")
            self.rem_in_action = menu.addAction("Remove Input")
        elif "Python Script" in self.node_type:
            self.add_py_in = menu.addAction("Add Input Pin")
            self.rem_py_in = menu.addAction("Remove Input Pin")
            self.add_py_out = menu.addAction("Add Output Pin")
            self.rem_py_out = menu.addAction("Remove Output Pin")
        elif "Template Injector" in self.node_type:
            self.add_tmpl_in = menu.addAction("Add New Input")
            self.rem_tmpl_in = menu.addAction("Remove Input")
        elif self.node_type in ("List", "List Node", "AND", "OR", "XOR", "NAND", "NOR", "XNOR"):
            self.add_list_in = menu.addAction("Add Item Input")
            self.rem_list_in = menu.addAction("Remove Item Input")
        if self.node and "graph_path" in self.node.properties:
             open_graph = menu.addAction("Open In New Tab")
        elif self.node_type == "Subtract Image":
            self.add_img_in = menu.addAction("Add Image Input")
            self.rem_img_in = menu.addAction("Remove Image Input")
        
        # [SuperNode Integration]
        # Check if this node type inherits from SuperNode
        from synapse.nodes.registry import NodeRegistry
        from synapse.core.super_node import SuperNode
        
        # Safe lookup
        is_super = False
        try:
            cls_def = NodeRegistry.get_node_class(self.node_type)
            if cls_def and issubclass(cls_def, SuperNode):
                is_super = True
        except: pass
        
        # if is_super:
        #     menu.addSeparator()
        #     self.sn_add_in = menu.addAction("Add Input (Super)")
        #     self.sn_rem_in = menu.addAction("Remove Input")
        #     self.sn_add_out = menu.addAction("Add Output (Super)")
        #     self.sn_rem_out = menu.addAction("Remove Output")
        
        # favorites Logic (Canvas-based)
        if self.node and "graph_path" in self.node.properties:
            menu.addSeparator()
            is_fav = self._is_node_favorite()
            fav_action = menu.addAction("Remove from Favorites" if is_fav else "Add to Favorites")
        else:
            fav_action = None
            
        menu.addSeparator()
        
        duplicate_action = menu.addAction("Duplicate Node(s)")
        delete_action = menu.addAction("Delete Node")
        
        action = menu.exec(event.screenPos())
        
        if action == group_action and group_action:
            self._create_frame_for_nodes(selected_items)
            return
        if action == ungroup_action and ungroup_action:
            if hasattr(self, 'parent_frame') and self.parent_frame:
                self.parent_frame.remove_node(self)
            return
        
        if action == delete_action:
            # If multiple selected, use the CanvasView.delete_selection (which has the prompt)
            scene = self.scene()
            if scene and scene.views():
                selected = scene.selectedItems()
                if len(selected) > 1:
                    canvas = scene.views()[0]
                    if hasattr(canvas, 'delete_selection'):
                        canvas.delete_selection()
                        return

            self.delete_node()
            self._mark_modified()
        elif action == duplicate_action:
            # Duplicate all selected nodes
            scene = self.scene()
            if scene:
                from synapse.gui.node_widget.widget import NodeWidget
                to_dup = [item for item in scene.selectedItems() if isinstance(item, NodeWidget)]
                if len(to_dup) <= 1:
                    to_dup = [self]
                for node_widget in to_dup:
                    node_widget.duplicate_node()
            self._mark_modified()

        elif fav_action and action == fav_action:
            self._toggle_favorite()
            self._mark_modified()
        elif open_graph and action == open_graph:
             path = self.node.properties["graph_path"]
             if path:
                 win = QApplication.activeWindow()
                 if hasattr(win, 'open_tab'): win.open_tab(path)

        # Specific Node Logic
        elif "Switch" in self.node_type:
            if action == add_case:
                # Ask for Name (port label)
                name, ok = QInputDialog.getText(None, "Add Case", "Output Name:")
                if ok and name and name not in [p.name for p in self.ports]:
                    # Ask for Value (match target)
                    value, ok2 = QInputDialog.getText(None, "Add Case", f"Match Value for '{name}':")
                    if ok2:
                        value = value.strip() if value else name
                        self.add_output(name)
                        # Store as {name, value} dict
                        if self.node:
                            cases = self.node.properties.get("cases", [])
                            cases.append({"name": name, "value": value})
                            self.node.properties["cases"] = cases
                        self._mark_modified()
            elif action == remove_case:
                # Show cases with their values for clarity
                case_items = []
                if self.node:
                    cases = self.node.properties.get("cases", [])
                    for c in cases:
                        if isinstance(c, dict):
                            case_items.append(f"{c['name']} (={c['value']})")
                        else:
                            case_items.append(c)
                if not case_items:
                    case_items = [p.name for p in self.outputs if p.name != "Default"]
                if case_items:
                    chosen, ok = QInputDialog.getItem(None, "Remove Case", "Select:", case_items, 0, False)
                    if ok and chosen:
                        # Extract the name part
                        case_name = chosen.split(" (=")[0] if " (=" in chosen else chosen
                        self.remove_port(case_name)
                        if self.node:
                            cases = self.node.properties.get("cases", [])
                            self.node.properties["cases"] = [
                                c for c in cases
                                if (isinstance(c, dict) and c.get("name") != case_name)
                                or (isinstance(c, str) and c != case_name)
                            ]
                        self._mark_modified()

        elif "Sender" in self.node_type:
            if action == add_input:
                self._add_port_dialog("Add Input", self.add_input)
            elif action == remove_input:
                self._remove_port_dialog([p.name for p in self.inputs if p.name != "Flow"])

        elif "Receiver" in self.node_type:
            if action == add_output:
                self._add_port_dialog("Add Output", self.add_output)
            elif action == remove_output:
                self._remove_port_dialog([p.name for p in self.outputs if p.name != "Flow"])

        elif "Start" in self.node_type:
            if action == self.add_out_action:
                self._add_port_dialog("Add Output", self.add_output, "additional_outputs", type_prop="output_types")
            elif action == self.rem_out_action:
                self._remove_port_dialog([p.name for p in self.outputs if p.name != "Flow"], "additional_outputs")

        elif "Return" in self.node_type:
            if action == self.add_in_action:
                self._add_port_dialog("Add Input", self.add_input, "additional_inputs")
            elif action == self.rem_in_action:
                self._remove_port_dialog([p.name for p in self.inputs if p.name != "Flow"], "additional_inputs")

        elif "Python Script" in self.node_type:
            if action == self.add_py_in:
                self._add_port_dialog("Add Input", self.add_input, "additional_inputs", sync_py=True)
            elif action == self.rem_py_in:
                self._remove_port_dialog([p.name for p in self.inputs if p.name != "Flow"], "additional_inputs", sync_py=True)
            elif action == self.add_py_out:
                self._add_port_dialog("Add Output", self.add_output, "additional_outputs", sync_py=True)
            elif action == self.rem_py_out:
                self._remove_port_dialog([p.name for p in self.outputs if p.name not in ["Flow", "Finished Flow"]], "additional_outputs", sync_py=True)

        elif "Template Injector" in self.node_type:
            if action == self.add_tmpl_in:
                self._add_port_dialog("Add New Input", self.add_input, "additional_inputs")
            elif action == self.rem_tmpl_in:
                self._remove_port_dialog(
                    [p.name for p in self.inputs if p.name not in ["Flow", "Template"]],
                    "additional_inputs"
                )

        elif self.node_type in ("List", "List Node", "AND", "OR", "XOR", "NAND", "NOR", "XNOR"):
            if action == self.add_list_in:
                # Auto-name: find next Item N index
                existing = [p.name for p in self.inputs if p.name.startswith("Item ")]
                next_idx = len(existing)
                new_name = f"Item {next_idx}"
                
                # Logic gates use BOOLEAN, List Node uses ANY
                is_logic = self.node_type in ("AND", "OR", "XOR", "NAND", "NOR", "XNOR")
                from synapse.core.types import DataType
                d_type = DataType.BOOLEAN if is_logic else DataType.ANY
                
                self.add_input(new_name, data_type=d_type)
                if self.node:
                    extras = self.node.properties.get("additional_inputs", [])
                    if new_name not in extras:
                        extras.append(new_name)
                    self.node.properties["additional_inputs"] = extras
                self._mark_modified()
            elif action == self.rem_list_in:
                removable = [p.name for p in self.inputs if p.name.startswith("Item ")]
                # Enforcement: Min 2 items for logic gates (optional per user request but implies "min 2 items" in prompt)
                is_logic = self.node_type in ("AND", "OR", "XOR", "NAND", "NOR", "XNOR")
                if is_logic and len(removable) <= 2:
                    QMessageBox.information(None, "Restriction", "Logic gates require at least 2 inputs.")
                    return
                if removable:
                    self._remove_port_dialog(removable, "additional_inputs")

        elif self.node and "graph_path" in self.node.properties:
             if action == open_graph:
                 path = self.node.properties["graph_path"]
                 if path:
                     win = QApplication.activeWindow()
                     if hasattr(win, 'open_tab'): win.open_tab(path)

        elif self.node_type == "Subtract Image":
            if action == self.add_img_in:
                # find next letter
                existing = [p.name for p in self.inputs if p.name.startswith("Image ")]
                
                max_ord = 66 # Default start at B (so next is C)
                
                for name in existing:
                    try:
                        suffix = name.split(" ")[1]
                        if len(suffix) == 1 and suffix.isalpha():
                            o = ord(suffix.upper())
                            if o > max_ord: max_ord = o
                    except: pass
                
                next_char = chr(max_ord + 1)
                new_name = f"Image {next_char}"
                
                from synapse.core.types import DataType
                self.add_input(new_name, data_type=DataType.IMAGE)
                self._update_list_prop("additional_inputs", new_name, add=True)
                self._mark_modified()

            elif action == self.rem_img_in:
                removable = [p.name for p in self.inputs if p.name.startswith("Image ")]
                # Keep at least Image 1 and Image 2
                if len(removable) <= 2:
                    QMessageBox.information(None, "Restriction", "Subtract Image requires at least 2 inputs.")
                    return
                
                # Sort by index descending to remove highest first by default or let user pick
                # Let's let user pick but pre-select last
                self._remove_port_dialog(removable, "additional_inputs")

        # [SuperNode Handlers]
        if hasattr(self, 'sn_add_in') and action == self.sn_add_in:
             self._add_port_dialog("Add Input", self.add_input, type_prop="custom_input_schema")
             
        elif hasattr(self, 'sn_rem_in') and action == self.sn_rem_in:
            # Filter standard ports if needed, but SuperNode allows removing custom ones
            # For now, list all non-default? Or just list all inputs.
            # Best to list keys in 'custom_input_schema'
            custom = self.node.properties.get("custom_input_schema", {})
            self._remove_port_dialog(list(custom.keys()), type_prop="custom_input_schema")

        elif hasattr(self, 'sn_add_out') and action == self.sn_add_out:
             self._add_port_dialog("Add Output", self.add_output, type_prop="custom_output_schema")

        elif hasattr(self, 'sn_rem_out') and action == self.sn_rem_out:
            custom = self.node.properties.get("custom_output_schema", {})
            self._remove_port_dialog(list(custom.keys()), type_prop="custom_output_schema")

    # --- Helper Methods ---
    def _add_port_dialog(self, title, add_method, prop_name=None, sync_py=False, type_prop=None):
        # 1. Get Name
        name, ok = QInputDialog.getText(None, title, "Name:")
        if not ok or not name: return
        
        if name in [p.name for p in self.ports]:
            QMessageBox.warning(None, "Duplicate Name", "A port with that name already exists.")
            return

        # 2. Get Type (Optional)
        from synapse.core.types import DataType
        types = [t.value for t in DataType]
        # Common types first
        prioritized = ["string", "int", "float", "bool", "list", "dict", "object", "any", "flow", "image"]
        sorted_types = sorted(types, key=lambda x: prioritized.index(x) if x in prioritized else 99)
        
        type_str, ok_type = QInputDialog.getItem(None, "Select Type", "Data Type:", sorted_types, 0, False)
        
        selected_type = DataType(type_str) if ok_type else DataType.ANY

        # 3. Add
        # Check if add_method supports data_type (it should be NodeWidget.add_input/output)
        import inspect
        sig = inspect.signature(add_method)
        if "data_type" in sig.parameters:
            add_method(name, data_type=selected_type)
        else:
            add_method(name)
            
        if prop_name: self._update_list_prop(prop_name, name, add=True)
        
        # [NEW] Save Type Metadata if requested
        if type_prop and self.node:
             type_map = self.node.properties.get(type_prop, {})
             type_map[name] = selected_type.value # Store string value of Enum
             self.node.properties[type_prop] = type_map
        
        if sync_py: self._sync_python_auto_vars()
        self._mark_modified()

    def _remove_port_dialog(self, items, prop_name=None, sync_py=False, type_prop=None):
        if not items: return
        name, ok = QInputDialog.getItem(None, "Remove", "Select:", items, 0, False)
        if ok and name:
            self.remove_port(name)
            if prop_name: 
                self._update_list_prop(prop_name, name, add=False)
                
                # [FIX] Cleanup property if it was a default value for Start/Return nodes
                if self.node_type in ["Start Node", "Return Node"] and name in self.node.properties:
                    del self.node.properties[name]
            
            # [SuperNode] Cleanup Map
            if type_prop and self.node:
                type_map = self.node.properties.get(type_prop, {})
                if name in type_map:
                    del type_map[name]
                    self.node.properties[type_prop] = type_map

            if sync_py: self._sync_python_auto_vars()
            self._mark_modified()

    def _update_list_prop(self, key, value, add=True):
        if not self.node: return
        lst = self.node.properties.get(key, [])
        if add:
            if value not in lst: lst.append(value)
            
            # [FIX] Auto-create property for defaults in Start/Return nodes
            if self.node_type in ["Start Node", "Return Node"]:
                if value not in self.node.properties:
                    self.node.properties[value] = ""
        else:
            if value in lst: lst.remove(value)
        self.node.properties[key] = lst

    def delete_node(self):
        # Remove wires
        for port in self.ports:
            wires = port.wires[:] 
            for wire in wires:
                if wire.scene(): wire.scene().removeItem(wire)
                if wire.start_port: 
                    if wire in wire.start_port.wires: wire.start_port.wires.remove(wire)
                if wire.end_port:
                    if wire in wire.end_port.wires: wire.end_port.wires.remove(wire)
            port.wires.clear()
        if self.scene(): self.scene().removeItem(self)

    def duplicate_node(self):
        scene = self.scene()
        if not scene or not scene.views(): return
        canvas = scene.views()[0] # NodeCanvas
        if hasattr(canvas, "create_standard_node"):
            offset = QPointF(50, 50)
            new_pos = self.pos() + offset
            new_node = canvas.create_standard_node(self.node_type, new_pos)
            if new_node and self.node and new_node.node:
                new_node.node.properties = copy.deepcopy(self.node.properties)
                # Re-create dynamic ports
                cur_names = [p.name for p in new_node.ports]
                for p in self.inputs:
                    if p.name not in cur_names: new_node.add_input(p.name)
                for p in self.outputs:
                    if p.name not in cur_names: new_node.add_output(p.name)
                new_node.update_layout() # Ensure mixin layout is called

    def _mark_modified(self):
        if self.scene() and self.scene().views():
            canvas = self.scene().views()[0]
            if hasattr(canvas, "modified"):
                canvas.modified.emit()

    def _is_node_favorite(self):
        if not self.node or "graph_path" not in self.node.properties: return False
        path = self.node.properties["graph_path"]
        win = QApplication.activeWindow()
        if hasattr(win, 'node_library'):
            return win.node_library.is_favorite(path)
        return False

    def _toggle_favorite(self):
        if not self.node or "graph_path" not in self.node.properties: return
        path = self.node.properties["graph_path"]
        win = QApplication.activeWindow()
        if hasattr(win, 'node_library'):
            if win.node_library.is_favorite(path):
                win.node_library.remove_favorite(path)
            else:
                win.node_library.add_favorite(path)

    def _create_frame_for_nodes(self, nodes):
        scene = self.scene()
        if not nodes or not scene: return
        # Local import to prevent circular dependency with widget/actions
        from synapse.gui.frame_widget import FrameWidget
        frame = FrameWidget(nodes)
        scene.addItem(frame)
        scene.clearSelection()
        frame.setSelected(True)

    def _sync_python_auto_vars(self):
        if not self.node or "script_body" not in self.node.properties: return
        body = self.node.properties.get("script_body", "")
        inputs = self.node.properties.get("additional_inputs", [])
        outputs = self.node.properties.get("additional_outputs", [])
        
        # 1. Inputs
        lines = ["### Auto-Input Vars ###"]
        for inp in inputs:
            safe = inp.replace(" ", "_")
            lines.append(f"{safe} = bridge.get(f'{{node_id}}_{inp}')")
        lines.append("### End of Auto-Input Vars ###")
        new_in = "\n".join(lines)
        
        # 2. Outputs
        out_lines = ["### Auto-Output Vars ###"]
        for outp in outputs:
            safe = outp.replace(" ", "_")
            out_lines.append(f"if '{safe}' in locals(): bridge.set(f'{{node_id}}_{outp}', {safe}, '{self.name}')")
        out_lines.append("### End Auto-Output Vars ###")
        new_out = "\n".join(out_lines)
        
        # 3. Apply
        import re
        # Inputs
        pat_in = re.compile(r"### Auto-Input Vars ###.*?### End of Auto-Input Vars ###", re.DOTALL)
        if pat_in.search(body): body = pat_in.sub(new_in, body)
        else: body = new_in + "\n\n" + body
        
        # Outputs
        pat_out = re.compile(r"### Auto-Output Vars ###.*?### End Auto-Output Vars ###", re.DOTALL)
        if pat_out.search(body): body = pat_out.sub(new_out, body)
        else: body = body + "\n\n" + new_out
            
        self.node.properties["script_body"] = body