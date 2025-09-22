"""Data models for the CrossCheck application."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

Base = declarative_base()

# SQLAlchemy Models
class UserDB(Base):
    """Database model for users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Usage tracking
    daily_api_calls = Column(Integer, default=0)
    daily_api_limit = Column(Integer, default=100)  # Default limit
    total_documents = Column(Integer, default=0)
    total_storage_bytes = Column(Integer, default=0)
    storage_limit_bytes = Column(Integer, default=1073741824)  # 1GB default
    
    # Relationships
    courses = relationship("CourseDB", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSessionDB", back_populates="user", cascade="all, delete-orphan")

class UserSessionDB(Base):
    """Database model for user sessions."""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("UserDB", back_populates="sessions")
class CourseDB(Base):
    """Database model for courses."""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("UserDB", back_populates="courses")
    lectures = relationship("LectureDB", back_populates="course", cascade="all, delete-orphan")

class LectureDB(Base):
    """Database model for lectures."""
    __tablename__ = "lectures"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    lecture_date = Column(DateTime, nullable=True)  # Optional lecture date
    created_at = Column(DateTime, default=datetime.utcnow)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Relationships
    course = relationship("CourseDB", back_populates="lectures")
    documents = relationship("DocumentDB", back_populates="lecture", cascade="all, delete-orphan")
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
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    
    # Audio/Transcription specific fields
    is_audio = Column(String, default="false")  # "true" for audio files, "false" for documents
    transcript = Column(Text, nullable=True)  # Stored transcript for audio files
    transcription_status = Column(String, default="pending")  # pending, processing, completed, failed
    audio_duration = Column(Float, nullable=True)  # Duration in seconds
    transcription_metadata = Column(Text, nullable=True)  # JSON metadata from transcription
    
    # Relationship
    lecture = relationship("LectureDB", back_populates="documents")
    
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
class UserCreate(BaseModel):
    """Model for user registration."""
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str

class UserResponse(BaseModel):
    """Model for user response."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    daily_api_calls: int
    daily_api_limit: int
    total_documents: int
    total_storage_bytes: int
    storage_limit_bytes: int
    
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    """Model for session response."""
    session_id: str
    user: UserResponse
    expires_at: datetime
    created_at: datetime

class CourseCreate(BaseModel):
    """Model for course creation."""
    name: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    """Model for course response."""
    id: int
    name: str
    description: Optional[str]
    lecture_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LectureCreate(BaseModel):
    """Model for lecture creation."""
    title: str
    description: Optional[str] = None
    lecture_date: Optional[datetime] = None

class LectureResponse(BaseModel):
    """Model for lecture response."""
    id: int
    title: str
    description: Optional[str]
    lecture_date: Optional[datetime]
    created_at: datetime
    course_id: int
    document_count: int
    
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
    lecture_id: int
    
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
    query: Optional[str] = None  # Alias for question for frontend compatibility
    course_id: Optional[int] = None  # Course to query
    lecture_id: Optional[int] = None  # Lecture to query
    document_ids: Optional[List[int]] = None  # Filter by specific documents
    max_results: Optional[int] = 5
    
    def __init__(self, **data):
        # Handle frontend sending 'query' instead of 'question'
        if 'query' in data and 'question' not in data:
            data['question'] = data['query']
        super().__init__(**data)

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

class DocumentWithNotesResponse(BaseModel):
    """Model for document with notes response."""
    id: int
    filename: str
    lecture_id: int
    lecture_title: str
    course_id: int
    course_name: str
    has_notes: bool
    is_audio: Optional[str] = "false"
    upload_date: datetime
    
    class Config:
        from_attributes = True
