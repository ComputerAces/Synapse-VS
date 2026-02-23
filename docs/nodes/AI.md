# 🧠 AI Tools

AI Tools allow you to integrate Large Language Models (LLMs) into your workflows for text generation, analysis, and more.

## Nodes

### AI Models

**Version**: 2.0.2
**Description**: Retrieves the list of available models from the connected AI Provider.

Inputs:
- Flow: Trigger execution.

Outputs:
- Flow: Triggered after models are retrieved.
- Models: A list containing the names or IDs of available models.
- Count: The total number of available models found.

### Add Documents

**Version**: 2.0.2
**Description**: Indexes text documents into a connected Vector Database Provider.
Requires an Embedding Provider to generate vectors for the documents.

Inputs:
- Flow: Trigger execution.
- Documents: A list of text strings (or a single string) to be indexed.
- Metadata: Optional list of dictionaries containing metadata for each document.

Outputs:
- Flow: Triggered after indexing is complete.
- Success: True if the documents were successfully added, False otherwise.

### Anomaly Detection

**Version**: 2.0.2
**Description**: Identifies outliers or unusual data points within a numerical sequence using the Isolation Forest algorithm.
Useful for fraud detection, fault monitoring, and data cleaning.

Inputs:
- Flow: Trigger execution and model training.
- X List: A list of numerical values used to train the Isolation Forest model (requires at least 5 points).
- Predict X: The specific value to be tested for anomaly status.
- Contamination: The expected proportion of outliers in the data set (range: 0.0 to 0.5, default: 0.1).

Outputs:
- Flow: Triggered after detection is complete.
- Is Anomaly: True if the Predict X value is determined to be an outlier.
- Score: The anomaly score (lower values indicate more abnormal data).

### Ask AI

**Version**: 2.0.2
**Description**: Sends a prompt to a connected AI Provider and retrieves the generated response.
Supports file attachments, system instructions, and structured JSON output.

Inputs:
- Flow: Trigger execution.
- User Prompt: The main instruction or question for the AI.
- System Prompt: Background instructions to define the AI's behavior.
- Files: A list of file paths to be analyzed by the AI (if supported).
- Model: Override the default model of the provider.
- Return As JSON: If True, attempts to parse the AI's response as a JSON object.

Outputs:
- Flow: Triggered after the AI completes its response.
- Text: The raw text response from the AI.
- JSON: The extracted and parsed JSON data (if Return As JSON is enabled).
- JSON Error: Description of any errors encountered during JSON parsing.
- Error Flow: Triggered if the AI request or logic fails.

### BM25 Provider

**Version**: 2.0.2
**Description**: Service provider for BM25 (Best Matching 25) rank-based keyword search.
Operates as a local Vector Provider using lexical relevance.

Inputs:
- Flow: Start the BM25 service scope.
- Provider End: Close the service scope.
- Corpus: A list of text documents to index for searching.

Outputs:
- Provider Flow: Active while the provider service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Chunk String

**Version**: 2.0.2
**Description**: Uses an AI Provider to perform intelligent semantic chunking of input text.
If no AI Provider is available, it attempts to use a Chunking Provider or falls back to basic rules.

Inputs:
- Flow: Trigger execution.
- Text: The text string to be chunked.
- System Prompt: Instructions for the AI on how to perform chunking.

Outputs:
- Flow: Triggered after chunking is complete.
- Chunks: The resulting list of text chunks.
- Error Flow: Triggered if AI-based chunking fails.

### Chunking Provider

**Version**: 2.0.2
**Description**: Base class for nodes that provide text chunking strategies.
Registers a chunking strategy and optional configuration in the bridge.

Inputs:
- Flow: Trigger execution to register the provider.
- Text: Optional text to chunk immediately upon registration.

Outputs:
- Flow: Triggered after registration (and optional chunking) is complete.
- Chunks: The result of chunking the input text (if provided).

### FastEmbed Provider

**Version**: 2.0.2
**Description**: Service provider for local document embedding using the 'fastembed' library.
Highly optimized for CPU-based vector generation.

Inputs:
- Flow: Start resizing/embedding service scope.
- Provider End: Close the service scope.
- Model Name: The specific embedding model to load (e.g., 'BAAI/bge-small-en-v1.5').

Outputs:
- Provider Flow: Active while the embedding service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Fixed Size Chunking

**Version**: 2.0.2
**Description**: Splits text into chunks of a constant character length, with optional overlap.

Inputs:
- Flow: Trigger execution and register as a chunking provider.
- Text: Optional text to chunk immediately.
- ChunkSize: The desired length of each chunk in characters (default: 1000).
- OverlapSize: Number of characters to overlap between adjacent chunks (default: 200).

Outputs:
- Flow: Triggered after registration/chunking.
- Chunks: List of generated text chunks.

### Gemini Embeddings

**Version**: 2.0.2
**Description**: Service provider for Google's Gemini embedding models.
Generates high-quality vector representations of text for semantic search.

Inputs:
- Flow: Start the embedding service and enter the EMBED scope.
- Provider End: Close the service and exit the scope.
- API Key: Your Google Gemini API Key.

Outputs:
- Provider Flow: Active while the embedding service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Gemini Provider

**Version**: 2.0.2
**Description**: Service provider for Google's Gemini AI models.
Registers an AI capability scope for 'Ask AI' and other consumer nodes.

Inputs:
- Flow: Start the provider service and enter the AI scope.
- Provider End: Close the provider service and exit the scope.
- API Key: Your Google Gemini API Key.
- Model: The Gemini model ID to use (default: gemini-1.5-pro).

Outputs:
- Provider Flow: Active while the provider service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### LanceDB

**Version**: 2.0.2
**Description**: Service provider for LanceDB, a serverless, persistent vector database.
Stores and retrieves embedded vectors directly from local disk.

Inputs:
- Flow: Start the LanceDB service and enter the vector scope.
- Provider End: Close the database connection and exit the scope.
- Storage Path: Directory path where the database files are stored.
- Table Name: The specific collection/table to interact with.

Outputs:
- Provider Flow: Active while the database connection is open.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Language Detector

**Version**: 2.0.2
**Description**: Identifies the primary language and confidence level of a given text string.
Supports a wide variety of ISO language codes.

Inputs:
- Flow: Trigger the detection process.
- Text: The string to be identified.

Outputs:
- Flow: Triggered after detection is complete.
- Language Code: The ISO 639-1 language code of the detected language (e.g., 'en', 'fr', 'es').
- Confidence: Probability score representing the detector's certainty (0.0 to 1.0).

### Linear Regression

**Version**: 2.0.2
**Description**: Performs simple linear regression to predict a numerical value based on historical X-Y pairs.
Ideal for trend estimation and simple forecasting.

Inputs:
- Flow: Trigger the training and prediction process.
- X List: List of independent variable values (training features).
- Y List: List of dependent variable values (training targets).
- Predict X: The value for which to predict a corresponding Y.

Outputs:
- Flow: Triggered after prediction is complete.
- Predicted Y: The estimated value calculated by the linear model.

### Milvus

**Version**: 2.0.2
**Description**: Service provider for Milvus, a high-performance, cloud-native vector database.
Manages connections to standalone Milvus instances or Milvus Lite.

Inputs:
- Flow: Start the Milvus service and enter the vector scope.
- Provider End: Close the database connection and exit the scope.
- URI: The Milvus server address (e.g., 'http://localhost:19530').
- Token: Authentication token/password (if required).
- Collection Name: The target collection for search/add operations.

Outputs:
- Provider Flow: Active while the database connection is open.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Ollama Provider

**Version**: 2.0.2
**Description**: Service provider for locally hosted Ollama AI models.
Registers an AI capability scope for 'Ask AI' and other consumer nodes.

Inputs:
- Flow: Start the local service connection and enter the AI scope.
- Provider End: Close the connection and exit the scope.
- Host: URL of the Ollama API (default: http://localhost:11434).
- Model: The Ollama model name to use (default: llama3).
- Temperature: Creativity setting for the model (0.0 to 1.0).

Outputs:
- Provider Flow: Active while the provider service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### OpenAI Embeddings

**Version**: 2.0.2
**Description**: Service provider for OpenAI's text embedding models.
Converts text into dense vectors for high-accuracy similarity search.

Inputs:
- Flow: Start the embedding service and enter the EMBED scope.
- Provider End: Close the service and exit the scope.
- API Key: Your OpenAI API Key.

Outputs:
- Provider Flow: Active while the embedding service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### OpenAI Provider

**Version**: 2.0.2
**Description**: Service provider for OpenAI's GPT models (or OpenAI-compatible APIs).
Registers an AI capability scope for 'Ask AI' and other consumer nodes.

Inputs:
- Flow: Start the provider service and enter the AI scope.
- Provider End: Close the provider service and exit the scope.
- API Key: Your OpenAI API Key.
- Model: The GPT model ID to use (default: gpt-4o).
- Base URL: The API endpoint URL (allows usage with local models like LM Studio).

Outputs:
- Provider Flow: Active while the provider service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Paragraph Chunking

**Version**: 2.0.2
**Description**: Splits text into chunks based on paragraph boundaries (double newlines).

Inputs:
- Flow: Trigger execution and register as a chunking provider.
- Text: Optional text to chunk immediately.

Outputs:
- Flow: Triggered after registration/chunking.
- Chunks: List of generated paragraphs.

### Pinecone

**Version**: 2.0.2
**Description**: Service provider for Pinecone, a managed cloud-native vector database.
Enables high-scale similarity search and persistent storage for AI applications.

Inputs:
- Flow: Start the Pinecone service and enter the vector scope.
- Provider End: Close the database connection and exit the scope.
- API Key: Your Pinecone API Key.

Outputs:
- Provider Flow: Active while the database connection is open.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Semantic Chunking

**Version**: 2.0.2
**Description**: Splits text into semantic chunks by grouping paragraphs together up to a maximum size.

Inputs:
- Flow: Trigger execution and register as a chunking provider.
- Text: Optional text to chunk immediately.
- MaxChunkSize: The maximum allowed length for a combined chunk (default: 1000).

Outputs:
- Flow: Triggered after registration/chunking.
- Chunks: List of combined semantic chunks.

### Sentence Chunking

**Version**: 2.0.2
**Description**: Splits text into chunks based on sentence boundaries (. ! ?).

Inputs:
- Flow: Trigger execution and register as a chunking provider.
- Text: Optional text to chunk immediately.

Outputs:
- Flow: Triggered after registration/chunking.
- Chunks: List of generated sentences.

### Sentiment Analysis

**Version**: 2.0.2
**Description**: Analyzes the emotional tone of a text string using the VADER sentiment algorithm.
Detects if a statement is positive, negative, or neutral.

Inputs:
- Flow: Trigger the analysis process.
- Text: The string to be analyzed.

Outputs:
- Flow: Triggered after analysis is complete.
- Compound Score: A normalized score between -1 (extremely negative) and +1 (extremely positive).
- Is Positive: True if the text has a net positive sentiment.
- Is Negative: True if the text has a net negative sentiment.
- Is Neutral: True if the text is objectively neutral.

### TF-IDF Provider

**Version**: 2.0.2
**Description**: Service provider for TF-IDF (Term Frequency-Inverse Document Frequency) search.
Operates as a local Vector Provider using statistical relevance rankings.

Inputs:
- Flow: Start the TF-IDF service scope.
- Provider End: Close the service scope.
- Corpus: A list of text documents to index for searching.

Outputs:
- Provider Flow: Active while the provider service is running.
- Provider ID: Unique ID for this specific provider instance.
- Flow: Triggered when the service is stopped.

### Token Counter

**Version**: 2.0.2
**Description**: Calculates the number of tokens in a given string using the connected AI Provider.
If no provider is available, it uses a fallback heuristic estimation.

Inputs:
- Flow: Trigger execution.
- String: The text string to count tokens for.

Outputs:
- Flow: Triggered after counting is complete.
- Count: The estimated or exact number of tokens in the string.

### Vector Search

**Version**: 2.0.2
**Description**: Performs a semantic similarity search against a connected Vector Database Provider.
Automatically leverages an Embedding Provider to vectorize the query before searching.
Assumes a Provider Flow connection for both VECTOR and EMBED capabilities.

Inputs:
- Flow: Trigger the search operation.
- Query: The text string to search for.
- Limit: The maximum number of results to return (default: 5).

Outputs:
- Flow: Triggered after search is complete.
- Results: List of matching document text.
- Scores: List of similarity scores (0.0 to 1.0).
- Metadata: List of metadata dictionaries for each result.

---
[Back to Nodes Index](Index.md)
