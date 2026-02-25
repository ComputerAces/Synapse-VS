import logging
import sys
from logging.handlers import RotatingFileHandler
import os

_shared_file_handler = None
_shared_console_handler = None

def setup_logger(name, log_file="synapse.log", level=logging.INFO):
    """
    Sets up a logger with both console and file handlers.
    """
    global _shared_file_handler, _shared_console_handler
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if _shared_file_handler is None:
        try:
            # Perform a dirty start-up rotation to avoid mid-execution WinError 32 file locks
            if os.path.exists(log_file) and os.path.getsize(log_file) > 5 * 1024 * 1024:
                if os.path.exists(log_file + ".1"):
                    try:
                        os.remove(log_file + ".1")
                    except: pass
                try:
                    os.rename(log_file, log_file + ".1")
                except: pass
        except Exception:
            pass
            
        _shared_file_handler = logging.FileHandler(log_file)
        _shared_file_handler.setFormatter(formatter)
        
    if _shared_console_handler is None:
        _shared_console_handler = logging.StreamHandler(sys.stdout)
        _shared_console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Avoid adding duplicate handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(_shared_file_handler)
        logger.addHandler(_shared_console_handler)

    return logger

# Global logger instance for the main process
main_logger = setup_logger("SynapseCore")
