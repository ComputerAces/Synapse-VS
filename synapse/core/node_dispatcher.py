import threading
import queue
import time
import asyncio
from synapse.utils.logger import setup_logger

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def _run_node_task(node, inputs):
    """Helper to run node in pool worker."""
    try:
        if hasattr(node, '_run_wrapper'):
            return node._run_wrapper(**inputs)
        else:
            exec_args = node.prepare_execution_args(inputs) if hasattr(node, 'prepare_execution_args') else inputs
            return node.execute(**exec_args)
    except Exception as e:
        raise e

class NodeDispatcher:
    """
    Decides HOW to run a node (Hybrid Execution Architecture).
    - Native/Safe: Runs in a Thread Pool (Shared with Engine).
    - Async/IO: Runs in a dedicated AsyncIO Event Loop Thread.
    - Heavy/Unsafe: Runs in a Process Pool (Warm Processes).
    """
    def __init__(self, bridge=None, is_child=False):
        self.logger = setup_logger("NodeDispatcher")
        self.running = True
        self.is_child = is_child
        self.bridge = bridge 
        
        # Native Task Pool (Parallel Threaded Native execution)
        self.native_executor = ThreadPoolExecutor(max_workers=32)

        # AsyncIO Worker
        self.async_loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._async_loop_runner, name="SynapseAsyncWorker", daemon=True)
        self.async_thread.start()
        
        # Heavy Worker Pool
        self.executor = ProcessPoolExecutor()
        
    def _async_loop_runner(self):
        """Runs the AsyncIO loop in a separate thread."""
        asyncio.set_event_loop(self.async_loop)
        self.logger.info("AsyncIO Worker Thread Started.")
        self.async_loop.run_forever()

    def dispatch(self, node, inputs, context_stack=[]):
        """
        routes execution request.
        """
        # --- Functional Hijacking ---
        node_type = type(node).__name__
        handler_node_id = self.bridge.get_hijack_handler(context_stack, node_type)
        
        if handler_node_id:
            self.logger.info(f"Hijacking execution of {node.name} ({node_type}) via Provider {handler_node_id}")
            inputs["_hijack_provider_id"] = handler_node_id
            inputs["_is_hijacked"] = True

        # 1. Async Node
        if getattr(node, "is_async", False):
            future = FutureResult()
            asyncio.run_coroutine_threadsafe(self._execute_async_wrapper(node, inputs, future), self.async_loop)
            return future

        # 2. Native Node
        if getattr(node, "is_native", False):
            # [FIX] Use ThreadPool instead of single-threaded Queue for Parallelism
            ft = self.native_executor.submit(self._execute_native_task, node, inputs)
            return PooledFuture(ft)
            
        # 3. Heavy/Process Node
        else:
            ft = self.executor.submit(_run_node_task, node, inputs)
            return PooledFuture(ft)
    
    def _execute_native_task(self, node, inputs):
        """Executes a native node safely within the thread pool."""
        try:
            self.logger.info(f"[Native] Executing {node.name}...")
            
            # [FIX] Use _run_wrapper to ensure context restoration and error handling
            if hasattr(node, '_run_wrapper'):
                return node._run_wrapper(**inputs)
            else:
                exec_args = node.prepare_execution_args(inputs)
                return node.execute(**exec_args)
        except (BrokenPipeError, EOFError, ConnectionResetError):
            self.running = False
            raise
        except Exception as e:
            if "pipe is being closed" not in str(e).lower():
                self.logger.error(f"[Native] Crash in {node.name}: {e}")
            raise e

    async def _execute_async_wrapper(self, node, inputs, future):
        """Coroutine wrapper to execute node and update future."""
        try:
            self.logger.info(f"[Async] Executing {node.name}...")
            exec_args = node.prepare_execution_args(inputs)
            result = await node.execute_async(**exec_args)
            future.set_success(result)
        except Exception as e:
            self.logger.error(f"[Async] Crash in {node.name}: {e}")
            future.set_error(e)

    def shutdown(self):
        self.logger.info("Initiating Graceful Shutdown...")
        self.running = False
        
        if self.bridge:
            try: self.bridge.set("_SYSTEM_SHUTDOWN", True, "Dispatcher")
            except: pass

        # Stop Async Loop
        if self.async_loop.is_running():
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            
        if self.async_thread.is_alive():
            self.async_thread.join(timeout=1.0)
            
        # Shutdown Pools
        self.logger.info("Shutting down Worker Pools...")
        self.native_executor.shutdown(wait=False)
        self.executor.shutdown(wait=False)

        # 5. Global Cleanup (Kill any orphans) — ONLY for root-level engines
        if not self.is_child:
            from synapse.utils.cleanup import CleanupManager
            CleanupManager.cleanup_all()

class FutureResult:
    """
    Sync primitive for Thread execution.
    """
    def __init__(self):
        self._event = threading.Event()
        self._error = None
        self._result = None
        
    def set_success(self, result=None):
        self._result = result
        self._event.set()
        
    def set_error(self, e):
        self._error = e
        self._event.set()
        
    def wait(self, timeout=None):
        self._event.wait(timeout)
        if self._error:
            raise self._error
        return self._result

    def result(self, timeout=None):
        return self.wait(timeout)

class PooledFuture:
    """
    Wrapper for concurrent.futures.Future to match Synapse interface.
    """
    def __init__(self, future):
        self.future = future
        
    def wait(self):
        # Result() blocks until done and re-raises exceptions
        return self.future.result()
