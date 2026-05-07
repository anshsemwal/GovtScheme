"""FAISS Vector Store for efficient similarity search"""

import numpy as np
from typing import List, Optional, Tuple
import faiss
import logging

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISS-based vector store for scheme embeddings"""
    
    def __init__(self, dimension: int = 768):
        """
        Initialize FAISS store
        
        Args:
            dimension: Embedding vector dimension (default 768 for Google embedding-001)
        """
        self.dimension = dimension
        self.index: Optional[faiss.Index] = None
        self.embeddings: List[np.ndarray] = []
        self.documents: List[str] = []
        self.metadata: List[dict] = []
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the FAISS index"""
        # Using L2 (Euclidean) distance index
        self.index = faiss.IndexFlatL2(self.dimension)
        self._initialized = True
        logger.info(f"FAISS index initialized with dimension {self.dimension}")
    
    def add_embeddings(
        self, 
        embeddings: List[List[float]], 
        documents: List[str],
        metadata: Optional[List[dict]] = None
    ) -> None:
        """
        Add embeddings to the index
        
        Args:
            embeddings: List of embedding vectors
            documents: List of document texts
            metadata: Optional metadata for each document
        """
        if not self._initialized:
            self.initialize()
        
        if not embeddings:
            logger.warning("No embeddings to add")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Verify dimension
        if embeddings_array.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings_array.shape[1]} doesn't match "
                f"index dimension {self.dimension}"
            )
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
        
        logger.info(f"Added {len(embeddings)} embeddings to FAISS index")
    
    def search(
        self, 
        query_embedding: List[float], 
        k: int = 5
    ) -> List[Tuple[str, float, dict]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of (document, distance, metadata) tuples
        """
        if not self._initialized or self.index.ntotal == 0:
            logger.warning("FAISS index is empty or not initialized")
            return []
        
        # Ensure k doesn't exceed number of documents
        k = min(k, self.index.ntotal)
        
        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_array, k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:  # Valid index
                results.append((
                    self.documents[idx],
                    float(dist),
                    self.metadata[idx]
                ))
        
        return results
    
    def vector_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[dict]:
        """
        Vector similarity search with optional score threshold
        
        Returns:
            List of result dictionaries with document, score, and metadata
        """
        results = self.search(query_embedding, k)
        
        formatted_results = []
        for doc, distance, meta in results:
            # Convert L2 distance to similarity score (lower distance = higher similarity)
            # Using 1 / (1 + distance) to get score between 0 and 1
            similarity_score = 1 / (1 + distance)
            
            if score_threshold and similarity_score < score_threshold:
                continue
            
            formatted_results.append({
                "document": doc,
                "score": similarity_score,
                "distance": distance,
                "metadata": meta
            })
        
        return formatted_results
    
    def clear(self) -> None:
        """Clear all data from the index"""
        if self._initialized:
            self.index.reset()
        self.embeddings = []
        self.documents = []
        self.metadata = []
        logger.info("FAISS index cleared")
    
    @property
    def count(self) -> int:
        """Get number of vectors in the index"""
        if not self._initialized:
            return 0
        return self.index.ntotal
    
    def save(self, filepath: str) -> None:
        """Save FAISS index to file"""
        if self._initialized:
            faiss.write_index(self.index, filepath)
            logger.info(f"FAISS index saved to {filepath}")
    
    def load(self, filepath: str) -> None:
        """Load FAISS index from file"""
        self.index = faiss.read_index(filepath)
        self._initialized = True
        logger.info(f"FAISS index loaded from {filepath}")


# Default store instance
faiss_store = FAISSStore()
