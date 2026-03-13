import os

import json

import multiprocessing

import traceback

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.data import ErrorObject

from axonpulse.utils.namespace import generate_scoped_name, create_scoped_logger

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nParallel Runner Node.\n\nExecutes a subgraph (.syp) in parallel across multiple workers using\nmultiprocessing.Pool. Each worker gets a unique scoped name, isolated\nbridge, and runs a headless ExecutionEngine instance.\n'

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
    graph_data = payload['graph_data']
    item = payload['item']
    item_index = payload['item_index']
    scoped_name = payload['scoped_name']
    logger = create_scoped_logger(scoped_name)
    logger.info(f'Worker starting. Item: {repr(item)[:80]}')
    try:
        from axonpulse.core.bridge import AxonPulseBridge
        from axonpulse.core.engine import ExecutionEngine
        manager = multiprocessing.Manager()
        bridge = AxonPulseBridge(manager)
        bridge.set('_PARALLEL_ITEM', item, scoped_name)
        bridge.set('_PARALLEL_INDEX', item_index, scoped_name)
        bridge.set('_PARALLEL_WORKER', scoped_name, scoped_name)
        nodes = graph_data.get('nodes', [])
        start_node_id = None
        for node in nodes:
            node_type = node.get('type', '')
            if 'Start' in node_type:
                start_node_id = node.get('id')
                break
        if not start_node_id:
            raise RuntimeError('No Start Node found in subgraph.')
        engine = ExecutionEngine(bridge, headless=True, delay=0.0, trace=False)
        engine.load_graph(graph_data)
        engine.run(start_node_id)
        result = bridge.get('_GRAPH_RESULT', default=None)
        last_error = bridge.get('_SYSTEM_LAST_ERROR_MESSAGE', default=None)
        if last_error:
            logger.warning(f'Worker completed with error: {last_error}')
            return {'index': item_index, 'item': item, 'scoped_name': scoped_name, 'result': None, 'error': str(last_error), 'success': False}
        logger.info(f'Worker completed successfully.')
        return {'index': item_index, 'item': item, 'scoped_name': scoped_name, 'result': result, 'error': None, 'success': True}
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f'Worker crashed: {e}')
        return {'index': item_index, 'item': item, 'scoped_name': scoped_name, 'result': None, 'error': f'{e}\n{tb}', 'success': False}

@axon_node(category="Logic/Control Flow", version="2.3.0", node_label="Parallel Runner", outputs=['Error Flow', 'Results', 'Errors', 'Count'])
def ParallelRunnerNode(Items: list, Graph: str, Threads: float = 2, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Executes a subgraph in parallel across multiple worker processes.

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
- Errors: List of error details for failing items."""
    items = Items if Items is not None else kwargs.get('Items') or []
    if not items:
        _node.logger.error('Items must be a non-empty list.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        pass
    graph_path = Graph if Graph is not None else kwargs.get('Graph') or _node.properties.get('Graph', '')
    if not graph_path:
        _node.logger.error('No Graph path provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        pass
    if not os.path.isfile(graph_path):
        _node.logger.error(f"Graph file not found: '{graph_path}'")
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        pass
    thread_count = int(Threads if Threads is not None else kwargs.get('Threads') or _node.properties.get('Threads', 2))
    thread_count = max(1, min(thread_count, 32))
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
    except Exception as e:
        _node.logger.error(f'Error loading graph: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    _node.logger.info(f'Parallel Runner: {len(items)} items')
    active_names = set()
    base_name = _node.name.replace(' ', '_')
    payloads = []
    for (i, item) in enumerate(items):
        scoped_name = generate_scoped_name(base_name, i, active_names)
        payloads.append({'graph_data': graph_data, 'item': item, 'item_index': i, 'scoped_name': scoped_name})
    results_list = [None] * len(items)
    errors_list = []
    try:
        with multiprocessing.Pool(processes=thread_count) as pool:
            worker_results = pool.map(_worker_fn, payloads)
        for wr in worker_results:
            idx = wr['index']
            if wr['success']:
                results_list[idx] = wr['result']
            else:
                results_list[idx] = None
                errors_list.append(wr)
                _node.logger.warning(f"Worker {wr['scoped_name']} failed.")
    except Exception as e:
        _node.logger.error(f'Pool execution error: {e}')
        errors_list.append({'error': str(e)})
    finally:
        pass
    success_count = len(items) - len(errors_list)
    _node.logger.info(f'Complete: {success_count}/{len(items)} succeeded, {len(errors_list)} failed.')
    if errors_list:
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Results': results_list, 'Errors': errors_list, 'Count': len(items)}
