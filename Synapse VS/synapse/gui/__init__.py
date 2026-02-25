# Synapse GUI Package

# Global registry of open graphs for live subgraph referencing
# Key: file_path (str) -> Value: serialized graph data (dict)
# This allows SubGraphNode to use in-memory edits instead of file data
LIVE_GRAPHS = {}
