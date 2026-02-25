"""
Path resolution utilities for Synapse VS.
"""
import os

def resolve_project_path(path, bridge):
    """
    Resolves a relative path against Project Variables.
    
    Checks (in order):
      1. ProjectVars.path
      2. ProjectVars.project_path
      3. os.getcwd() (fallback)
    
    Args:
        path: The file path (relative or absolute).
        bridge: The SynapseBridge instance.
    
    Returns:
        The absolute path.
    """
    if not path:
        return path
    
    # [FIX] Strip accidental whitespace (common in String Join nodes with " /" separators)
    path = str(path).strip()
    
    # Already absolute? Return normalized.
    if os.path.isabs(path):
        return os.path.normpath(path)
    
    # Check Project Variables in Bridge
    base_path = bridge.get("ProjectVars.path")
    
    if not base_path:
        base_path = bridge.get("ProjectVars.project_path")
    
    # Legacy fallback: Check 'path' directly (for backwards compatibility)
    if not base_path:
        base_path = bridge.get("path")
    
    # Ultimate fallback: Current working directory
    if not base_path:
        base_path = os.getcwd()
    
    if base_path:
        base_path = str(base_path).strip()
        
    # [FIX] Ensure we don't have leading slashes on relative part that break os.path.join drive logic
    if path.startswith('/') or path.startswith('\\'):
        path = path[1:].strip()
        
    full_path = os.path.join(base_path, path)
    
    # [FIX] Convert forward slashes to backslashes on Windows and vice versa
    if os.name == 'nt':
        full_path = full_path.replace('/', '\\')
    else:
        full_path = full_path.replace('\\', '/')

    return os.path.normpath(full_path)
