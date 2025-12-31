# -*- coding: utf-8 -*-
"""
SQLAlchemy Models - Emotion Chatbot
Database models cho emotion tracking va chatbot
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Time, ForeignKey, Text, JSON, TIMESTAMP, Boolean, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base


class User(Base):
    """User table - Nguoi dung he thong"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    age = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    emotion_logs = relationship("EmotionLog", back_populates="user")
    mood_entries = relationship("MoodEntry", back_populates="user")
    crisis_alerts = relationship("CrisisAlert", back_populates="user")


class EmotionTopic(Base):
    """Emotion topics - 11 chu de cam xuc"""
    __tablename__ = 'emotion_topics'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    name_vi = Column(String(100))
    description = Column(Text)
    icon = Column(String(50))
    color = Column(String(20))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    emotion_logs = relationship("EmotionLog", back_populates="topic")
    documents = relationship("Document", back_populates="topic")


class EmotionLog(Base):
    """Emotion tracking logs - Nhat ky cam xuc"""
    __tablename__ = 'emotion_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)
    
    # FLEXIBLE: topic co the NULL (khong chon), multi-select luu rieng
    topic_id = Column(Integer, ForeignKey('emotion_topics.id'), nullable=True)
    
    # Emotion labels: ["buon", "lo", "gian"] - tags
    emotion_labels = Column(ARRAY(String), default=[])
    
    # Intensity: 1-5
    intensity = Column(Integer, nullable=False)
    
    note = Column(Text)
    triggers = Column(ARRAY(String), default=[])
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emotion_logs")
    topic = relationship("EmotionTopic", back_populates="emotion_logs")


class MoodEntry(Base):
    """Mood journal - Nhat ky tam trang"""
    __tablename__ = 'mood_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    
    mood_score = Column(Integer)  # 1-10
    energy_level = Column(Integer)  # 1-10
    sleep_quality = Column(Integer)  # 1-10
    
    journal_text = Column(Text)
    grateful_for = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="mood_entries")


class CrisisAlert(Base):
    """Crisis detection - Phat hien crisis"""
    __tablename__ = 'crisis_alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(TIMESTAMP, server_default=func.now())
    
    # Crisis level: 0-3
    crisis_level = Column(Integer, nullable=False)
    
    detected_keywords = Column(ARRAY(String), default=[])
    action_taken = Column(String(255))
    resolved = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="crisis_alerts")


class Document(Base):
    """Knowledge base documents - Tai lieu tam ly"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    
    # Link den topic (neu co)
    topic_id = Column(Integer, ForeignKey('emotion_topics.id'), nullable=True)
    
    title = Column(String(255))
    category = Column(String(100))
    file_path = Column(Text)
    file_type = Column(String(50))
    content_text = Column(Text)
    doc_metadata = Column(JSON)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    topic = relationship("EmotionTopic", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """Document chunks for RAG"""
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    chunk_text = Column(Text)
    chunk_index = Column(Integer)
    embedding_id = Column(String(255))
    chunk_metadata = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class ChartInsight(Base):
    """Chart insights cache"""
    __tablename__ = 'chart_insights'
    
    id = Column(Integer, primary_key=True)
    chart_id = Column(String(255), unique=True)
    chart_type = Column(String(100))
    data_query = Column(Text)
    insights = Column(JSON)
    qa_suggestions = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP)


class ChatSessionDB(Base):
    """Chat sessions"""
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("ChatMessageDB", back_populates="session")


class ChatMessageDB(Base):
    """Chat messages"""
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'))
    role = Column(String(50))
    content = Column(Text)
    msg_metadata = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    session = relationship("ChatSessionDB", back_populates="messages")

