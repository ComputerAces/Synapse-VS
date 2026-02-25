import os
import sys
import signal
import traceback
import subprocess
import multiprocessing
import time
from synapse.utils.logger import setup_logger

logger = setup_logger("CleanupManager")

class CleanupManager:
    """
    Centralized manager for Synapse processes and error handling.
    Ensures graceful shutdown of subprocesses and captures fatal crash reports.
    """
    _instance = None
    _processes = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CleanupManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register_process(cls, process):
        """Registers a process for tracking and cleanup."""
        cls._processes.append(process)

    @classmethod
    def cleanup_all(cls):
        """Terminates all registered processes and reaps orphaned children."""
        logger.info("Initiating Global Cleanup...")
        
        # 1. Kill Registered Processes
        for p in cls._processes:
            try:
                if hasattr(p, 'terminate'):
                    p.terminate()
                elif hasattr(p, 'kill'):
                    p.kill()
            except Exception:
                pass

        # 2. Reap Orphaned Children (Deep Cleanup)
        try:
            import psutil
            current_process = psutil.Process(os.getpid())
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    logger.debug(f"Terminating orphaned child: {child.pid}")
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait briefly then force kill survivors
            _, alive = psutil.wait_procs(children, timeout=2)
            for p in alive:
                try:
                    logger.warning(f"Force killing stubborn child: {p.pid}")
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            if children:
                logger.info(f"Cleaned up {len(children)} child process(es).")
                
        except ImportError:
            # Fallback to multiprocessing
            for p in multiprocessing.active_children():
                p.terminate()
                p.join(timeout=1)
        except Exception as e:
            logger.error(f"Cleanup Error: {e}")

    @classmethod
    def handle_exception(cls, exc_type, exc_value, exc_traceback):
        """Global exception hook to capture crashes and ensure cleanup."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.critical(f"FATAL CRASH DETECTED:\n{error_msg}")
        
        # Write to Error Cache
        try:
            with open("synapse_error.cache", "w") as f:
                f.write(f"Timestamp: {time.ctime()}\n")
                f.write(f"Process ID: {os.getpid()}\n")
                f.write("-" * 40 + "\n")
                f.write(error_msg)
        except Exception as e:
            logger.error(f"Failed to write error cache: {e}")

        # Ensure cleanup runs
        cls.cleanup_all()
        
        # Continue with standard exit
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

def init_global_handlers():
    """Initializes signal handlers and exception hooks."""
    manager = CleanupManager()
    
    # 1. Sys Exception Hook
    sys.excepthook = manager.handle_exception
    
    # 2. Signal Handlers
    def sig_handler(signum, frame):
        logger.info(f"Received signal {signum}. Shutting down...")
        manager.cleanup_all()
        # Re-raise or exit
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)
    except Exception as e:
        logger.error(f"Failed to bind signals: {e}")

    # 3. Atexit fallback
    import atexit
    atexit.register(manager.cleanup_all)
