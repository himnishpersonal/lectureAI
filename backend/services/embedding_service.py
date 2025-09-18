"""Embedding service using SentenceTransformers."""

import numpy as np
from typing import List, Union, Dict, Any
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from ..utils.config import get_settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using SentenceTransformers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_name = self.settings.EMBEDDING_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        if not SentenceTransformer:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if the embedding service is available."""
        return self.model is not None
    
    def encode_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if not self.is_available():
            raise RuntimeError("Embedding model not available")
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def encode_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        if not self.is_available():
            raise RuntimeError("Embedding model not available")
        
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def encode_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for document chunks."""
        if not chunks:
            return []
        
        try:
            # Extract text from chunks
            texts = [chunk.get('text', '') for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.encode_texts(texts)
            
            # Add embeddings to chunks
            enriched_chunks = []
            for i, chunk in enumerate(chunks):
                enriched_chunk = chunk.copy()
                enriched_chunk['embedding'] = embeddings[i]
                enriched_chunk['embedding_model'] = self.model_name
                enriched_chunks.append(enriched_chunk)
            
            return enriched_chunks
            
        except Exception as e:
            logger.error(f"Error encoding chunks: {str(e)}")
            raise
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find most similar embeddings to a query."""
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate)
                similarities.append({
                    'index': i,
                    'similarity': similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {str(e)}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model."""
        if not self.is_available():
            return 0
        
        try:
            # Generate a test embedding to get dimension
            test_embedding = self.encode_text("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {str(e)}")
            return 0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_available():
            return {"available": False, "error": "Model not loaded"}
        
        return {
            "available": True,
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'unknown')
        }
