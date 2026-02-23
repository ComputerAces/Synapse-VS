import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QListWidgetItem, QTreeWidgetItem, QTabWidget, QPushButton
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QColor, QBrush
from .tree import DraggableTreeWidget
from .list import DraggableListWidget
from synapse.utils.logger import main_logger as logger

FAVORITES_FILE = "favorites.json"

class NodeLibrary(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
            
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search Box & Scope
        from PyQt6.QtWidgets import QLineEdit, QComboBox
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes...")
        self.search_input.textChanged.connect(self.filter_nodes)
        search_layout.addWidget(self.search_input, 4)
        
        self.search_scope = QComboBox()
        self.search_scope.addItems(["All", "Categories", "Node Names", "Properties", "Ports/Flows"])
        self.search_scope.currentIndexChanged.connect(lambda: self.filter_nodes(self.search_input.text()))
        search_layout.addWidget(self.search_scope, 1)
        
        self.main_layout.addLayout(search_layout)
        
        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 1. Quick Links
        self.quick_container = QWidget()
        quick_layout = QVBoxLayout(self.quick_container)
        quick_layout.setContentsMargins(0, 5, 0, 0)
        quick_layout.addWidget(QLabel("Quick Links"))
        self.quick_list = DraggableListWidget(self)
        quick_layout.addWidget(self.quick_list)
        self.splitter.addWidget(self.quick_container)
        
        # 2. Main Area (Tree Only)
        self.tree_container = QWidget()
        tree_layout = QVBoxLayout(self.tree_container)
        tree_layout.setContentsMargins(0, 5, 0, 0)
        
        self.tree_widget = DraggableTreeWidget(self)
        self.tree_widget.setHeaderHidden(True)
        tree_layout.addWidget(self.tree_widget)
        
        # 3. Controls (Collapse/Expand)
        controls_layout = QHBoxLayout()
        self.btn_collapse = QPushButton("Collapse All")
        self.btn_expand = QPushButton("Expand All")
        
        self.btn_collapse.clicked.connect(self.on_collapse_all)
        self.btn_expand.clicked.connect(self.on_expand_all)
        
        controls_layout.addWidget(self.btn_collapse)
        controls_layout.addWidget(self.btn_expand)
        tree_layout.addLayout(controls_layout)
        
        self.splitter.addWidget(self.tree_container)
        
        self.main_layout.addWidget(self.splitter)
        
        self.splitter.splitterMoved.connect(self.save_splitter_state)
        
        self.favorites = [] 
        self.quick_links = [] 
        
        self.load_favorites()
        self.load_quick_links()
        self.load_splitter_state()
        
        self.populate_quick_links()

        # [NEW] Session-Persistent State Connections
        self.tree_widget.itemExpanded.connect(self.save_tree_state)
        self.tree_widget.itemCollapsed.connect(self.save_tree_state)
        
        # Lazy Load Library
        QTimer.singleShot(0, self.populate_library)

    def get_snippets_dir(self):
        d = os.path.join(os.getcwd(), "snippets")
        if not os.path.exists(d): os.makedirs(d)
        return d


    
    def on_collapse_all(self):
        self.tree_widget.collapseAll()
        
    def on_expand_all(self):
        self.tree_widget.expandAll()

    def filter_nodes(self, text):
        search_text = text.lower().strip()
        scope = self.search_scope.currentText()
        
        for i in range(self.tree_widget.topLevelItemCount()):
            category = self.tree_widget.topLevelItem(i)
            visible_children = self._filter_category(category, search_text, scope)
            
            # Special case for Category scope: if the category itself matches, show it
            cat_match = scope == "Categories" and search_text in category.text(0).lower()
            is_hidden = (visible_children == 0 and not cat_match) and bool(search_text)
            category.setHidden(is_hidden)
            
            # [NEW] Auto-expand if search is active and category has matches
            if search_text and not is_hidden:
                category.setExpanded(True)

    def _filter_category(self, category, search_text, scope):
        """Recursively filter a category and its children."""
        visible_children = 0
        for j in range(category.childCount()):
            child = category.child(j)
            
            # If this child has sub-children (nested category), recurse
            if child.childCount() > 0:
                sub_visible = self._filter_category(child, search_text, scope)
                
                # If scope is Categories, sub-category might match directly
                cat_match = scope == "Categories" and search_text in child.text(0).lower()
                
                is_hidden = (sub_visible == 0 and not cat_match) and bool(search_text)
                child.setHidden(is_hidden)
                
                if sub_visible > 0 or cat_match: 
                    visible_children += 1
                    # [NEW] Auto-expand nested categories if search matches
                    if search_text:
                        child.setExpanded(True)
                continue
            
            if not search_text:
                child.setHidden(False)
                visible_children += 1
                continue
            
            match = False
            label = child.text(0).lower()
            
            if scope == "All":
                if search_text in label:
                    match = True
                elif search_text in self._get_port_search_text(child):
                    match = True
            elif scope == "Categories":
                # Leaf nodes don't match categories unless parent matches (handled by recursion)
                match = False 
            elif scope == "Node Names":
                match = search_text in label
            elif scope == "Properties":
                # Deep search through docstrings
                desc = self._get_node_description(label).lower()
                match = search_text in desc
            elif scope == "Ports/Flows":
                match = search_text in self._get_port_search_text(child)

            if match:
                child.setHidden(False)
                visible_children += 1
            else:
                child.setHidden(True)
                
        return visible_children

    def _get_node_description(self, label):
        """Internal helper to get node docstrings for property search."""
        try:
            from synapse.nodes.registry import NodeRegistry
            node_cls = NodeRegistry.get_node_class(label)
            return node_cls.__doc__ or ""
        except: return ""

    def _get_port_search_text(self, tree_item):
        """Returns a cached lowercase string of all port names for deep search."""
        # Check cache (stored in UserRole+1)
        cached = tree_item.data(0, Qt.ItemDataRole.UserRole + 1)
        if cached is not None:
            return cached
        
        label = tree_item.text(0)
        port_names = []
        
        try:
            from synapse.nodes.registry import NodeRegistry
            node_cls = NodeRegistry.get_node_class(label)
            if node_cls:
                # Gather input port names
                inputs = getattr(node_cls, 'default_inputs', None)
                if isinstance(inputs, property):
                    try:
                        temp = node_cls.__new__(node_cls)
                        inputs = temp.default_inputs
                    except: inputs = None
                if inputs:
                    for inp in inputs:
                        port_names.append(inp[0] if isinstance(inp, tuple) else inp)
                
                # Gather output port names
                outputs = getattr(node_cls, 'default_outputs', None)
                if isinstance(outputs, property):
                    try:
                        temp = node_cls.__new__(node_cls) if not inputs else temp
                        outputs = temp.default_outputs
                    except: outputs = None
                if outputs:
                    for out in outputs:
                        port_names.append(out[0] if isinstance(out, tuple) else out)
        except: pass
        
        result = " ".join(port_names).lower()
        tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, result)
        return result
        
    def get_favorites_path(self):
        return os.path.join(os.getcwd(), FAVORITES_FILE)

    def get_quick_links_path(self):
        return os.path.join(os.getcwd(), "quick_links.json")

    def save_splitter_state(self):
        settings = QSettings("SynapseOS", "NodeLibrary")
        settings.setValue("splitter_state", self.splitter.saveState())

    def load_splitter_state(self):
        try:
            settings = QSettings("SynapseOS", "NodeLibrary")
            state = settings.value("splitter_state")
            if state:
                self.splitter.restoreState(state)
            else:
                self.splitter.setSizes([150, 350])
        except Exception:
            self.splitter.setSizes([150, 350])

    def save_tree_state(self):
        """Saves expanded item paths to QSettings."""
        settings = QSettings("SynapseOS", "NodeLibrary")
        expanded = self._get_currently_expanded_paths()
        settings.setValue("tree_expansion_state", expanded)

    def load_tree_state(self):
        """Returns list of expanded item paths from QSettings."""
        settings = QSettings("SynapseOS", "NodeLibrary")
        return settings.value("tree_expansion_state", [])

    def _get_currently_expanded_paths(self):
        expanded_items = []
        def get_expanded_recursive(item):
            if item.isExpanded():
                expanded_items.append(self._get_item_path(item))
            for i in range(item.childCount()):
                get_expanded_recursive(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            get_expanded_recursive(self.tree_widget.topLevelItem(i))
        return expanded_items

    def _restore_expanded_paths(self, expanded_items):
        if not expanded_items:
            return
            
        def restore_recursive(item):
            if self._get_item_path(item) in expanded_items:
                item.setExpanded(True)
            for i in range(item.childCount()):
                restore_recursive(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            restore_recursive(self.tree_widget.topLevelItem(i))
        
    def load_favorites(self):
        # [ULTRA-SAFE] Ensure logger is available
        from synapse.utils.logger import main_logger as logger
        
        try:
            if os.path.exists(self.get_favorites_path()):
                with open(self.get_favorites_path(), 'r') as f:
                    raw = json.load(f)
                    all_paths = [os.path.abspath(p) for p in raw]
                    
                    # [CLEANUP] Check for existence
                    existing = []
                    missing = []
                    for p in all_paths:
                        if os.path.exists(p):
                            existing.append(p)
                        else:
                            missing.append(p)
                    
                    self.favorites = existing
                    
                    if missing:
                        from PyQt6.QtWidgets import QMessageBox
                        names = [os.path.basename(p) for p in missing]
                        logger.warning(f"Removing missing favorites: {names}")
                        # Update file immediately
                        self.save_favorites()
                        
                        # Notify user once
                        QMessageBox.warning(self, "Missing Favorites", 
                                          "The following favorite graphs were missing and have been removed:\n\n" + 
                                          "\n".join(names))
        except Exception as e:
            logger.error(f"Error loading favorites: {e}")
            self.favorites = []

    def load_quick_links(self):
        try:
            if os.path.exists(self.get_quick_links_path()):
                with open(self.get_quick_links_path(), 'r') as f:
                    raw_links = json.load(f)
                    
                    # [CLEANUP] Filter missing file-based links
                    clean_links = []
                    missing_names = []
                    for link in raw_links:
                        payload = link.get("payload")
                        label = link.get("label", "Unknown")
                        # If payload looks like a path and doesn't exist, skip it
                        if isinstance(payload, str) and (payload.endswith(".syp") or payload.endswith(".json")):
                            if os.path.exists(payload):
                                clean_links.append(link)
                            else:
                                missing_names.append(label)
                        else:
                            clean_links.append(link)
                            
                    self.quick_links = clean_links
                    if len(clean_links) != len(raw_links):
                        self.save_quick_links()
                        
                        if missing_names:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Missing Quick Links", 
                                              "The following quick links were missing their source files and have been removed:\n\n" + 
                                              "\n".join(missing_names))
        except Exception:
            self.quick_links = []
            
    def save_favorites(self):
        try:
            with open(self.get_favorites_path(), 'w') as f:
                json.dump(self.favorites, f, indent=4)
        except Exception: pass

    def save_quick_links(self):
        try:
            with open(self.get_quick_links_path(), 'w') as f:
                json.dump(self.quick_links, f, indent=4)
        except Exception: pass

    def update_path(self, old_path, new_path):
        """Remaps favorites and quick links when a file is moved/renamed."""
        if not old_path or not new_path or old_path == new_path:
            return
            
        old_path = os.path.abspath(old_path)
        new_path = os.path.abspath(new_path)
        changed = False
        
        # 1. Remap Favorites
        if old_path in self.favorites:
            self.favorites = [new_path if p == old_path else p for p in self.favorites]
            changed = True
            
        # 2. Remap Quick Links
        for link in self.quick_links:
            if link.get("payload") == old_path:
                link["payload"] = new_path
                # Also update label if it was the filename
                if link.get("label") == os.path.basename(old_path):
                    link["label"] = os.path.basename(new_path)
                changed = True
                
        if changed:
            self.save_favorites()
            self.save_quick_links()
            # Force registry to see the new path if it's a favorite
            if new_path in self.favorites:
                from synapse.core.loader import load_favorites_into_registry
                load_favorites_into_registry()
            self.populate_library()

    def add_quick_link(self, data):
        for q in self.quick_links:
            if q["payload"] == data["payload"]: return
        self.quick_links.append(data)
        self.save_quick_links()
        self.populate_quick_links()

    def remove_quick_link(self, data):
        self.quick_links = [q for q in self.quick_links if q["payload"] != data["payload"]]
        self.save_quick_links()
        self.populate_quick_links()

    def populate_quick_links(self):
        self.quick_list.clear()
        for link in self.quick_links:
            item = QListWidgetItem(link["label"])
            item.setData(Qt.ItemDataRole.UserRole, link)
            self.quick_list.addItem(item)

    def add_favorite(self, path):
        path = os.path.abspath(path)
        if path not in self.favorites:
            self.favorites.append(path)
            self.save_favorites()
            # Force registry update before refresh
            from synapse.core.loader import load_favorites_into_registry
            load_favorites_into_registry()
            self.populate_library()
            
    def remove_favorite(self, path):
        path = os.path.abspath(path)
        if path in self.favorites:
            self.favorites.remove(path)
            self.save_favorites()
            # Force registry update before refresh (registry will handle cleanup)
            from synapse.core.loader import load_favorites_into_registry
            load_favorites_into_registry()
            self.populate_library()
            
    def is_favorite(self, path):
        if not path: return False
        return os.path.abspath(path) in self.favorites

    def set_tooltips_hidden(self, hidden):
        self.tooltips_hidden = hidden

    def add_current_graph_as_tool(self):
        """Adds the currently active graph to the node library as a favorite."""
        from PyQt6.QtWidgets import QApplication, QMessageBox
        
        # 1. Get MainWindow (which should have get_current_graph)
        main_win = self.window()
        if not hasattr(main_win, 'get_current_graph'):
             # Try parent if window() didn't work as expected
             main_win = self.parent()
             while main_win and not hasattr(main_win, 'get_current_graph'):
                 main_win = main_win.parent()
                 
        if not main_win or not hasattr(main_win, 'get_current_graph'):
            return

        graph = main_win.get_current_graph()
        if not graph:
            QMessageBox.information(self, "Add to Library", "No active graph to add.")
            return

        # 2. Check if saved
        path = getattr(graph, 'file_path', None)
        if not path:
            res = QMessageBox.question(self, "Save Graph", 
                                     "The graph must be saved before adding it to the library. Save now?",
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)
            if res == QMessageBox.StandardButton.Save:
                # Trigger save via MainWindow
                if hasattr(main_win, 'save_graph'):
                    main_win.save_graph(graph)
                    path = getattr(graph, 'file_path', None)
                
            if not path:
                return

        # 3. Add to favorites (which refreshes library)
        self.add_favorite(path)
        QMessageBox.information(self, "Add to Library", f"Added '{os.path.basename(path)}' to Node Library.")
        # Trigger registry update then refresh
        from synapse.core.loader import load_favorites_into_registry
        load_favorites_into_registry()
        self.populate_library()
        

    def get_or_create_category_item(self, category_path):
        """
        Traverses or creates the category tree based on a path "Grandparent/Parent/Child".
        Returns the QTreeWidgetItems for the leaf category.
        """
        if not category_path: category_path = "Uncategorized"
        
        # Normalize separators
        clean_path = category_path.replace("\\", "/")
        parts = [p.strip() for p in clean_path.split("/") if p.strip()]
        
        if not parts: parts = ["Uncategorized"]

        current_item = None
        
        # We need a way to track root items vs child items.
        # Since we clear() the tree at start of populate, we can just search top-level then children.
        
        # Top Level
        root_text = parts[0]
        root_item = None
        
        for i in range(self.tree_widget.topLevelItemCount()):
            it = self.tree_widget.topLevelItem(i)
            if it.text(0) == root_text:
                root_item = it
                break
        
        if not root_item:
            root_item = QTreeWidgetItem(self.tree_widget)
            root_item.setText(0, root_text)
            root_item.setFlags(root_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled) 
            root_item.setExpanded(True)
            
        current_item = root_item
        
        # Traverse Children
        for part in parts[1:]:
            found_child = None
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                # Check for existing CATEGORY items (we might have node items mixed in, 
                # but node labels shouldn't clash with category names ideally, or we accept the collision/merge)
                if child.text(0) == part:
                    found_child = child
                    break
            
            if not found_child:
                found_child = QTreeWidgetItem(current_item)
                found_child.setText(0, part)
                found_child.setFlags(found_child.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
                found_child.setExpanded(True)
                
            current_item = found_child
            
        return current_item

    def populate_library(self):
        """Unified method to populate the node library with standard nodes, favorites, and snippets."""
        try:
            # 1. Save Current State (so we don't lose session-only changes)
            current_session_expanded = self._get_currently_expanded_paths()
            persistent_expanded = self.load_tree_state()
            
            # Combine
            expanded_items = list(set(current_session_expanded + (persistent_expanded if persistent_expanded else [])))
            
            search_text = self.search_input.text()

            self.tree_widget.clear()
            from synapse.nodes.registry import NodeRegistry
            
            # 2. Load Registry Nodes
            registry_cats = NodeRegistry.get_categories()
            for cat, nodes in registry_cats.items():
                if cat == "Hidden": continue
                parent = self.get_or_create_category_item(cat)
                
                for node_name in nodes:
                    node_cls = NodeRegistry.get_node_class(node_name)
                    if not node_cls: continue
                    
                    is_plugin = hasattr(node_cls, "graph_path") and node_cls.graph_path
                    self._add_node_to_item(parent, node_name, is_plugin, 
                                          node_cls.graph_path if is_plugin else None, 
                                          node_cls.__doc__ or "Plugin Subgraph" if is_plugin else None)

            # 3. Load Snippets
            snippets_dir = self.get_snippets_dir()
            if os.path.exists(snippets_dir):
                files = [f for f in os.listdir(snippets_dir) if f.endswith(".json")]
                for f in files:
                    path = os.path.join(snippets_dir, f)
                    try:
                         with open(path, 'r') as file:
                             data = json.load(file)
                             s_name = data.get("name", os.path.splitext(f)[0])
                             s_cat = data.get("category", "Snippets")
                             s_desc = data.get("description", "Snippet")
                             
                             parent = self.get_or_create_category_item(s_cat)
                             self._add_node_to_item(parent, s_name, False, path, s_desc, is_snippet=True)
                    except: pass
            
            # 4. Sort & Restore State
            self.tree_widget.sortItems(0, Qt.SortOrder.AscendingOrder)
            self._restore_expanded_paths(expanded_items)

            # Re-apply search
            if search_text:
                self.filter_nodes(search_text)
            
        except Exception as e:
            print(f"CRITICAL ERROR in populate_library: {e}")

    def _get_item_path(self, item):
        """Builds a slash-separated path for a tree item."""
        path = [item.text(0)]
        curr = item.parent()
        while curr:
            path.insert(0, curr.text(0))
            curr = curr.parent()
        return "/".join(path)

    def _add_node_to_item(self, parent_item, label, is_plugin, path=None, desc=None, is_snippet=False):
        node_item = QTreeWidgetItem(parent_item)
        node_item.setText(0, label)
        
        hide_tips = getattr(self, 'tooltips_hidden', False)

        from synapse.nodes.registry import NodeRegistry
        node_class = NodeRegistry.get_node_class(label)
        
        # [NEW] Dependency-based coloring (Hot Plugins)
        has_deps = False
        all_installed = True
        if node_class and hasattr(node_class, "required_libraries"):
            from synapse.core.dependencies import DependencyManager
            reqs = node_class.required_libraries
            if reqs:
                has_deps = True
                for lib in reqs:
                    if not DependencyManager.is_installed(lib):
                        all_installed = False
                        break

        # Apply Styling based on status
        if is_snippet:
             # SNIPPETS: Blue/Bold
             node_item.setData(0, Qt.ItemDataRole.UserRole, f"SNIPPET:{path}")
             font = node_item.font(0)
             font.setBold(True)
             node_item.setFont(0, font)
             node_item.setForeground(0, QBrush(QColor("#00BFFF"))) # Blue
             
             if not hide_tips:
                 clean_desc = desc.replace("\n", "<br>")
                 tooltip = f"<html><b>Snippet: {label}</b><br><br>{clean_desc}</html>"
                 node_item.setToolTip(0, tooltip)
        
        elif has_deps:
            # HOT PLUGIN: Dark Yellow (Missing) or Dark Purple (Installed)
            if not all_installed:
                node_item.setForeground(0, QBrush(QColor("#8B8000"))) # Dark Yellow
            else:
                node_item.setForeground(0, QBrush(QColor("#6A0DAD"))) # Dark Purple
            
            font = node_item.font(0)
            font.setBold(True)
            node_item.setFont(0, font)
            
            if is_plugin:
                node_item.setData(0, Qt.ItemDataRole.UserRole, path)
            
            if not hide_tips and node_class:
                import inspect
                doc = inspect.cleandoc(node_class.__doc__ or "").strip()
                ver = getattr(node_class, 'version', '1.0.0')
                formatted_doc = doc.replace("\n", "<br>")
                status = "<b>Status:</b> <span style='color:red;'>Missing Libraries</span>" if not all_installed else "<b>Status:</b> <span style='color:green;'>Installed</span>"
                req_text = f"<br><br><b>Requires:</b> {', '.join(node_class.required_libraries)}<br>{status}"
                tooltip = f"<html><b>{label}</b> (v{ver})<br><br>{formatted_doc}{req_text}</html>"
                node_item.setToolTip(0, tooltip)

        elif is_plugin:
            # PLUGINS: Green/Bold
            node_item.setData(0, Qt.ItemDataRole.UserRole, path)
            font = node_item.font(0)
            font.setBold(True)
            node_item.setFont(0, font)
            node_item.setForeground(0, QBrush(QColor("#008000"))) # Dark Green
            
            if not hide_tips:
                clean_desc = desc.replace("\n", "<br>") if desc else label
                tooltip = f"<html>{clean_desc}</html>"
                node_item.setToolTip(0, tooltip)

        else:
            # STANDARD
            if not hide_tips:
                if node_class:
                    import inspect
                    doc = inspect.cleandoc(node_class.__doc__ or "").strip()
                    ver = getattr(node_class, 'version', '1.0.0')
                    formatted_doc = doc.replace("\n", "<br>")
                    if formatted_doc:
                        tooltip = f"<html><b>{label}</b> (v{ver})<br><br>{formatted_doc}</html>"
                    else:
                        tooltip = f"<html><b>{label}</b> (v{ver})<br><br>Description pending...</html>"
                    node_item.setToolTip(0, tooltip)
                else:
                    node_item.setToolTip(0, label)
            
            if parent_item.text(0) == "Enums":
                font = node_item.font(0)
                font.setItalic(True)
                node_item.setFont(0, font)
