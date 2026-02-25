from synapse.core.node import BaseNode

class NodeRegistry:
    _nodes = {} # label -> node_class
    _categories = {} # category -> [labels]

    @classmethod
    def register(cls, label, category="General"):
        def decorator(node_class):
            # 1. Cleanup old category mapping if re-registering
            for cat_list in cls._categories.values():
                if label in cat_list:
                    cat_list.remove(label)

            # Register namespaced key (Category.Label)
            namespaced_label = f"{category}.{label}"
            cls._nodes[namespaced_label] = node_class
            
            # Register legacy short label (warn on collision?)
            if label not in cls._nodes:
                cls._nodes[label] = node_class
            else:
                # Collision detected!
                # We overwrite for now but could log warning.
                # Use namespaced version to be safe.
                cls._nodes[label] = node_class # Last write wins strategy for legacy
            
            if category not in cls._categories:
                cls._categories[category] = []
            if label not in cls._categories[category]:
                cls._categories[category].append(label)
                
            # Attach metadata to class
            node_class.node_label = label
            node_class.node_category = category
            node_class.node_namespaced_id = namespaced_label
            
            return node_class
        return decorator

    @classmethod
    def get_node_class(cls, label):
        return cls._nodes.get(label)

    @classmethod
    def get_all_labels(cls):
        return list(cls._nodes.keys())

    @classmethod
    def get_categories(cls):
        return cls._categories

    @classmethod
    def register_subgraph(cls, label, path, category="Uncategorized", is_alias=False, description=None):
        # Map a custom label to a Dynamic Subclass of SubGraphNode
        # This ensures the class metadata (node_label) matches the registry key
        
        # 1. Deduplication check: if this exact path is already registered under this label, skip.
        # This prevents redundant class creation during rapid refreshes.
        existing = cls._nodes.get(label)
        if existing and hasattr(existing, 'graph_path') and existing.graph_path == path:
            # Update description if it changed
            if description and existing.__doc__ != description:
                existing.__doc__ = description
            return

        # 2. Cleanup old category mapping if re-registering
        for cat_list in cls._categories.values():
            if label in cat_list:
                cat_list.remove(label)

        base_cls = cls._nodes.get("SubGraph Node")
        if base_cls:
             # Create dynamic class
             # name needs to be a valid identifier
             safe_name = "".join(x for x in label.title() if x.isalnum())
             new_cls = type(safe_name, (base_cls,), {})
             
             # Set Metadata
             new_cls.node_label = label
             new_cls.node_category = category
             new_cls.graph_path = path
             new_cls.__doc__ = description or "Plugin Subgraph"
             
             # Register
             cls._nodes[label] = new_cls
             
             # Only add to categories if NOT an alias
             if not is_alias:
                 if category not in cls._categories:
                     cls._categories[category] = []
                 if label not in cls._categories[category]:
                     cls._categories[category].append(label)

    @classmethod
    def unregister(cls, label):
        """Removes a node from the registry and cleanup category mappings."""
        if label in cls._nodes:
            del cls._nodes[label]
        
        # Cleanup category mapping
        for cat_name, node_list in list(cls._categories.items()):
            if label in node_list:
                node_list.remove(label)
            # Remove empty categories (optional, but keeps things clean)
            if not node_list:
                del cls._categories[cat_name]
