import os
import sys
import signal
import traceback
import subprocess
import multiprocessing
import time
from axonpulse.utils.logger import setup_logger
from axonpulse.utils.shm_tracker import SHMTracker

logger = setup_logger("CleanupManager")

class CleanupManager:
    """
    Centralized manager for AxonPulse processes and error handling.
    Ensures graceful shutdown of subprocesses and captures fatal crash reports.
    """
    _instance = None
    _processes = []
    _engines = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CleanupManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register_process(cls, process):
        """Registers a process for tracking and cleanup."""
        cls._processes.append(process)

    @classmethod
    def register_engine(cls, engine):
        """Registers an ExecutionEngine instance for graceful stop."""
        cls._engines.append(engine)

    @classmethod
    def cleanup_all(cls):
        """Terminates all registered processes and reaps orphaned children."""
        logger.info("Initiating Global Cleanup...")
        
        # 0. Gracefully Stop Engines
        if cls._engines:
            logger.info(f"Signaling {len(cls._engines)} engine(s) to stop...")
            for engine in cls._engines:
                try:
                    engine.stop()
                except: pass
            
            # Wait briefly for engines to finish (Barrier)
            time.sleep(0.5)

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
    def cleanup_orphaned_shm(cls):
        """
        [NEW] Orphaned SHM Garbage Collection.
        Reads the SHM registry and unlinks any blocks that are still allocated in the OS.
        This prevents memory leaks on Windows after crashes.
        """
        from multiprocessing import shared_memory
        tracked_blocks = SHMTracker.get_all()
        if not tracked_blocks:
            return

        logger.info(f"[SHM_GC] Checking {len(tracked_blocks)} tracked SHM blocks for orphans...")
        cleaned_count = 0
        for shm_name in tracked_blocks:
            try:
                # Try to attach. If it exists, we close and unlink it.
                # If it doesn't exist, we just unregister it.
                try:
                    shm = shared_memory.SharedMemory(name=shm_name)
                    shm.close()
                    shm.unlink()
                    cleaned_count += 1
                except FileNotFoundError:
                    pass # Already gone from OS
                
                SHMTracker.unregister(shm_name)
            except Exception as e:
                logger.debug(f"[SHM_GC] Failed to cleanup block '{shm_name}': {e}")
        
        if cleaned_count > 0:
            logger.info(f"[SHM_GC] Successfully unlinked {cleaned_count} orphaned SHM blocks.")

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
            with open("axonpulse_error.cache", "w") as f:
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

    # [NEW] Perform initial SHM cleanup to catch orphans from previous crashes
    manager.cleanup_orphaned_shm()
    
    # 2. Signal Handlers
    _shutting_down = False
    def sig_handler(signum, frame):
        nonlocal _shutting_down
        if _shutting_down:
            # Second Ctrl+C: force kill immediately
            logger.warning("Force kill requested.")
            os._exit(1)
        _shutting_down = True
        logger.info(f"Received signal {signum}. Shutting down...")
        
        # [FIX] Instead of os._exit, we raise KeyboardInterrupt to allow the main thread 
        # to catch it and exit cleanly through its own finally blocks.
        manager.cleanup_all()
        # On Windows, raising KeyboardInterrupt in a signal handler might not work 
        # as expected if the signal handler is called in a separate thread, 
        # but in current Python it should be pushed to the main thread.
        # We also call os.kill(pid, signal.CTRL_C_EVENT) inside cleanup if needed,
        # but for now, raising should work or the engine will see _SYSTEM_STOP.
        raise KeyboardInterrupt()

    try:
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)
    except Exception as e:
        logger.error(f"Failed to bind signals: {e}")

    # 3. Atexit fallback
    import atexit
    atexit.register(manager.cleanup_all)
