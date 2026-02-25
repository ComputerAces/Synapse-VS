class DataBuffer:
    """
    Wrapper for binary or complex data in Synapse OS.
    Prevents UI lag by masking content under the '[data]' string.
    """
    def __init__(self, content, content_type="raw"):
        self.content = content
        self.content_type = content_type
        
    def __str__(self):
        return "[data]"
        
    def __repr__(self):
        # Provide a bit more info for debugging if needed, but still mask
        size = 0
        try:
            size = len(self.content)
        except: pass
        return f"[data: {size} bytes]"

    def get_raw(self):
        """Returns the actual content for processing nodes."""
        return self.content

    def get_display_str(self):
        """Returns '[data]' for UI displays."""
        return "[data]"

class ErrorObject:
    """
    Standardized Error Container for Synapse OS.
    Passed between nodes via the Bridge when exceptions occur.
    """
    def __init__(self, project_name, node_name, inputs, error_details):
        self.project_name = project_name
        self.node_name = node_name
        self.inputs = inputs if inputs else {}
        self.error_details = str(error_details)
        
    def __str__(self):
        return "[Error]"
        
    def __repr__(self):
        return f"<ErrorObject node='{self.node_name}' err='{self.error_details}'>"
        
    def to_dict(self):
        return {
            "Project": self.project_name,
            "Node": self.node_name,
            "Inputs": self.inputs,
            "Error": self.error_details
        }