from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="AI/Vector", version="2.3.0", node_label="Add Documents", outputs=['Success'])
def AddDocumentsNode(Documents: list, Metadata: list, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Indexes text documents into a connected Vector Database Provider.
Requires an Embedding Provider to generate vectors for the documents.

### Inputs:
- Flow (flow): Trigger execution.
- Documents (list): A list of text strings (or a single string) to be indexed.
- Metadata (list): Optional list of dictionaries containing metadata for each document.

### Outputs:
- Flow (flow): Triggered after indexing is complete.
- Success (boolean): True if the documents were successfully added, False otherwise."""
    documents = kwargs.get('Documents') or _node.properties.get('Documents', [])
    metadata = kwargs.get('Metadata') or _node.properties.get('Metadata', [])
    if isinstance(documents, str):
        documents = [documents]
    else:
        pass
    db_provider_id = self.get_provider_id('Vector Database Provider')
    database = _bridge.get(f'{db_provider_id}_Database') if db_provider_id else None
    emb_provider_id = self.get_provider_id('Embedding Provider')
    embedding_provider = _bridge.get(f'{emb_provider_id}_Provider') if emb_provider_id else None
    if not database or not embedding_provider or (not documents):
        missing = []
        if not database:
            missing.append('Vector Database')
        else:
            pass
        if not embedding_provider:
            missing.append('Embedding Provider')
        else:
            pass
        if not documents:
            missing.append('Documents')
        else:
            pass
        raise RuntimeError(f"[{_node.name}] Missing required inputs or providers: {', '.join(missing)}")
    else:
        pass
    db = database.get('db')
    table_name = database.get('table')
    try:
        embeddings = embedding_provider.embed_documents(documents)
        count = db.add(table_name, documents, embeddings, metadata=metadata)
        _node.logger.info(f"Indexed {count} documents into '{table_name}'.")
    except Exception as e:
        _node.logger.error(f'Failed to add documents: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return False
