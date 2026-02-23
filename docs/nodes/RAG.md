# 🧬 Vector Database (RAG)

Nodes for Retrieval-Augmented Generation (RAG), text embeddings, and semantic search.

## Nodes

### Embedding Providers

**Nodes**: `FastEmbed Provider`, `Gemini Embeddings`, `OpenAI Embeddings`.
**Description**: Configures local or cloud-based engines to convert text into numerical vectors.

### Databases

**Nodes**: `LanceDB`, `Pinecone`, `Milvus`.
**Description**: Connects to local or cloud vector stores to index and search embeddings.

### Core Operations

**Nodes**: `Vector Add`, `Vector Search`.
**Description**: Indexes documents into a database or searches for semantically similar content.

### Pre-processing

**Nodes**: `File Chunk`, `Deconstruct Vector Result`.
**Description**: Splits large text files into manageable pieces for indexing and extracts fields from search results.

---
[Back to Nodes Index](Index.md)
