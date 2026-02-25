import sys
import os
import subprocess
import importlib
import logging

logger = logging.getLogger(__name__)

class DependencyManager:
    """
    Manages lazy loading of heavy AI/Vector dependencies.
    """
    @staticmethod
    def check_dependencies():
        """Returns True if all vector dependencies are installed."""
        try:
            import fastembed
            import lancedb
            import pinecone
            import pymilvus
            import sklearn
            import rank_bm25
            return True
        except ImportError:
            return False

    @staticmethod
    def install_dependencies():
        """Attempts to install dependencies via pip."""
        print("Installing Vector Memory dependencies (fastembed, lancedb, pinecone-client, pymilvus, scikit-learn, rank-bm25)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "fastembed", "lancedb", "pinecone-client", "pymilvus", "scikit-learn", "rank-bm25"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False

class VectorProvider:
    """Abstract base class for Embedding Providers."""
    def embed_documents(self, texts):
        raise NotImplementedError

    def embed_query(self, text):
        raise NotImplementedError

class FastEmbedProvider(VectorProvider):
    """
    Concrete implementation using FastEmbed (ONNX Runtime).
    """
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        # Lazy import inside init to prevent startup crash if not installed
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        # returns generator, convert to list
        return list(self.model.embed(texts))

    def embed_query(self, text):
        result = list(self.model.embed([text]))
        return result[0]

class GeminiVectorProvider(VectorProvider):
    """
    Wrapper for Google Gemini Embeddings.
    """
    def __init__(self, api_key, model_name="models/embedding-001"):
        import google.generativeai as genai
        self.genai = genai
        self.model_name = model_name
        if not api_key:
             raise ValueError("Gemini API Key is required.")
        genai.configure(api_key=api_key)

    def embed_documents(self, texts):
        results = self.genai.embed_content(
            model=self.model_name,
            content=texts,
            task_type="retrieval_document"
        )
        return results['embedding']

    def embed_query(self, text):
        result = self.genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']

class OpenAIVectorProvider(VectorProvider):
    """
    Wrapper for OpenAI Embeddings.
    """
    def __init__(self, api_key, model_name="text-embedding-3-small"):
        from openai import OpenAI
        if not api_key:
             raise ValueError("OpenAI API Key is required.")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def embed_documents(self, texts):
        texts = [t.replace("\n", " ") for t in texts] # Best practice for OpenAI
        response = self.client.embeddings.create(input=texts, model=self.model_name)
        return [data.embedding for data in response.data]

    def embed_query(self, text):
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input=[text], model=self.model_name)
        return response.data[0].embedding

class TFIDFVectorProvider(VectorProvider):
    """
    Sparse vector provider using TF-IDF.
    Note: Requires fitting on a corpus before use.
    """
    def __init__(self, corpus=None):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer()
        if corpus:
            self.vectorizer.fit(corpus)

    def fit(self, corpus):
        self.vectorizer.fit(corpus)

    def embed_documents(self, texts):
        # Returns sparse matrix, converted to dense for compatibility
        return self.vectorizer.transform(texts).toarray().tolist()

    def embed_query(self, text):
        return self.vectorizer.transform([text]).toarray().tolist()[0]

class BM25VectorProvider(VectorProvider):
    """
    Sparse ranking provider using BM25.
    Note: BM25 is a ranking algorithm, not a true embedding.
    We return a tokenized representation or just use it as a dummy handle.
    """
    def __init__(self, corpus=None):
        from rank_bm25 import BM25Okapi
        self.model = None
        self.corpus = corpus
        if corpus:
            tokenized_corpus = [doc.split(" ") for doc in corpus]
            self.model = BM25Okapi(tokenized_corpus)

    def fit(self, corpus):
        self.corpus = corpus
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        from rank_bm25 import BM25Okapi
        self.model = BM25Okapi(tokenized_corpus)

    def embed_documents(self, texts):
        # Mock embeddings for compatibility
        return [[0.0]] * len(texts)

    def embed_query(self, text):
        return [0.0]
        
    def get_scores(self, query, corpus=None):
        if not self.model and corpus:
            self.fit(corpus)
        if not self.model: return []
        tokenized_query = query.split(" ")
        return self.model.get_scores(tokenized_query).tolist()

class BaseVectorDatabase:
    """Abstract Interface for Vector DBs."""
    def add(self, table_name, documents, embeddings, metadata=None):
        raise NotImplementedError
    
    def search(self, table_name, query_vector, limit=5):
        raise NotImplementedError

class LanceDBVectorDatabase(BaseVectorDatabase):
    """
    Wrapper for LanceDB.
    """
    def __init__(self, path="./data/vectors"):
        import lancedb
        if not os.path.exists(path):
            os.makedirs(path)
        self.db = lancedb.connect(path)

    def add(self, table_name, documents, embeddings, metadata=None):
        data = []
        for i, doc in enumerate(documents):
            entry = {
                "vector": embeddings[i],
                "text": doc,
                "id": str(i)
            }
            if metadata and i < len(metadata):
                entry.update(metadata[i])
            data.append(entry)
            
        if not data: return 0

        if table_name in self.db.table_names():
            tbl = self.db.open_table(table_name)
            tbl.add(data)
        else:
            self.db.create_table(table_name, data=data)
        return len(data)

    def search(self, table_name, query_vector, limit=5):
        if table_name not in self.db.table_names():
            return [], [], []
            
        tbl = self.db.open_table(table_name)
        results = tbl.search(query_vector).limit(limit).to_list()
        
        docs = []
        scores = []
        metas = []
        
        for r in results:
            docs.append(r.get("text", ""))
            scores.append(r.get("_distance", 0.0))
            m = {k:v for k,v in r.items() if k not in ["vector", "text", "_distance", "id"]}
            metas.append(m)
            
        return docs, scores, metas

class PineconeVectorDatabase(BaseVectorDatabase):
    """
    Wrapper for Pinecone.
    """
    def __init__(self, api_key, index_name="synapse-memory", namespace="default"):
        from pinecone import Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        self.namespace = namespace

    def add(self, table_name, documents, embeddings, metadata=None):
        # table_name is ignored or used as namespace override if needed
        # We use self.namespace usually. But let's respect table_name as namespace if provided?
        # Standardizing: table_name = namespace
        target_ns = table_name if table_name else self.namespace
        
        vectors = []
        import uuid
        for i, doc in enumerate(documents):
            meta = {"text": doc}
            if metadata and i < len(metadata):
                meta.update(metadata[i])
            
            # Pinecone needs ID
            vid = str(uuid.uuid4())
            vectors.append({
                "id": vid,
                "values": embeddings[i],
                "metadata": meta
            })
            
        self.index.upsert(vectors=vectors, namespace=target_ns)
        return len(vectors)

    def search(self, table_name, query_vector, limit=5):
        target_ns = table_name if table_name else self.namespace
        
        results = self.index.query(
            namespace=target_ns,
            vector=query_vector,
            top_k=int(limit),
            include_values=False,
            include_metadata=True
        )
        
        docs = []
        scores = []
        metas = []
        
        for match in results.matches:
            docs.append(match.metadata.get("text", ""))
            scores.append(match.score)
            metas.append(match.metadata)
            
        return docs, scores, metas

class MilvusVectorDatabase(BaseVectorDatabase):
    """
    Wrapper for Milvus.
    """
    def __init__(self, uri="http://localhost:19530", token=""):
        from pymilvus import MilvusClient
        self.client = MilvusClient(uri=uri, token=token)

    def add(self, table_name, documents, embeddings, metadata=None):
        # table_name = collection_name
        data = []
        for i, doc in enumerate(documents):
            entry = {
                "vector": embeddings[i],
                "text": doc,
                # Milvus usually needs an ID or auto-id. 
                # If we use MilvusClient helpers, it simplifies things.
                # using auto-id schema is best.
            }
            if metadata and i < len(metadata):
                entry.update(metadata[i])
            data.append(entry)

        # Check collection
        if not self.client.has_collection(table_name):
            # Create simple collection
            # Dim check? We don't know dim here. 
            # Milvus requires dim at creation.
            # We can infer from first embedding
            dim = len(embeddings[0])
            self.client.create_collection(
                collection_name=table_name,
                dimension=dim,
                auto_id=True
            )
            
        res = self.client.insert(collection_name=table_name, data=data)
        return res["insert_count"]

    def search(self, table_name, query_vector, limit=5):
        if not self.client.has_collection(table_name):
            return [], [], []
            
        res = self.client.search(
            collection_name=table_name,
            data=[query_vector],
            limit=int(limit),
            output_fields=["text", "*"] # Fetch all
        )
        
        # Res is list of list of dicts
        hits = res[0]
        
        docs = []
        scores = []
        metas = []
        
        for hit in hits:
            entity = hit.get("entity", {})
            docs.append(entity.get("text", ""))
            scores.append(hit.get("distance", 0.0))
            # Metas
            m = {k:v for k,v in entity.items() if k not in ["vector", "text"]}
            metas.append(m)
            
        return docs, scores, metas
