from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="AI/Vector", version="2.3.0", node_label="Vector Search", outputs=['Results', 'Scores', 'Metadata'])
def VectorSearchNode(Query: str, Limit: float = 5, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a semantic similarity search against a connected Vector Database Provider.
Automatically leverages an Embedding Provider to vectorize the query before searching.
Assumes a Provider Flow connection for both VECTOR and EMBED capabilities.

### Inputs:
- Flow (flow): Trigger the search operation.
- Query (string): The text string to search for.
- Limit (integer): The maximum number of results to return (default: 5).

### Outputs:
- Flow (flow): Triggered after search is complete.
- Results (list): List of matching document text.
- Scores (list): List of similarity scores (0.0 to 1.0).
- Metadata (list): List of metadata dictionaries for each result."""
    query = kwargs.get('Query') or _node.properties.get('Query')
    limit = kwargs.get('Limit') or _node.properties.get('Limit', 5)
    db_provider_id = self.get_provider_id('Vector Database Provider')
    database = _bridge.get(f'{db_provider_id}_Database') if db_provider_id else None
    emb_provider_id = self.get_provider_id('Embedding Provider')
    embedding_provider = _bridge.get(f'{emb_provider_id}_Provider') if emb_provider_id else None
    if not database or not embedding_provider or (not query):
        missing = []
        if not database:
            missing.append('Vector Database')
        else:
            pass
        if not embedding_provider:
            missing.append('Embedding Provider')
        else:
            pass
        if not query:
            missing.append('Query')
        else:
            pass
        raise RuntimeError(f"[{_node.name}] Missing required inputs or providers: {', '.join(missing)}")
    else:
        pass
    db = database.get('db')
    table_name = database.get('table')
    try:
        query_vec = embedding_provider.embed_query(str(query))
        (docs, scores, metas) = db.search(table_name, query_vec, limit=int(limit))
        _node.logger.info(f'Vector search returned {len(docs)} results.')
    except Exception as e:
        _node.logger.error(f'Search Failed: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Results': docs, 'Scores': scores, 'Metadata': metas}
