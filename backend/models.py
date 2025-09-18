"""Data models for the CrossCheck application."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

Base = declarative_base()

# SQLAlchemy Models
class CourseDB(Base):
    """Database model for courses."""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    documents = relationship("DocumentDB", back_populates="course")
class DocumentDB(Base):
    """Database model for documents."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(String, default="pending")  # pending, processing, completed, failed
    num_chunks = Column(Integer, default=0)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Audio/Transcription specific fields
    is_audio = Column(String, default="false")  # "true" for audio files, "false" for documents
    transcript = Column(Text, nullable=True)  # Stored transcript for audio files
    transcription_status = Column(String, default="pending")  # pending, processing, completed, failed
    audio_duration = Column(Float, nullable=True)  # Duration in seconds
    transcription_metadata = Column(Text, nullable=True)  # JSON metadata from transcription
    
    # Relationship
    course = relationship("CourseDB", back_populates="documents")
    
class ChunkDB(Base):
    """Database model for document chunks."""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String, nullable=True)  # FAISS vector ID
    chunk_metadata = Column(Text, nullable=True)  # JSON metadata

class AINotesDB(Base):
    """Database model for AI-generated notes."""
    __tablename__ = "ai_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    notes = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String, nullable=True)  # Track which LLM model was used
    
    # Relationship
    document = relationship("DocumentDB")

# Pydantic Models for API
class CourseCreate(BaseModel):
    """Model for course creation."""
    name: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    """Model for course response."""
    id: int
    name: str
    description: Optional[str]
    document_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
class DocumentCreate(BaseModel):
    """Model for document creation."""
    filename: str
    file_type: str
    file_size: int

class DocumentResponse(BaseModel):
    """Model for document response."""
    id: int
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    processed: str
    num_chunks: int
    course_id: int
    
    # Audio/Transcription fields
    is_audio: Optional[str] = "false"
    transcript: Optional[str] = None
    transcription_status: Optional[str] = "not_applicable"
    audio_duration: Optional[float] = None
    transcription_metadata: Optional[str] = None
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    """Model for RAG query request."""
    question: str
    document_ids: Optional[List[int]] = None  # Filter by specific documents
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    """Model for RAG query response."""
    answer: str
    sources: List[dict]
    confidence_score: Optional[float] = None

class UploadResponse(BaseModel):
    """Model for upload response."""
    message: str
    document_id: int
    filename: str

class ChatMessage(BaseModel):
    """Model for chat messages."""
    message: str
    is_user: bool
    timestamp: datetime = datetime.now()

class AINotesResponse(BaseModel):
    """Model for AI notes response."""
    id: int
    document_id: int
    notes: str
    generated_at: datetime
    model_used: Optional[str]
    
    class Config:
        from_attributes = True

class AINotesGenerate(BaseModel):
    """Model for AI notes generation request."""
    regenerate: Optional[bool] = False  # Force regeneration even if notes exist

class TranscriptionStatus(BaseModel):
    """Model for transcription status response."""
    document_id: int
    filename: str
    transcription_status: str
    audio_duration: Optional[float]
    progress_percentage: Optional[float] = None
    error_message: Optional[str] = None
    
class TranscriptResponse(BaseModel):
    """Model for transcript response."""
    document_id: int
    filename: str
    transcript: str
    audio_duration: Optional[float]
    transcription_metadata: Optional[dict] = None
