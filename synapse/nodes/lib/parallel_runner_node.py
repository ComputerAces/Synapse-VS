"""
Parallel Runner Node.

Executes a subgraph (.syp) in parallel across multiple workers using
multiprocessing.Pool. Each worker gets a unique scoped name, isolated
bridge, and runs a headless ExecutionEngine instance.
"""
import os
import json
import multiprocessing
import traceback
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.data import ErrorObject
from synapse.utils.namespace import generate_scoped_name, create_scoped_logger


def _worker_fn(payload):
    """
    Module-level worker function (must be picklable).
    
    Runs a headless ExecutionEngine with the given graph data
    and a single item injected as _PARALLEL_ITEM.
    
    Args:
        payload: dict with keys:
            - graph_data:  The parsed .syp JSON dict.
            - item:        The single item from the batch list.
            - item_index:  Index of this item in the original list.
            - scoped_name: Unique worker name (e.g., "Worker_0_A2B3").
    
    Returns:
        dict with: { "index", "item", "scoped_name", "result", "success" }
    """
    graph_data = payload["graph_data"]
    item = payload["item"]
    item_index = payload["item_index"]
    scoped_name = payload["scoped_name"]

    logger = create_scoped_logger(scoped_name)
    logger.info(f"Worker starting. Item: {repr(item)[:80]}")

    try:
        # Import here to avoid circular imports at module level
        from synapse.core.bridge import SynapseBridge
        from synapse.core.engine import ExecutionEngine

        # Create isolated manager + bridge for this worker
        manager = multiprocessing.Manager()
        bridge = SynapseBridge(manager)

        # Inject the item and worker metadata
        bridge.set("_PARALLEL_ITEM", item, scoped_name)
        bridge.set("_PARALLEL_INDEX", item_index, scoped_name)
        bridge.set("_PARALLEL_WORKER", scoped_name, scoped_name)

        # Find the start node
        nodes = graph_data.get("nodes", [])
        start_node_id = None
        for node in nodes:
            node_type = node.get("type", "")
            if "Start" in node_type:
                start_node_id = node.get("id")
                break

        if not start_node_id:
            raise RuntimeError("No Start Node found in subgraph.")

        # Create and run headless engine
        engine = ExecutionEngine(
            bridge,
            headless=True,
            delay=0.0,
            trace=False
        )

        # Load graph topology
        engine.load_graph(graph_data)

        # Run
        engine.run(start_node_id)

        # Collect result: check for Return node output
        result = bridge.get("_GRAPH_RESULT", default=None)
        
        # Also collect any last error
        last_error = bridge.get("_SYSTEM_LAST_ERROR_MESSAGE", default=None)
        
        if last_error:
            logger.warning(f"Worker completed with error: {last_error}")
            return {
                "index": item_index,
                "item": item,
                "scoped_name": scoped_name,
                "result": None,
                "error": str(last_error),
                "success": False
            }

        logger.info(f"Worker completed successfully.")
        return {
            "index": item_index,
            "item": item,
            "scoped_name": scoped_name,
            "result": result,
            "error": None,
            "success": True
        }

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Worker crashed: {e}")
        return {
            "index": item_index,
            "item": item,
            "scoped_name": scoped_name,
            "result": None,
            "error": f"{e}\n{tb}",
            "success": False
        }


@NodeRegistry.register("Parallel Runner", "Logic/Control Flow")
class ParallelRunnerNode(SuperNode):
    """
    Executes a subgraph in parallel across multiple worker processes.
    
    Takes a list of 'Items' and a '.syp' graph file, spinning up 
    a process pool to execute the graph for each item. Results are 
    aggregated into a single list once all workers complete.
    
    Inputs:
    - Flow: Trigger the parallel batch.
    - Items: The list of data points to process.
    - Graph: Path to the .syp subgraph file.
    - Threads: Maximum number of parallel workers.
    
    Outputs:
    - Flow: Triggered if all workers complete successfully.
    - Error Flow: Triggered if any worker fails or a crash occurs.
    - Results: List of return values from each execution.
    - Errors: List of error details for failing items.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = False  # Heavy: runs in process pool context
        self.properties["Threads"] = 2
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.run_parallel)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Items": DataType.LIST,
            "Graph": DataType.STRING,
            "Threads": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Results": DataType.LIST,
            "Errors": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def run_parallel(self, Items=None, Graph=None, Threads=None, **kwargs):
        # Validate inputs
        # BaseNode/SuperNode registers inputs, but if they are None, fallback to properties?
        # Items is required.
        # NOTE: register_handler passes kwargs with Input names.
        
        items = Items if Items is not None else kwargs.get("Items") or []
        if not items:
            self.logger.error("Items must be a non-empty list.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        graph_path = Graph if Graph is not None else kwargs.get("Graph") or self.properties.get("Graph", "")
        if not graph_path:
            self.logger.error("No Graph path provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        if not os.path.isfile(graph_path):
            self.logger.error(f"Graph file not found: '{graph_path}'")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        thread_count = int(Threads if Threads is not None else kwargs.get("Threads") or self.properties.get("Threads", 2))
        thread_count = max(1, min(thread_count, 32))  # Clamp 1-32

        # Load graph data
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading graph: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        self.logger.info(f"Parallel Runner: {len(items)} items")

        # Generate scoped names
        active_names = set()
        base_name = self.name.replace(" ", "_")

        # Build payloads
        payloads = []
        for i, item in enumerate(items):
            scoped_name = generate_scoped_name(base_name, i, active_names)
            payloads.append({
                "graph_data": graph_data,
                "item": item,
                "item_index": i,
                "scoped_name": scoped_name
            })

        # Execute in pool
        results_list = [None] * len(items)
        errors_list = []

        try:
            with multiprocessing.Pool(processes=thread_count) as pool:
                worker_results = pool.map(_worker_fn, payloads)

            # Aggregate results
            for wr in worker_results:
                idx = wr["index"]
                if wr["success"]:
                    results_list[idx] = wr["result"]
                else:
                    results_list[idx] = None
                    errors_list.append(wr)
                    self.logger.warning(f"Worker {wr['scoped_name']} failed.")

        except Exception as e:
            self.logger.error(f"Pool execution error: {e}")
            errors_list.append({"error": str(e)})

        # Set outputs
        self.bridge.set(f"{self.node_id}_Results", results_list, self.name)
        self.bridge.set(f"{self.node_id}_Errors", errors_list, self.name)
        self.bridge.set(f"{self.node_id}_Count", len(items), self.name)

        success_count = len(items) - len(errors_list)
        self.logger.info(f"Complete: {success_count}/{len(items)} succeeded, {len(errors_list)} failed.")

        if errors_list:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        else:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
