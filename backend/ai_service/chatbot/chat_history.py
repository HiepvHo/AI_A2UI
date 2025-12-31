# -*- coding: utf-8 -*-
"""
Chat History Service - Emotion Chatbot
Quan ly chat history voi PostgreSQL
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...database.connection import async_session_maker
from ...database.models import ChatSessionDB, ChatMessageDB
import uuid


class ChatHistoryService:
    """Service quan ly chat history tu PostgreSQL"""
    
    async def get_or_create_session(
        self, 
        session_id: Optional[str] = None, 
        user_id: Optional[int] = None
    ) -> str:
        """
        Lay hoac tao moi chat session
        
        Args:
            session_id: Session ID (neu None thi tao moi)
            user_id: User ID (optional)
            
        Returns:
            Session ID (string)
        """
        async with async_session_maker() as session:
            try:
                # Neu co session_id, tim session
                if session_id:
                    stmt = select(ChatSessionDB).where(
                        ChatSessionDB.session_id == session_id
                    )
                    result = await session.execute(stmt)
                    existing_session = result.scalar_one_or_none()
                    
                    if existing_session:
                        return existing_session.session_id
                
                # Tao session moi
                new_session_id = session_id or f"session_{uuid.uuid4().hex[:16]}"
                new_session = ChatSessionDB(
                    session_id=new_session_id,
                    user_id=user_id
                )
                session.add(new_session)
                await session.commit()
                
                return new_session_id
                
            except Exception as e:
                await session.rollback()
                raise RuntimeError(f"Failed to get/create session: {str(e)}")
    
    async def get_chat_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> str:
        """
        Lay chat history de format cho LLM prompt
        
        Args:
            session_id: Session ID
            limit: So luong messages toi da
            
        Returns:
            Formatted chat history string
        """
        async with async_session_maker() as session:
            try:
                # Tim session
                stmt = select(ChatSessionDB).where(
                    ChatSessionDB.session_id == session_id
                )
                result = await session.execute(stmt)
                chat_session = result.scalar_one_or_none()
                
                if not chat_session:
                    return ""
                
                # Lay messages
                stmt = select(ChatMessageDB).where(
                    ChatMessageDB.session_id == chat_session.id
                ).order_by(ChatMessageDB.created_at.desc()).limit(limit)
                
                result = await session.execute(stmt)
                messages = result.scalars().all()
                
                # Format history (tu cu den moi)
                messages.reverse()
                history_lines = []
                for msg in messages:
                    role = "User" if msg.role == "user" else "Assistant"
                    history_lines.append(f"{role}: {msg.content}")
                
                return "\n".join(history_lines)
                
            except Exception as e:
                return ""
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Luu message vao database
        
        Args:
            session_id: Session ID (string)
            role: "user" hoac "assistant"
            content: Message content
            metadata: Optional metadata (JSON)
            
        Returns:
            True neu thanh cong
        """
        async with async_session_maker() as session:
            try:
                # Tim session
                stmt = select(ChatSessionDB).where(
                    ChatSessionDB.session_id == session_id
                )
                result = await session.execute(stmt)
                chat_session = result.scalar_one_or_none()
                
                if not chat_session:
                    # Tao session neu chua co
                    chat_session = ChatSessionDB(session_id=session_id)
                    session.add(chat_session)
                    await session.flush()
                
                # Luu message
                message = ChatMessageDB(
                    session_id=chat_session.id,
                    role=role,
                    content=content,
                    msg_metadata=metadata or {}
                )
                session.add(message)
                await session.commit()
                
                return True
                
            except Exception as e:
                await session.rollback()
                return False


# Global instance
_chat_history_service = None


async def get_chat_history_service() -> ChatHistoryService:
    """Get or create global chat history service instance"""
    global _chat_history_service
    
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    
    return _chat_history_service

