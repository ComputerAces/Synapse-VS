import threading
import queue
import time
import asyncio
from synapse.utils.logger import setup_logger

from concurrent.futures import ProcessPoolExecutor

def _run_node_task(node, inputs):
    """Helper to run node in pool worker."""
    # Ensure bridge is connected if passed in node?
    # Node logic should be self-contained or use shared manager proxy
    try:
        # If node has _run_wrapper, use it (BaseNode)
        if hasattr(node, '_run_wrapper'):
            return node._run_wrapper(**inputs)
        else:
            # Fallback
            exec_args = node.prepare_execution_args(inputs) if hasattr(node, 'prepare_execution_args') else inputs
            return node.execute(**exec_args)
    except Exception as e:
        # Log?
        raise e

class NodeDispatcher:
    """
    Decides HOW to run a node (Hybrid Execution Architecture).
    - Native/Safe: Runs in a dedicated Worker Thread.
    - Async/IO: Runs in a dedicated AsyncIO Event Loop Thread.
    - Heavy/Unsafe: Runs in a Process Pool (Warm Processes).
    """
    def __init__(self, bridge=None, is_child=False):
        self.logger = setup_logger("NodeDispatcher")
        self.native_queue = queue.Queue()
        self.running = True
        self.is_child = is_child
        
        self.bridge = bridge 
        
        # Native Sync Worker
        self.worker_thread = threading.Thread(target=self._worker_loop, name="SynapseNativeWorker", daemon=True)
        self.worker_thread.start()

        # AsyncIO Worker
        self.async_loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._async_loop_runner, name="SynapseAsyncWorker", daemon=True)
        self.async_thread.start()
        
        # Heavy Worker Pool
        # Use max_workers=None (defaults to CPU count)
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
        # Before executing the node, check if any provider in the stack overrides it.
        node_type = type(node).__name__
        handler_node_id = self.bridge.get_hijack_handler(context_stack, node_type)
        
        if handler_node_id:
            self.logger.info(f"Hijacking execution of {node.name} ({node_type}) via Provider {handler_node_id}")
            # [DELEGATION DESIGN]
            # In a full implementation, we would now signal the Provider Service
            # to handle this node's execution. For now, we tag the inputs 
            # so the node's execute() method can potentially handle the hijack internally 
            # if it's a 'plain client' aware of the stack.
            inputs["_hijack_provider_id"] = handler_node_id
            inputs["_is_hijacked"] = True

        # 1. Async Node
        if getattr(node, "is_async", False):
            future = FutureResult()
            # Schedule in the Async Loop
            asyncio.run_coroutine_threadsafe(self._execute_async_wrapper(node, inputs, future), self.async_loop)
            return future

        # 2. Native Node
        if getattr(node, "is_native", False):
            # Fast Track
            future = FutureResult()
            self.native_queue.put((node, inputs, future))
            return future
            
        # 3. Heavy/Process Node
        else:
            # Heavy Track (Pool)
            ft = self.executor.submit(_run_node_task, node, inputs)
            return PooledFuture(ft)
    
    async def _execute_async_wrapper(self, node, inputs, future):
        """Coroutine wrapper to execute node and update future."""
        try:
            self.logger.info(f"[Async] Executing {node.name}...")
            
            # Use shared preparation logic
            exec_args = node.prepare_execution_args(inputs)
            
            # Await the async execution
            result = await node.execute_async(**exec_args)
            
            # Set result (Thread-safe)
            future.set_success(result)
            
        except Exception as e:
            self.logger.error(f"[Async] Crash in {node.name}: {e}")
            future.set_error(e)

    def _worker_loop(self):
        self.logger.info("Native Worker Thread Started.")
        while self.running:
            try:
                # 1. Get Job
                task = self.native_queue.get()
                if task is None: break
                
                node, inputs, future = task
                
                # 2. Execute Safely
                try:
                    self.logger.info(f"[Native] Executing {node.name}...")
                    
                    # Use shared preparation logic
                    exec_args = node.prepare_execution_args(inputs)
                    
                    result = node.execute(**exec_args)
                    
                    future.set_success(result)
                except (BrokenPipeError, EOFError, ConnectionResetError):
                    self.running = False
                    break
                except Exception as e:
                    if "pipe is being closed" in str(e).lower():
                        self.running = False
                        break
                    self.logger.error(f"[Native] Crash in {node.name}: {e}")
                    future.set_error(e)
                finally:
                    self.native_queue.task_done()
                    
            except Exception as e:
                self.logger.critical(f"Worker Thread Crash: {e}")

    def shutdown(self):
        self.logger.info("Initiating Graceful Shutdown...")
        self.running = False
        self.native_queue.put(None)
        
        # 1. Signal Shutdown via Bridge (Soft Stop)
        if self.bridge:
            try: self.bridge.set("_SYSTEM_SHUTDOWN", True, "Dispatcher")
            except: pass

        # 2. Stop Async Loop
        if self.async_loop.is_running():
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            
        # 3. Wait for threads
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        if self.async_thread.is_alive():
            self.async_thread.join(timeout=1.0)
            
        # 4. Shutdown Pool
        self.logger.info("Shutting down Worker Pool...")
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
