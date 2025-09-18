"""Vector store service using FAISS for similarity search."""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    import faiss
except ImportError:
    faiss = None

from ..utils.config import get_settings

logger = logging.getLogger(__name__)

class VectorStore:
    """FAISS-based vector store for similarity search."""
    
    def __init__(self):
        self.settings = get_settings()
        self.index_path = self.settings.FAISS_INDEX_PATH
        self.index = None
        self.metadata = {}  # Store metadata for each vector
        self.dimension = None
        self.document_indices = {}  # Store separate indices per document (legacy)
        self.course_indices = {}    # Store separate indices per course (NEW)
        self._ensure_directories()
        # Load any existing indices
        self.load_all_document_indices()  # Legacy support
        self.load_all_course_indices()    # NEW
    
    def _ensure_directories(self):
        """Ensure necessary directories exist."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
    
    def is_available(self) -> bool:
        """Check if FAISS is available."""
        return faiss is not None
    
    def initialize_index(self, dimension: int, index_type: str = "flat"):
        """Initialize a new FAISS index."""
        if not self.is_available():
            raise RuntimeError("FAISS not available. Run: pip install faiss-cpu")
        
        try:
            self.dimension = dimension
            
            if index_type == "flat":
                # Use L2 distance (Euclidean)
                self.index = faiss.IndexFlatL2(dimension)
            elif index_type == "ivf":
                # Use IVF (Inverted File) index for larger datasets
                quantizer = faiss.IndexFlatL2(dimension)
                self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)  # 100 clusters
            else:
                raise ValueError(f"Unsupported index type: {index_type}")
            
            self.metadata = {}
            logger.info(f"Initialized FAISS index with dimension {dimension}")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {str(e)}")
            raise
    
    def add_document_vectors(
        self,
        document_id: int,
        vectors: List[np.ndarray], 
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """Add vectors for a specific document."""
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors must match number of metadata entries")
        
        try:
            # Initialize document-specific index if needed
            if document_id not in self.document_indices:
                if not vectors:
                    raise ValueError("Cannot determine dimension from empty vectors list")
                
                dimension = len(vectors[0])
                self.document_indices[document_id] = {
                    'index': faiss.IndexFlatL2(dimension),
                    'metadata': {},
                    'dimension': dimension
                }
            
            doc_data = self.document_indices[document_id]
            
            # Convert to numpy array
            vectors_array = np.array(vectors).astype('float32')
            
            # Get current size to generate IDs
            current_size = doc_data['index'].ntotal
            
            # Add vectors to document index
            doc_data['index'].add(vectors_array)
            
            # Store metadata
            vector_ids = []
            for i, metadata in enumerate(metadata_list):
                vector_id = current_size + i
                doc_data['metadata'][vector_id] = metadata
                vector_ids.append(vector_id)
            
            logger.info(f"Added {len(vectors)} vectors to document {document_id} index")
            
            # Save the index to disk for persistence
            self.save_document_index(document_id)
            
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error adding vectors to document {document_id} index: {str(e)}")
            raise
    
    def add_course_vectors(
        self,
        course_id: int,
        document_id: int,
        vectors: List[np.ndarray], 
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """Add vectors for a specific course (from any document in that course)."""
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors must match number of metadata entries")
        
        try:
            # Initialize course-specific index if needed
            if course_id not in self.course_indices:
                if not vectors:
                    raise ValueError("Cannot determine dimension from empty vectors list")
                
                dimension = vectors[0].shape[0]
                # Use Inner Product for cosine similarity (after L2 normalization)
                index = faiss.IndexFlatIP(dimension)
                
                self.course_indices[course_id] = {
                    'index': index,
                    'metadata': {},
                    'dimension': dimension
                }
                logger.info(f"Created new FAISS index for course {course_id} with dimension {dimension}")
            
            course_data = self.course_indices[course_id]
            
            # Convert to numpy array and normalize for cosine similarity
            vectors_array = np.vstack(vectors).astype('float32')
            faiss.normalize_L2(vectors_array)
            
            # Add vectors to index
            current_size = course_data['index'].ntotal
            course_data['index'].add(vectors_array)
            
            # Store metadata with course and document info
            vector_ids = []
            for i, metadata in enumerate(metadata_list):
                vector_id = current_size + i
                # Enhance metadata with course and document info
                enhanced_metadata = metadata.copy()
                enhanced_metadata['course_id'] = course_id
                enhanced_metadata['document_id'] = document_id
                
                course_data['metadata'][vector_id] = enhanced_metadata
                vector_ids.append(vector_id)
            
            logger.info(f"Added {len(vectors)} vectors to course {course_id} index (from document {document_id})")
            
            # Save the index to disk for persistence
            self.save_course_index(course_id)
            
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error adding vectors to course {course_id} index: {str(e)}")
            raise
    
    def search_document(
        self, 
        document_id: int,
        query_vector: np.ndarray, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors within a specific document."""
        logger.info(f"Searching document {document_id}. Available indices: {list(self.document_indices.keys())}")
        
        # Try to load the index if it's not in memory
        if document_id not in self.document_indices:
            logger.info(f"Index not in memory, trying to load from disk for document {document_id}")
            if not self.load_document_index(document_id):
                logger.warning(f"No index found for document {document_id}")
                return []
        
        try:
            doc_data = self.document_indices[document_id]
            
            # Ensure query vector is the right shape and type
            query_vector = query_vector.reshape(1, -1).astype('float32')
            
            # Search the document index
            distances, indices = doc_data['index'].search(query_vector, k)
            
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue
                
                # Get metadata
                metadata = doc_data['metadata'].get(idx, {})
                
                # Convert distance to similarity score (L2 distance -> similarity)
                similarity = 1 / (1 + distance)  # Simple conversion
                
                results.append({
                    'vector_id': int(idx),
                    'distance': float(distance),
                    'similarity': float(similarity),  # Ensure it's a Python float
                    'metadata': metadata,
                    'document_id': document_id
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching document {document_id} index: {str(e)}")
            return []
    
    def search_course(
        self, 
        course_id: int,
        query_vector: np.ndarray, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors within a specific course (across all documents in that course)."""
        logger.info(f"Searching course {course_id}. Available course indices: {list(self.course_indices.keys())}")
        
        # Try to load the index if it's not in memory
        if course_id not in self.course_indices:
            logger.info(f"Course index not in memory, trying to load from disk for course {course_id}")
            if not self.load_course_index(course_id):
                logger.warning(f"No index found for course {course_id}")
                return []
        
        try:
            course_data = self.course_indices[course_id]
            
            # Ensure query vector is the right shape and type
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            query_vector = query_vector.astype('float32')
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_vector)
            
            # Search the index
            similarities, indices = course_data['index'].search(query_vector, k)
            
            # Convert results to readable format
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if idx == -1:  # FAISS returns -1 for empty results
                    continue
                
                distance = 1.0 - similarity  # Convert similarity to distance
                metadata = course_data['metadata'].get(int(idx), {})
                
                results.append({
                    'vector_id': int(idx),
                    'distance': float(distance),
                    'similarity': float(similarity),  # Ensure it's a Python float
                    'metadata': metadata,
                    'course_id': course_id
                })
            
            logger.info(f"Found {len(results)} results for course {course_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching course {course_id} index: {str(e)}")
            return []
    
    def save_document_index(self, document_id: int, path: Optional[str] = None):
        """Save a document's FAISS index and metadata to disk."""
        if document_id not in self.document_indices:
            logger.warning(f"No index to save for document {document_id}")
            return
        
        save_path = path or f"{self.index_path}_doc_{document_id}"
        
        try:
            doc_data = self.document_indices[document_id]
            
            # Save FAISS index
            faiss.write_index(doc_data['index'], f"{save_path}.faiss")
            
            # Save metadata
            with open(f"{save_path}.metadata", 'wb') as f:
                pickle.dump({
                    'metadata': doc_data['metadata'],
                    'dimension': doc_data['dimension']
                }, f)
            
            logger.info(f"Saved document {document_id} index to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving document {document_id} index: {str(e)}")
            raise
    
    def load_document_index(self, document_id: int, path: Optional[str] = None) -> bool:
        """Load a document's FAISS index and metadata from disk."""
        load_path = path or f"{self.index_path}_doc_{document_id}"
        
        try:
            # Check if files exist
            if not os.path.exists(f"{load_path}.faiss") or not os.path.exists(f"{load_path}.metadata"):
                logger.info(f"Index files not found for document {document_id}")
                return False
            
            # Load FAISS index
            index = faiss.read_index(f"{load_path}.faiss")
            
            # Load metadata
            with open(f"{load_path}.metadata", 'rb') as f:
                data = pickle.load(f)
                
            # Store in document indices
            self.document_indices[document_id] = {
                'index': index,
                'metadata': data['metadata'],
                'dimension': data['dimension']
            }
            
            logger.info(f"Loaded document {document_id} index from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading document {document_id} index: {str(e)}")
            return False
    
    def load_all_document_indices(self):
        """Load all available document indices from disk."""
        try:
            embeddings_dir = os.path.dirname(self.index_path)
            if not os.path.exists(embeddings_dir):
                return
                
            # Look for all document index files
            for filename in os.listdir(embeddings_dir):
                if filename.endswith('.faiss') and '_doc_' in filename:
                    # Extract document ID from filename
                    try:
                        doc_id_str = filename.split('_doc_')[1].split('.')[0]
                        document_id = int(doc_id_str)
                        self.load_document_index(document_id)
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse document ID from {filename}")
                        
        except Exception as e:
            logger.error(f"Error loading document indices: {str(e)}")
    
    def save_course_index(self, course_id: int, path: Optional[str] = None):
        """Save a course's FAISS index and metadata to disk."""
        if course_id not in self.course_indices:
            logger.warning(f"No index to save for course {course_id}")
            return
        
        save_path = path or f"{self.index_path}_course_{course_id}"
        
        try:
            course_data = self.course_indices[course_id]
            
            # Save FAISS index
            faiss.write_index(course_data['index'], f"{save_path}.faiss")
            
            # Save metadata
            with open(f"{save_path}.metadata", 'wb') as f:
                pickle.dump({
                    'metadata': course_data['metadata'],
                    'dimension': course_data['dimension']
                }, f)
            
            logger.info(f"Saved course {course_id} index to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving course {course_id} index: {str(e)}")
            raise
    
    def load_course_index(self, course_id: int, path: Optional[str] = None) -> bool:
        """Load a course's FAISS index and metadata from disk."""
        load_path = path or f"{self.index_path}_course_{course_id}"
        
        try:
            # Check if files exist
            if not os.path.exists(f"{load_path}.faiss") or not os.path.exists(f"{load_path}.metadata"):
                logger.info(f"Index files not found for course {course_id}")
                return False
            
            # Load FAISS index
            index = faiss.read_index(f"{load_path}.faiss")
            
            # Load metadata
            with open(f"{load_path}.metadata", 'rb') as f:
                data = pickle.load(f)
                
            # Store in course indices
            self.course_indices[course_id] = {
                'index': index,
                'metadata': data['metadata'],
                'dimension': data['dimension']
            }
            
            logger.info(f"Loaded course {course_id} index from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading course {course_id} index: {str(e)}")
            return False
    
    def load_all_course_indices(self):
        """Load all available course indices from disk."""
        try:
            embeddings_dir = os.path.dirname(self.index_path)
            if not os.path.exists(embeddings_dir):
                return
                
            # Look for all course index files
            for filename in os.listdir(embeddings_dir):
                if filename.endswith('.faiss') and '_course_' in filename:
                    # Extract course ID from filename
                    try:
                        course_id_str = filename.split('_course_')[1].split('.')[0]
                        course_id = int(course_id_str)
                        self.load_course_index(course_id)
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse course ID from {filename}")
                        
        except Exception as e:
            logger.error(f"Error loading course indices: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self.index:
            return {
                "initialized": False,
                "total_vectors": 0,
                "dimension": None
            }
        
        return {
            "initialized": True,
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_entries": len(self.metadata)
        }
    
    def clear(self):
        """Clear the index and metadata."""
        if self.index:
            self.index.reset()
        self.metadata = {}
        logger.info("Cleared vector store")
    
    def remove_vectors_by_document(self, document_id: int) -> int:
        """Remove all vectors associated with a document."""
        # Note: FAISS doesn't support efficient removal
        # This is a placeholder implementation
        # In production, you might need to rebuild the index
        
        removed_count = 0
        keys_to_remove = []
        
        for vector_id, metadata in self.metadata.items():
            if metadata.get('document_id') == document_id:
                keys_to_remove.append(vector_id)
                removed_count += 1
        
        # Remove metadata entries
        for key in keys_to_remove:
            del self.metadata[key]
        
        logger.info(f"Removed metadata for {removed_count} vectors from document {document_id}")
        logger.warning("Note: Vectors still exist in FAISS index. Consider rebuilding index for production use.")
        
        return removed_count
