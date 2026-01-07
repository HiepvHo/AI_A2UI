# -*- coding: utf-8 -*-
"""
Embedding Manager - Emotion Chatbot
Quan ly embeddings su dung sentence-transformers + Pinecone
"""

import asyncio
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from ...config.config import (
    PINECONE_API_KEY, 
    PINECONE_INDEX_NAME, 
    EMBEDDING_MODEL, 
    EMBEDDING_DIMENSION
)
import time
import logging

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Quan ly text embeddings va vector database voi Pinecone"""
    
    def __init__(self, api_key: str = None, index_name: str = None):
        """
        Khoi tao embedding manager
        
        Args:
            api_key: Pinecone API key
            index_name: Pinecone index name
        """
        self.api_key = api_key or PINECONE_API_KEY
        self.index_name = index_name or PINECONE_INDEX_NAME
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        
        self.pinecone_client = None
        self.embedding_model = None
        self.batch_size = 32
        
    async def initialize(self, recreate_index: bool = False):
        """
        Khoi tao Pinecone connection va embedding model
        
        Args:
            recreate_index: Co tao lai index hay khong
        """
        try:
            # Initialize Pinecone client
            self.pinecone_client = Pinecone(api_key=self.api_key)
            
            # Delete existing index if requested
            if recreate_index:
                try:
                    self.pinecone_client.delete_index(self.index_name)
                    logger.debug(f"Deleted index: {self.index_name}")
                except Exception as e:
                    logger.debug(f"Delete index error: {e}")
            
            # Create new index if not exists
            if self.index_name not in self.pinecone_client.list_indexes().names():
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                logger.debug(f"Created index: {self.index_name}")
            else:
                logger.debug(f"Index exists: {self.index_name}")
            
            # Initialize embedding model (chỉ load 1 lần duy nhất)
            if self.embedding_model is None:
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("Embedding model loaded")
            else:
                logger.debug("Model already loaded")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize embedding manager: {str(e)}")
    
    async def embed_texts(self, texts: List[Dict[str, Any]]) -> bool:
        """
        Embed text documents va luu vao Pinecone
        
        Args:
            texts: List of dicts voi 'content' va 'metadata'
            
        Returns:
            True neu thanh cong
        """
        if not self.pinecone_client or not self.embedding_model:
            raise RuntimeError("Embedding manager not initialized. Call initialize() first.")
        
        try:
            # Extract texts
            texts_to_embed = []
            metadata_list = []
            ids = []
            
            for i, text_data in enumerate(texts):
                if not text_data.get('content'):
                    continue
                    
                texts_to_embed.append(text_data['content'])
                metadata_list.append(text_data.get('metadata', {}))
                ids.append(text_data.get('id', f"doc_{i}_{int(time.time())}"))
            
            if not texts_to_embed:
                logger.warning("No valid documents to embed")
                return False
            
            # Generate embeddings
            logger.info(f"Embedding {len(texts_to_embed)} documents...")
            embeddings = self.embedding_model.encode(
                texts_to_embed,
                batch_size=self.batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # Prepare vectors for Pinecone
            vectors = []
            for idx, (doc_id, embedding, text, metadata) in enumerate(zip(ids, embeddings, texts_to_embed, metadata_list)):
                vector = {
                    'id': doc_id,
                    'values': embedding.tolist(),
                    'metadata': {
                        **metadata,
                        'text': text[:1000]  # First 1000 chars
                    }
                }
                vectors.append(vector)
                
            # Upsert to Pinecone in batches
            index = self.pinecone_client.Index(self.index_name)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch)
            
            logger.info(f"Embedded {len(texts_to_embed)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            return False
    
    async def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Tim documents tuong tu dua tren query
        
        Args:
            query: Query text
            top_k: So luong ket qua tra ve
            
        Returns:
            List of similar documents
        """
        if not self.pinecone_client or not self.embedding_model:
            raise RuntimeError("Embedding manager not initialized. Call initialize() first.")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]
            
            # Search in Pinecone
            index = self.pinecone_client.Index(self.index_name)
            results = index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            documents = []
            for match in results.matches:
                doc = {
                    'id': match.id,
                    'score': match.score,
                    'text': match.metadata.get('text', ''),
                    'metadata': {k: v for k, v in match.metadata.items() if k != 'text'}
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Kiem tra health cua embedding system
            
        Returns:
            Health status dict
        """
        status = {
            'embedding_model_loaded': self.embedding_model is not None,
            'pinecone_connected': False,
            'index_exists': False,
            'overall': False
        }
        
        try:
            if self.pinecone_client:
                # Check if index exists
                indexes = self.pinecone_client.list_indexes().names()
                status['index_exists'] = self.index_name in indexes
                status['pinecone_connected'] = True
            
            status['overall'] = all([
                status['embedding_model_loaded'],
                status['pinecone_connected'],
                status['index_exists']
            ])
        
        except Exception as e:
            status['error'] = str(e)
        
        return status


# Global instance với lock để tránh race condition
_embedding_manager = None
_init_lock = asyncio.Lock()


async def get_embedding_manager() -> EmbeddingManager:
    """
    Get or create global embedding manager instance (singleton pattern)
    
    CRITICAL: Model chỉ được load 1 lần duy nhất khi server start.
    Tất cả requests sau sẽ reuse instance đã có.
    """
    global _embedding_manager
    
    # Nếu đã có instance và đã initialize, return ngay
    if _embedding_manager is not None and _embedding_manager.embedding_model is not None:
        return _embedding_manager
    
    # Dùng lock để tránh race condition khi nhiều request đồng thời
    async with _init_lock:
        # Double-check sau khi acquire lock
        if _embedding_manager is not None and _embedding_manager.embedding_model is not None:
            return _embedding_manager
        
        # Tạo instance mới và initialize
        logger.info("Creating EmbeddingManager instance")
        _embedding_manager = EmbeddingManager()
        await _embedding_manager.initialize()
        logger.info("EmbeddingManager initialized")
    
    return _embedding_manager


