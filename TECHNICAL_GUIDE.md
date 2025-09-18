# CrossCheck Technical Implementation Guide

## Overview

CrossCheck is a Retrieval-Augmented Generation (RAG) system designed for journalists to analyze documents using AI. This comprehensive guide explains the complete technical pipeline from document upload to AI-generated responses, with detailed focus on vector operations and troubleshooting.

## Architecture Overview

```
User Upload → Document Processing → Embedding Generation → Vector Storage → Query Processing → AI Response
     ↓              ↓                      ↓                   ↓               ↓              ↓
  Streamlit     Text Extraction        SentenceTransformers    FAISS        Similarity      DeepSeek V3
    UI         + Chunking              (all-MiniLM-L6-v2)     Index         Search         via OpenRouter
```

## Complete Data Flow Pipeline

### Phase 1: Document Upload & Processing

#### 1.1 File Upload (Streamlit UI → FastAPI)
```python
# User uploads file through Streamlit sidebar
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])

# Streamlit sends file to FastAPI /upload endpoint
files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
response = requests.post(f"{API_BASE_URL}/upload", files=files)
```

**What happens:**
- User selects a file in the Streamlit interface
- File is uploaded to FastAPI backend via HTTP POST
- FastAPI saves the file to the `data/uploads/` directory with timestamp prefix
- Database record is created in `documents` table with metadata

#### 1.2 Text Extraction (`document_processor.py`)
```python
def extract_text(self, file_path: str) -> str:
    file_extension = Path(file_path).suffix.lower()
    
    if file_extension == '.pdf':
        return self.extract_text_from_pdf(file_path)  # Uses PyPDF2
    elif file_extension == '.docx':
        return self.extract_text_from_docx(file_path)  # Uses python-docx
    elif file_extension == '.txt':
        return self.extract_text_from_txt(file_path)  # Direct file read
```

**What happens:**
- System determines file type by extension
- Appropriate parser extracts raw text content
- Text is cleaned and normalized for processing

#### 1.3 Document Chunking (Critical for RAG Performance)
```python
def create_chunks(self, text: str, doc_id: int, filename: str) -> List[Dict[str, Any]]:
    # Token-based chunking with sentence awareness
    sentences = self._split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = len(sentence.split())
        
        # Check if adding this sentence would exceed chunk size
        if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
            # Create chunk from current sentences
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'document_id': doc_id,
                    'filename': filename,
                    'chunk_index': len(chunks),
                    'estimated_tokens': current_tokens,
                    'sentence_count': len(current_chunk)
                }
            })
            
            # Start new chunk with overlap
            overlap_sentences = current_chunk[-self.chunk_overlap:]
            current_chunk = overlap_sentences + [sentence]
            current_tokens = sum(len(s.split()) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
```

**Key Chunking Concepts:**
- **Chunk Size**: 500 tokens (configurable via `CHUNK_SIZE`)
- **Overlap**: 100 tokens between chunks (configurable via `CHUNK_OVERLAP`)
- **Sentence Awareness**: Chunks break at sentence boundaries to maintain semantic coherence
- **Metadata**: Each chunk carries document ID, filename, position, and statistics

**Why Chunking Matters:**
- **LLM Context Limits**: Large documents exceed token limits
- **Retrieval Precision**: Smaller chunks allow more precise matching
- **Semantic Coherence**: Sentence-aware splitting preserves meaning
- **Overlap**: Ensures important information isn't lost at chunk boundaries

### Phase 2: Embedding Generation & Vector Storage

#### 2.1 Embedding Generation (`embedding_service.py`)
```python
def encode_chunks(self, chunks: List[Dict[str, Any]]) -> List[np.ndarray]:
    """Convert text chunks into high-dimensional vectors."""
    texts = [chunk['text'] for chunk in chunks]
    
    # Generate embeddings using SentenceTransformers
    embeddings = self.model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )
    
    return embeddings  # Shape: (num_chunks, 384)
```

**Embedding Model Details:**
- **Model**: `all-MiniLM-L6-v2` (SentenceTransformers)
- **Dimensions**: 384-dimensional vectors
- **Advantages**: Fast inference, good semantic understanding, multilingual
- **Output**: Each text chunk becomes a 384-dimensional vector representing its semantic meaning

**Vector Representation:**
```python
# Example: "Climate change is accelerating" becomes:
# array([0.123, -0.456, 0.789, ..., 0.234])  # 384 numbers
```

#### 2.2 Vector Storage Architecture (`vector_store.py`)

**Critical Design Decision: Document Isolation**
```python
class VectorStore:
    def __init__(self):
        # Separate FAISS index per document for isolation
        self.document_indices = {}  # {doc_id: {'index': faiss_index, 'metadata': {}, 'dimension': 384}}
```

**Why Document Isolation?**
- **Data Integrity**: Prevents content mixing between documents
- **Selective Querying**: Can search within specific documents
- **Clean Deletion**: Can remove document without affecting others
- **Debugging**: Easier to troubleshoot document-specific issues

#### 2.3 FAISS Index Operations

**Adding Vectors to Document Index:**
```python
def add_document_vectors(self, document_id: int, vectors: np.ndarray, metadata_list: List[Dict]):
    # Create or get existing document index
    if document_id not in self.document_indices:
        # Initialize new FAISS index for this document
        dimension = vectors.shape[1]  # 384 for all-MiniLM-L6-v2
        index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        
        self.document_indices[document_id] = {
            'index': index,
            'metadata': {},
            'dimension': dimension
        }
    
    # Add vectors to the document's index
    doc_data = self.document_indices[document_id]
    current_size = doc_data['index'].ntotal
    
    # Normalize vectors for cosine similarity
    faiss.normalize_L2(vectors)
    doc_data['index'].add(vectors)
    
    # Store metadata for each vector
    for i, metadata in enumerate(metadata_list):
        vector_id = current_size + i
        doc_data['metadata'][vector_id] = metadata
    
    # Persist to disk for server restart resilience
    self.save_document_index(document_id)
```

**FAISS Index Types:**
- **IndexFlatIP**: Inner Product similarity (cosine after L2 normalization)
- **Exact Search**: No approximation, perfect recall
- **Memory Efficient**: Suitable for single-document RAG

#### 2.4 Persistence Layer (Critical for Production)
```python
def save_document_index(self, document_id: int):
    """Save FAISS index and metadata to disk."""
    save_path = f"{self.index_path}_doc_{document_id}"
    
    # Save FAISS index binary
    faiss.write_index(doc_data['index'], f"{save_path}.faiss")
    
    # Save metadata as pickle
    with open(f"{save_path}.metadata", 'wb') as f:
        pickle.dump({
            'metadata': doc_data['metadata'],
            'dimension': doc_data['dimension']
        }, f)

def load_all_document_indices(self):
    """Load all document indices on server startup."""
    for filename in os.listdir(embeddings_dir):
        if filename.endswith('.faiss') and '_doc_' in filename:
            doc_id = int(filename.split('_doc_')[1].split('.')[0])
            self.load_document_index(doc_id)
```

**Why Persistence Matters:**
- **Server Restarts**: Vector indices survive application restarts
- **Development**: Code changes don't require re-embedding
- **Performance**: Avoid expensive re-computation
- **Data Safety**: Indices are backed up to disk

### Phase 3: Query Processing & Retrieval

#### 3.1 Query Embedding
```python
def query_document(self, user_input: str, document_id: int):
    # Convert user query to same vector space as document chunks
    query_embedding = self.embedding_service.encode_text(user_input)
    # Shape: (384,) - same dimensions as document chunks
```

#### 3.2 Similarity Search
```python
def search_document(self, document_id: int, query_vector: np.ndarray, k: int = 5):
    # Ensure document index is loaded
    if document_id not in self.document_indices:
        if not self.load_document_index(document_id):
            return []  # No index found
    
    doc_data = self.document_indices[document_id]
    
    # Normalize query vector for cosine similarity
    query_vector = query_vector.reshape(1, -1).astype('float32')
    faiss.normalize_L2(query_vector)
    
    # Perform similarity search
    similarities, indices = doc_data['index'].search(query_vector, k)
    
    # Convert results to readable format
    results = []
    for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
        if idx == -1:  # FAISS returns -1 for empty slots
            continue
            
        metadata = doc_data['metadata'].get(int(idx), {})
        results.append({
            'vector_id': int(idx),
            'distance': float(1.0 - similarity),  # Convert similarity to distance
            'similarity': float(similarity),      # Cosine similarity score
            'metadata': metadata,
            'document_id': document_id
        })
    
    return results
```

**Similarity Search Deep Dive:**
- **Cosine Similarity**: Measures angle between vectors (semantic similarity)
- **L2 Normalization**: Ensures cosine similarity calculation
- **Top-K Retrieval**: Returns most relevant chunks
- **Similarity Scores**: Range from 0 (unrelated) to 1 (identical)

#### 3.3 Context Construction
```python
def _generate_flexible_response(self, user_input: str, context_chunks: List[Dict]):
    # Build context from retrieved chunks
    context_texts = []
    for i, chunk in enumerate(context_chunks, 1):
        metadata = chunk.get('metadata', {})
        text = metadata.get('text', '')
        chunk_idx = metadata.get('chunk_index', i)
        
        context_texts.append(f"[Chunk {chunk_idx}]: {text}")
    
    context = "\n\n".join(context_texts)
```

### Phase 4: AI Response Generation

#### 4.1 Flexible Prompt Engineering
```python
# Detect if input is a question or statement
is_question = user_input.strip().endswith('?') or any(
    user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which']
)

# Adaptive system prompt
system_prompt = """You are a journalism assistant specialized in document analysis. 
Using ONLY the provided document excerpts, respond appropriately to the user input.

- If the input is a question, answer it clearly and comprehensively.
- If the input is a topic or statement, provide a relevant summary or analysis.
- Always cite specific chunks (e.g., "According to Chunk 1...") for each claim.
- If the excerpts don't contain enough information, say so clearly."""

if is_question:
    user_prompt = f"""Question: {user_input}

Document Excerpts:
{context}

Please provide a comprehensive answer based on the document excerpts above."""
else:
    user_prompt = f"""Topic/Statement: {user_input}

Document Excerpts:
{context}

Please provide relevant information or analysis based on the document excerpts above."""
```

#### 4.2 LLM API Integration (OpenRouter)
```python
# API call to DeepSeek V3 via OpenRouter
response = requests.post(
    f"{self.base_url}/chat/completions",
    headers={
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
)
```

## Common Issues & Troubleshooting

### Issue 1: Mixed Document Content in Responses
**Symptoms:**
- AI mentions content from multiple documents when querying single document
- Responses contain information not in the uploaded document

**Root Cause:**
- Vector indices not properly isolated by document
- Old indices not cleared when documents are deleted/replaced

**Debug Steps:**
```bash
# Check what's in the database
sqlite3 ./data/journalism.db "SELECT id, filename FROM documents;"

# Check vector index files
ls -la ./data/embeddings/

# Check chunk content
sqlite3 ./data/journalism.db "SELECT content FROM chunks WHERE document_id=1 LIMIT 3;"
```

**Solution:**
```bash
# Clear all data and start fresh
rm -rf ./data/embeddings/* ./data/journalism.db
# Re-upload documents
```

### Issue 2: "No Answer Generated"
**Symptoms:**
- Backend logs show successful API calls
- Frontend displays "No answer generated"

**Root Cause:**
- Frontend/backend response format mismatch
- API wrapper adding extra data layers

**Debug Steps:**
- Check backend logs for `LLM response success: True`
- Verify API response structure in `app.py`

**Solution:**
- Ensure frontend directly returns API response without wrapping

### Issue 3: Vector Store Not Persisting
**Symptoms:**
- Documents need re-upload after server restart
- "No index found for document X" warnings

**Root Cause:**
- Indices not saved to disk
- Indices not loaded on startup

**Debug Steps:**
```python
# Check if indices are being saved
logger.info(f"Saving document {document_id} index to {save_path}")

# Check if indices are being loaded
logger.info(f"Loaded document {document_id} index from {load_path}")
```

### Issue 4: Poor Similarity Scores
**Symptoms:**
- Low similarity scores (< 0.3) for relevant content
- Irrelevant chunks being retrieved

**Potential Causes:**
- Query and document language mismatch
- Very short queries or chunks
- Domain-specific terminology

**Solutions:**
- Use more specific queries
- Adjust chunk size and overlap
- Consider domain-specific embedding models

## Performance Optimization

### Vector Search Optimization
```python
# For larger datasets, consider approximate search
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
index.nprobe = 10  # Search 10 clusters instead of all
```

### Memory Management
```python
# Monitor vector store memory usage
def get_memory_usage(self):
    total_vectors = sum(data['index'].ntotal for data in self.document_indices.values())
    memory_mb = total_vectors * self.dimension * 4 / (1024 * 1024)  # float32 = 4 bytes
    return memory_mb
```

### Batch Processing
```python
# Process multiple documents efficiently
def process_documents_batch(self, documents: List[str]):
    all_texts = []
    metadata = []
    
    for doc in documents:
        chunks = self.create_chunks(doc)
        all_texts.extend([c['text'] for c in chunks])
        metadata.extend(chunks)
    
    # Generate embeddings in batch for efficiency
    embeddings = self.embedding_service.encode_texts(all_texts)
```

## Configuration Guide

### Environment Variables (.env)
```bash
# Required
OPENROUTER_API_KEY=your_actual_api_key_here

# Optional with defaults
DATABASE_URL=sqlite:///./data/journalism.db
FAISS_INDEX_PATH=./data/embeddings/faiss_index
UPLOAD_DIR=./data/uploads
CHUNKS_DIR=./data/chunks
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=deepseek/deepseek-chat
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# RAG Parameters
CHUNK_SIZE=500
CHUNK_OVERLAP=100
MAX_RETRIEVED_DOCS=5
TEMPERATURE=0.7
```

### Model Selection Trade-offs

#### Embedding Models:
- **all-MiniLM-L6-v2**: Fast, 384-dim, good general performance
- **all-mpnet-base-v2**: Slower, 768-dim, better accuracy
- **text-embedding-ada-002**: OpenAI, 1536-dim, best quality but paid

#### LLM Models:
- **deepseek/deepseek-chat**: Good balance of quality and cost
- **gpt-4**: Highest quality, more expensive
- **claude-3-sonnet**: Good reasoning, moderate cost

## Extending the System

### Adding New Document Types
```python
def extract_text_from_csv(self, file_path: str) -> str:
    import pandas as pd
    df = pd.read_csv(file_path)
    return df.to_string()

# Register in extract_text method
elif file_extension == '.csv':
    return self.extract_text_from_csv(file_path)
```

### Multi-Document Querying
```python
def query_multiple_documents(self, user_input: str, document_ids: List[int]):
    all_chunks = []
    for doc_id in document_ids:
        chunks = self.vector_store.search_document(doc_id, query_embedding, k=3)
        all_chunks.extend(chunks)
    
    # Sort by similarity and take top results
    all_chunks.sort(key=lambda x: x['similarity'], reverse=True)
    return all_chunks[:self.max_retrieved_docs]
```

### Advanced Chunking Strategies
```python
def create_semantic_chunks(self, text: str):
    """Chunk by semantic similarity instead of fixed size."""
    sentences = self._split_into_sentences(text)
    embeddings = self.embedding_service.encode_texts(sentences)
    
    # Group sentences with high similarity
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        similarity = cosine_similarity(embeddings[i-1], embeddings[i])
        if similarity > 0.8:  # High similarity threshold
            current_chunk.append(sentences[i])
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
    
    return chunks
```

## Monitoring & Logging

### Key Metrics to Track
```python
# Vector store statistics
{
    "total_documents": len(self.document_indices),
    "total_vectors": sum(data['index'].ntotal for data in self.document_indices.values()),
    "memory_usage_mb": self.get_memory_usage(),
    "average_similarity_scores": self.get_average_similarities()
}

# Query performance
{
    "query_latency_ms": time.time() - start_time,
    "chunks_retrieved": len(relevant_chunks),
    "llm_response_length": len(response),
    "api_usage_tokens": response.get('usage', {})
}
```

### Debug Logging
```python
# Enable detailed logging
logging.getLogger('backend.services.vector_store').setLevel(logging.DEBUG)
logging.getLogger('backend.services.rag_service').setLevel(logging.DEBUG)
```

This technical guide provides a comprehensive understanding of the CrossCheck RAG system, from basic concepts to advanced troubleshooting. The vector storage architecture and document isolation patterns are critical for maintaining data integrity in multi-document scenarios.