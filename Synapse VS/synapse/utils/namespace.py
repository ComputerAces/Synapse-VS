"""
Namespace Generator for Parallel Execution.

Generates collision-safe scoped names in the format:
    [NodeName]_[ProcessIndex]_[4DigitHex]

Used by the Parallel Runner Node to uniquely identify workers
and scope their logging + bridge variables.
"""
import os
import logging


def generate_scoped_name(base_name, index, active_names=None):
    """
    Generates a unique scoped name: BaseName_Index_XXXX.
    
    Args:
        base_name:    The node or worker base name (e.g. "OCR_Worker").
        index:        The process index (0, 1, 2, ...).
        active_names: Optional set of currently active names.
                      If provided, hex is regenerated until unique,
                      and the new name is added to the set.
    
    Returns:
        A unique scoped name string.
    """
    # Sanitize base name: replace spaces with underscores
    safe_base = base_name.replace(" ", "_").replace("/", "_")
    
    max_attempts = 1000
    for _ in range(max_attempts):
        hex_code = os.urandom(2).hex().upper()  # 4-digit hex
        name = f"{safe_base}_{index}_{hex_code}"
        
        if active_names is None:
            return name
        
        if name not in active_names:
            active_names.add(name)
            return name
    
    # Fallback: use PID + counter
    fallback = f"{safe_base}_{index}_{os.getpid():04X}"
    if active_names is not None:
        active_names.add(fallback)
    return fallback


def create_scoped_logger(scoped_name, level=logging.INFO):
    """
    Creates a logger with the scoped name as prefix.
    
    Output format: [OCR_Worker_1_A2B3] Found text: "Invoice"
    
    Args:
        scoped_name: The unique scoped name from generate_scoped_name.
        level:       Logging level (default: INFO).
    
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(scoped_name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(f"[{scoped_name}] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
