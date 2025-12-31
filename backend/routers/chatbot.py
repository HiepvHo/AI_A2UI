"""
Chatbot Router - API endpoints cho emotion chatbot
Cung cap endpoints: chat, health, stats
"""

import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chatbot interactions."""
    query: str = Field(..., min_length=1, max_length=1000, description="User's question or query")
    session_id: Optional[str] = Field(None, description="Optional session identifier for conversation tracking")
    user_id: Optional[int] = Field(1, description="User ID for SQL analytics")
    context_limit: Optional[int] = Field(5, ge=1, le=10, description="Maximum number of context documents to retrieve")


class ChatResponse(BaseModel):
    """Response model for chatbot interactions."""
    success: bool = Field(..., description="Success status")
    answer: str = Field(..., description="Chatbot's answer")
    chart_spec: Optional[Dict] = Field(None, description="Plotly chart specification")
    chart_id: Optional[str] = Field(None, description="Chart ID for insights mapping")
    a2ui_blocks: List[Dict] = Field(default_factory=list, description="A2UI JSON blocks")
    sources: List[Dict] = Field(default_factory=list, description="Source documents used")
    sql_query: Optional[str] = Field(None, description="SQL query if analytics was used")
    crisis_detected: bool = Field(False, description="Crisis keywords detected")
    context_used: bool = Field(False, description="Whether context was used")
    query: str = Field(..., description="Original query")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")
    processing_time: Optional[float] = Field(None, description="Processing time (seconds)")


class HealthStatus(BaseModel):
    """Model for system health status."""
    gemini_api: bool = Field(..., description="Gemini API connectivity status")
    embedding_system: bool = Field(..., description="Embedding system status")
    pinecone_connection: bool = Field(..., description="Pinecone vector database status")
    overall: bool = Field(..., description="Overall system health")
    error: Optional[str] = Field(None, description="Error message if any component failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
from ..ai_service.chatbot.rag import get_rag_system, chat_with_rag
from ..ai_service.chatbot.embedding import get_embedding_manager
from ..config.config import (
    EMBEDDING_MODEL,
    TOP_K_RESULTS,
    LLM_MODEL
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat query using the RAG system.
    
    Args:
        request: Chat request containing query and optional parameters
        
    Returns:
        ChatResponse with generated answer and sources
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Generate response using RAG system
        response_data = await chat_with_rag(
            query=request.query,
            session_id=request.session_id,
            user_id=request.user_id,
            context_docs=None
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Format response
        chat_response = ChatResponse(
            success=response_data.get('success', True),
            answer=response_data.get('answer', ''),
            chart_spec=response_data.get('chart_spec'),
            chart_id=response_data.get('chart_id'),
            a2ui_blocks=response_data.get('a2ui_blocks', []),
            sources=response_data.get('sources', []),
            sql_query=response_data.get('sql_query'),
            crisis_detected=response_data.get('crisis_detected', False),
            context_used=response_data.get('context_used', False),
            query=request.query,
            session_id=request.session_id,
            processing_time=processing_time
        )
        
        logger.info(f"Chat response generated in {processing_time:.2f}s")
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


# NOTE: Indexing endpoints removed
# Use scripts/index_documents.py to index PDF/Word documents
# No web crawling needed for this project


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Check the health status of the chatbot system components.
    
    Returns:
        HealthStatus with component status information
    """
    try:
        # Get RAG system health
        rag_system = await get_rag_system()
        rag_health = await rag_system.health_check()
        
        # Check embedding system separately
        try:
            embedding_manager = await get_embedding_manager()
            # Test a simple search to verify Pinecone connection
            await embedding_manager.search_similar("health_check", top_k=1)
            pinecone_status = True
        except Exception as e:
            logger.warning(f"Pinecone connection check failed: {str(e)}")
            pinecone_status = False
        
        health_status = HealthStatus(
            gemini_api=rag_health.get('gemini_api', False),
            embedding_system=rag_health.get('embedding_system', False),
            pinecone_connection=pinecone_status,
            overall=rag_health.get('overall', False) and pinecone_status,
            error=rag_health.get('error')
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthStatus(
            gemini_api=False,
            embedding_system=False,
            pinecone_connection=False,
            overall=False,
            error=str(e)
        )


@router.post("/initialize")
async def initialize_system(recreate_index: bool = False):
    """
    Initialize the chatbot system components.
    
    Args:
        recreate_index: Whether to recreate the vector index
        
    Returns:
        Status message
    """
    try:
        logger.info("Initializing chatbot system...")
        
        # Initialize embedding manager
        embedding_manager = await get_embedding_manager()
        await embedding_manager.initialize(recreate_index=recreate_index)
        
        # Initialize RAG system
        rag_system = await get_rag_system()
        
        # Perform health check
        health = await rag_system.health_check()
        
        if health.get('overall', False):
            return {
                "success": True,
                "message": "Chatbot system initialized successfully",
                "components": {
                    "embedding_system": health.get('embedding_system', False),
                    "gemini_api": health.get('gemini_api', False)
                }
            }
        else:
            return {
                "success": False,
                "message": "Chatbot system initialization incomplete",
                "error": health.get('error', 'Unknown error'),
                "components": health
            }
            
    except Exception as e:
        logger.error(f"System initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize system: {str(e)}"
        )




@router.get("/stats")
async def get_system_stats():
    """
    Get system statistics and information.
    
    Returns:
        Dictionary with system statistics
    """
    try:
        # Get basic stats
        stats = {
            "system_version": "1.0.0",
            "domain": "emotion_chatbot",
            "features": {
                "rag_chat": True,
                "emotion_tracking": True,
                "vector_search": True,
                "sql_analytics": True,
                "chart_generation": True,
                "a2ui_blocks": True
            },
            "configuration": {
                "max_context_docs": TOP_K_RESULTS,
                "embedding_model": EMBEDDING_MODEL,
                "llm_model": LLM_MODEL
            }
        }
        
        # Add health status
        health = await health_check()
        stats["health"] = health
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system stats: {str(e)}"
        )


# NOTE: Index management endpoints removed
# Use Pinecone Console to manage index manually
# Or use scripts/index_documents.py with recreate_index parameter