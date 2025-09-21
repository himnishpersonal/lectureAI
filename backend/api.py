"""FastAPI server for LectureAI intelligent course assistant."""

import os
import shutil
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    CourseDB, LectureDB, DocumentDB, ChunkDB, AINotesDB, CourseCreate, CourseResponse,
    LectureCreate, LectureResponse, DocumentCreate, DocumentResponse, QueryRequest, QueryResponse, UploadResponse,
    AINotesResponse, AINotesGenerate, TranscriptionStatus, TranscriptResponse,
    DocumentWithNotesResponse
)
from .utils.config import get_settings
from .services.document_processor import DocumentProcessor
from .services.embedding_service import EmbeddingService
from .services.vector_store import VectorStore
from .services.rag_service import RAGService
from .services.transcription_service import TranscriptionService

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LectureAI API",
    description="Intelligent Course Assistant API - AI-Powered Educational RAG System",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
from .models import Base
Base.metadata.create_all(bind=engine)

# Note: Database migration should be run manually using migrate_database.py
# This ensures proper schema updates before the application starts

# Dependency to get database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize services as singletons
document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStore()
rag_service = RAGService(embedding_service=embedding_service, vector_store=vector_store)
transcription_service = TranscriptionService()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

async def process_audio_file_async(document_id: int, file_path: str, db: Session):
    """Process audio file asynchronously with transcription and AI notes generation."""
    import asyncio
    from datetime import timedelta
    
    async def transcribe_and_process():
        # Create a new database session for the async task
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        async_db = SessionLocal()
        
        try:
            # Update status to processing
            document = async_db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
            if not document:
                async_db.close()
                return
            
            document.transcription_status = "processing"
            document.processed = "processing"
            async_db.commit()
            
            # Get audio duration
            duration = transcription_service.get_audio_duration(file_path)
            if duration:
                document.audio_duration = duration
                async_db.commit()
            
            # Transcribe audio
            transcription_result = await transcription_service.transcribe_audio_async(file_path)
            
            if transcription_result["success"]:
                # Store transcript and metadata
                document.transcript = transcription_result["transcript"]
                document.transcription_metadata = json.dumps(transcription_result["metadata"])
                document.transcription_status = "completed"
                
                # Process transcript as text for chunking and embeddings
                processing_result = document_processor.process_text(
                    transcription_result["transcript"], 
                    document_id,
                    filename=document.filename
                )
                
                if processing_result["success"]:
                    # Generate embeddings for transcript chunks
                    chunks_with_embeddings = embedding_service.encode_chunks(processing_result["chunks"])
                    
                    # Extract embeddings and metadata for vector store
                    embeddings = [chunk["embedding"] for chunk in chunks_with_embeddings]
                    chunk_metadata = []
                    
                    for chunk in chunks_with_embeddings:
                        metadata = chunk["metadata"].copy()
                        metadata["text"] = chunk["text"]
                        metadata["filename"] = document.filename
                        metadata["is_audio"] = True
                        chunk_metadata.append(metadata)
                    
                    # Get course_id from lecture
                    lecture = async_db.query(LectureDB).filter(LectureDB.id == document.lecture_id).first()
                    if not lecture:
                        logger.error(f"Lecture {document.lecture_id} not found for document {document.id}")
                        return
                    
                    # Store embeddings in course-based vector store
                    vector_ids = vector_store.add_course_vectors(
                        course_id=lecture.course_id,
                        document_id=document.id,
                        vectors=embeddings,
                        metadata_list=chunk_metadata
                    )
                    
                    # Store chunks in database
                    for i, chunk in enumerate(chunks_with_embeddings):
                        db_chunk = ChunkDB(
                            document_id=document.id,
                            chunk_index=chunk["metadata"]["chunk_index"],
                            content=chunk["text"],
                            embedding_id=str(vector_ids[i]) if i < len(vector_ids) else None,
                            chunk_metadata=json.dumps(chunk["metadata"])
                        )
                        async_db.add(db_chunk)
                    
                    # Update document status
                    document.processed = "completed"
                    document.num_chunks = len(chunks_with_embeddings)
                    async_db.commit()
                    
                    # Wait 0.5 seconds then auto-generate AI notes
                    await asyncio.sleep(0.5)
                    
                    # Auto-generate AI notes from transcript
                    try:
                        chunk_data = [{"content": chunk.content} for chunk in 
                                    async_db.query(ChunkDB).filter(ChunkDB.document_id == document_id).all()]
                        
                        notes_result = rag_service.generate_document_notes(chunk_data, document.filename)
                        
                        if notes_result.get("success", False):
                            # Check if notes already exist
                            existing_notes = async_db.query(AINotesDB).filter(AINotesDB.document_id == document_id).first()
                            if not existing_notes:
                                notes_record = AINotesDB(
                                    document_id=document_id,
                                    notes=notes_result["notes"],
                                    model_used=notes_result.get("model_used")
                                )
                                async_db.add(notes_record)
                                async_db.commit()
                                logger.info(f"Auto-generated AI notes for audio document {document_id}")
                    except Exception as e:
                        logger.error(f"Error auto-generating AI notes: {str(e)}")
                    
                else:
                    document.processed = "failed"
                    async_db.commit()
            else:
                document.transcription_status = "failed"
                document.processed = "failed"
                async_db.commit()
                
        except Exception as e:
            logger.error(f"Error processing audio file {document_id}: {str(e)}")
            document = async_db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
            if document:
                document.transcription_status = "failed"
                document.processed = "failed"
                async_db.commit()
        finally:
            # Always close the database session
            async_db.close()
    
    # Start the async task
    asyncio.create_task(transcribe_and_process())

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "CrossCheck Journalism RAG Assistant API"}

@app.post("/lectures/{lecture_id}/upload", response_model=UploadResponse)
async def upload_document_to_lecture(
    lecture_id: int,
    file: UploadFile = File(...),
    custom_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a document to a specific lecture for processing."""
    try:
        # Verify lecture exists
        lecture = db.query(LectureDB).filter(LectureDB.id == lecture_id).first()
        if not lecture:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        # Validate file type
        document_types = [".pdf", ".docx", ".txt"]
        audio_types = [".mp3", ".wav", ".m4a", ".mp4"]
        allowed_types = document_types + audio_types
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed: {allowed_types}"
            )
        
        # Determine if this is an audio file
        is_audio = file_extension in audio_types
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use custom name if provided, otherwise use original filename
        if custom_name and custom_name.strip():
            display_name = custom_name.strip()
            # Ensure the display name has the correct extension
            if not display_name.endswith(file_extension):
                display_name += file_extension
        else:
            display_name = file.filename
        
        filename = f"{timestamp}_{display_name}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        db_document = DocumentDB(
            filename=filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=file_size,
            processed="pending",
            lecture_id=lecture_id,
            is_audio="true" if is_audio else "false"
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Process document immediately (in production, consider async processing)
        try:
            if is_audio:
                # Handle audio transcription
                transcription_result = transcription_service.transcribe_audio(file_path)
                
                if transcription_result["success"]:
                    db_document.transcript = transcription_result["transcript"]
                    db_document.transcription_status = "completed"
                    db_document.audio_duration = transcription_result.get("duration")
                    db_document.transcription_metadata = json.dumps(transcription_result.get("metadata", {}))
                    
                    # Process transcript as text document
                    processing_result = document_processor.process_text(
                        transcription_result["transcript"], 
                        db_document.id
                    )
                else:
                    db_document.transcription_status = "failed"
                    processing_result = {"success": False, "chunks": []}
            else:
                # Process regular document
                processing_result = document_processor.process_document(file_path, db_document.id)
            
            if processing_result["success"]:
                # Generate embeddings for chunks
                chunks_with_embeddings = embedding_service.encode_chunks(processing_result["chunks"])
                
                # Extract embeddings and metadata for vector store
                embeddings = [chunk["embedding"] for chunk in chunks_with_embeddings]
                chunk_metadata = []
                
                for chunk in chunks_with_embeddings:
                    metadata = chunk["metadata"].copy()
                    metadata["text"] = chunk["text"]  # Include text in metadata
                    metadata["filename"] = filename
                    metadata["lecture_id"] = lecture_id
                    metadata["course_id"] = lecture.course_id
                    chunk_metadata.append(metadata)
                
                # Store embeddings in course-based vector store
                vector_ids = vector_store.add_course_vectors(
                    course_id=lecture.course_id,
                    document_id=db_document.id,
                    vectors=embeddings,
                    metadata_list=chunk_metadata
                )
                
                # Store chunks in database
                for i, chunk in enumerate(chunks_with_embeddings):
                    db_chunk = ChunkDB(
                        document_id=db_document.id,
                        chunk_index=chunk["metadata"]["chunk_index"],
                        content=chunk["text"],
                        embedding_id=str(vector_ids[i]) if i < len(vector_ids) else None,
                        chunk_metadata=json.dumps(chunk["metadata"])
                    )
                    db.add(db_chunk)
                
                # Update document status
                db_document.processed = "completed"
                db_document.num_chunks = len(chunks_with_embeddings)
                db.commit()
                
                # Automatically generate AI notes for the document
                try:
                    logger.info(f"Auto-generating AI notes for document {db_document.id}")
                    
                    # Get document chunks for AI notes generation
                    chunks = db.query(ChunkDB).filter(ChunkDB.document_id == db_document.id).all()
                    
                    if chunks:
                        # Convert chunks to the format expected by the RAG service
                        chunk_data = [{"content": chunk.content} for chunk in chunks]
                        
                        # Generate notes using RAG service
                        result = rag_service.generate_document_notes(chunk_data, db_document.filename)
                        
                        if result.get("success", False):
                            # Save AI notes to database
                            ai_notes = AINotesDB(
                                document_id=db_document.id,
                                notes=result["notes"],
                                generated_at=datetime.utcnow(),
                                model_used=result.get("model_used", "deepseek/deepseek-chat")
                            )
                            db.add(ai_notes)
                            db.commit()
                            logger.info(f"AI notes generated successfully for document {db_document.id}")
                        else:
                            logger.warning(f"Failed to generate AI notes for document {db_document.id}: {result.get('error', 'Unknown error')}")
                    else:
                        logger.warning(f"No chunks found for document {db_document.id}, skipping AI notes generation")
                        
                except Exception as e:
                    logger.warning(f"Failed to auto-generate AI notes for document {db_document.id}: {str(e)}")
                    # Don't fail the upload if notes generation fails
                
            else:
                # Mark as failed
                db_document.processed = "failed"
                db.commit()
                
        except Exception as e:
            logger.error(f"Error processing document {db_document.id}: {str(e)}")
            db_document.processed = "failed"
            db.commit()
        
        return UploadResponse(
            message="Document uploaded successfully",
            document_id=db_document.id,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/documents", response_model=UploadResponse)
async def upload_document_to_course(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document to a specific course for processing."""
    try:
        # Verify course exists
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Validate file type
        document_types = [".pdf", ".docx", ".txt"]
        audio_types = [".mp3", ".wav", ".m4a", ".mp4"]
        allowed_types = document_types + audio_types
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed: {allowed_types}"
            )
        
        # Determine if this is an audio file
        is_audio = file_extension in audio_types
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record with course association
        db_document = DocumentDB(
            filename=filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=file_size,
            course_id=course_id,  # Associate with course
            processed="pending",
            is_audio="true" if is_audio else "false",
            transcription_status="pending" if is_audio else "not_applicable"
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Process document or audio file
        try:
            if is_audio:
                # Start transcription process asynchronously
                await process_audio_file_async(db_document.id, file_path, db)
                
                return UploadResponse(
                    message=f"Audio file uploaded successfully. Transcription started.",
                    document_id=db_document.id,
                    filename=filename
                )
            else:
                # Process the document to extract text and create chunks
                processing_result = document_processor.process_document(file_path, db_document.id)
                
                if processing_result["success"]:
                    # Generate embeddings for chunks
                    chunks_with_embeddings = embedding_service.encode_chunks(processing_result["chunks"])
                    
                    # Extract embeddings and metadata for vector store
                    embeddings = [chunk["embedding"] for chunk in chunks_with_embeddings]
                    chunk_metadata = []
                    
                    for chunk in chunks_with_embeddings:
                        metadata = chunk["metadata"].copy()
                        metadata["text"] = chunk["text"]  # Include text in metadata
                        metadata["filename"] = filename
                        chunk_metadata.append(metadata)
                    
                    # Store embeddings in course-based vector store
                    vector_ids = vector_store.add_course_vectors(
                        course_id=course_id,
                        document_id=db_document.id,
                        vectors=embeddings,
                        metadata_list=chunk_metadata
                    )
                    
                    # Store chunks in database
                    for i, chunk in enumerate(chunks_with_embeddings):
                        db_chunk = ChunkDB(
                            document_id=db_document.id,
                            chunk_index=chunk["metadata"]["chunk_index"],
                            content=chunk["text"],
                            embedding_id=str(vector_ids[i]) if i < len(vector_ids) else None,
                            chunk_metadata=json.dumps(chunk["metadata"])
                        )
                        db.add(db_chunk)
                    
                    # Update document status
                    db_document.processed = "completed"
                    db_document.num_chunks = len(chunks_with_embeddings)
                    db.commit()
                    
                else:
                    # Mark as failed
                    db_document.processed = "failed"
                    db.commit()
                
        except Exception as e:
            logger.error(f"Error processing document {db_document.id} for course {course_id}: {str(e)}")
            db_document.processed = "failed"
            db.commit()
        
        return UploadResponse(
            message=f"Document uploaded successfully to course '{course.name}'",
            document_id=db_document.id,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to course {course_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
    """Get list of uploaded documents."""
    try:
        documents = db.query(DocumentDB).order_by(DocumentDB.upload_date.desc()).all()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and all associated data."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Deleting document {document_id}: {document.filename}")
        
        # 1. Delete AI notes
        ai_notes = db.query(AINotesDB).filter(AINotesDB.document_id == document_id).all()
        for note in ai_notes:
            db.delete(note)
        logger.info(f"Deleted {len(ai_notes)} AI notes for document {document_id}")
        
        # 2. Delete chunks and their embeddings
        chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document_id).all()
        embedding_ids_to_remove = []
        
        for chunk in chunks:
            if chunk.embedding_id:
                embedding_ids_to_remove.append(chunk.embedding_id)
            db.delete(chunk)
        
        # Remove embeddings from vector store
        if embedding_ids_to_remove:
            try:
                vector_store.delete_vectors(embedding_ids_to_remove)
                logger.info(f"Deleted {len(embedding_ids_to_remove)} embeddings from vector store")
            except Exception as e:
                logger.warning(f"Failed to delete embeddings from vector store: {e}")
        
        logger.info(f"Deleted {len(chunks)} chunks for document {document_id}")
        
        # 3. Delete associated files
        files_deleted = []
        
        # Delete main document file
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
            files_deleted.append(document.file_path)
        
        # Delete chunks file if it exists
        chunks_file = os.path.join(
            settings.CHUNKS_DIR, 
            f"document_{document_id}_chunks.json"
        )
        if os.path.exists(chunks_file):
            os.remove(chunks_file)
            files_deleted.append(chunks_file)
        
        logger.info(f"Deleted files: {files_deleted}")
        
        # 4. Delete document record
        db.delete(document)
        db.commit()
        
        return {
            "message": "Document deleted successfully",
            "details": {
                "document_id": document_id,
                "filename": document.filename,
                "ai_notes_deleted": len(ai_notes),
                "chunks_deleted": len(chunks),
                "embeddings_deleted": len(embedding_ids_to_remove),
                "files_deleted": len(files_deleted)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/query")
async def query_documents(
    query: QueryRequest,
    db: Session = Depends(get_db)
):
    """Query documents using RAG."""
    try:
        # Handle course-based queries (from chat interface)
        if query.course_id:
            # Verify course exists
            course = db.query(CourseDB).filter(CourseDB.id == query.course_id).first()
            if not course:
                raise HTTPException(status_code=404, detail="Course not found")
            
            # Check if course has any processed documents through its lectures
            document_count = db.query(DocumentDB).join(LectureDB).filter(
                LectureDB.course_id == query.course_id,
                DocumentDB.processed == "completed"
            ).count()
            
            if document_count == 0:
                return {
                    "answer": f"Course '{course.name}' has no processed documents yet. Please upload some documents first.",
                    "citations": [],
                    "success": False
                }
            
            # Perform RAG query on the course
            result = rag_service.query_course(
                user_input=query.question,
                course_id=query.course_id,
                max_results=query.max_results or 5
            )
            
            return {
                "answer": result["answer"],
                "citations": result["citations"],
                "success": result["success"],
                "model_info": result.get("model_info", {}),
                "course_info": {
                    "course_id": query.course_id,
                    "course_name": course.name,
                    "document_count": document_count
                }
            }
        
        # If specific document IDs are provided, query each one
        elif query.document_ids and len(query.document_ids) == 1:
            # Single document query
            document_id = query.document_ids[0]
            
            # Check if document exists and is processed
            document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            if document.processed != "completed":
                return {
                    "answer": f"Document '{document.filename}' is still being processed. Please try again in a moment.",
                    "citations": [],
                    "success": False
                }
            
            # Perform RAG query on the specific document
            result = rag_service.query_document(
                user_input=query.question,
                document_id=document_id,
                max_results=query.max_results or 5
            )
            
            return {
                "answer": result["answer"],
                "citations": result["citations"],
                "success": result["success"],
                "model_info": result.get("model_info", {})
            }
        
        else:
            # No specific course or document specified
            return {
                "answer": "Please specify either a course_id or document_ids to query.",
                "citations": [],
                "success": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/{document_id}")
async def process_document(document_id: int, db: Session = Depends(get_db)):
    """Process a document (extract text, create embeddings)."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.processed == "completed":
            return {"message": "Document already processed"}
        
        # Update status to processing
        document.processed = "processing"
        db.commit()
        
        # TODO: Implement actual document processing
        # For now, just mark as completed
        document.processed = "completed"
        document.num_chunks = 5  # Placeholder
        db.commit()
        
        return {"message": "Document processed successfully"}
        
    except Exception as e:
        document.processed = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

# Course Management Endpoints
@app.post("/courses", response_model=CourseResponse)
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    try:
        # Create new course
        db_course = CourseDB(
            name=course.name,
            description=course.description
        )
        
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        # Get lecture count (will be 0 for new course)
        lecture_count = db.query(LectureDB).filter(LectureDB.course_id == db_course.id).count()
        
        return CourseResponse(
            id=db_course.id,
            name=db_course.name,
            description=db_course.description,
            lecture_count=lecture_count,
            created_at=db_course.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating course: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course and all its lectures and documents."""
    try:
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        logger.info(f"Deleting course {course_id}: {course.name}")
        
        # Get all lectures in this course
        lectures = db.query(LectureDB).filter(LectureDB.course_id == course_id).all()
        
        total_documents_deleted = 0
        
        # Delete each lecture and its documents
        for lecture in lectures:
            # Get all documents in this lecture
            documents = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture.id).all()
            
            # Delete each document (this will handle cleanup of chunks, embeddings, AI notes, and files)
            for document in documents:
                # Delete AI notes
                ai_notes = db.query(AINotesDB).filter(AINotesDB.document_id == document.id).all()
                for note in ai_notes:
                    db.delete(note)
                
                # Delete chunks and their embeddings
                chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document.id).all()
                embedding_ids_to_remove = []
                
                for chunk in chunks:
                    if chunk.embedding_id:
                        embedding_ids_to_remove.append(chunk.embedding_id)
                    db.delete(chunk)
                
                # Remove embeddings from vector store
                if embedding_ids_to_remove:
                    try:
                        vector_store.delete_vectors(embedding_ids_to_remove)
                    except Exception as e:
                        logger.warning(f"Failed to delete embeddings from vector store: {e}")
                
                # Delete associated files
                if document.file_path and os.path.exists(document.file_path):
                    os.remove(document.file_path)
                
                # Delete chunks file if it exists
                chunks_file = os.path.join(
                    settings.CHUNKS_DIR, 
                    f"document_{document.id}_chunks.json"
                )
                if os.path.exists(chunks_file):
                    os.remove(chunks_file)
                
                # Delete document record
                db.delete(document)
                total_documents_deleted += 1
            
            # Delete the lecture
            db.delete(lecture)
        
        # Delete the course
        db.delete(course)
        db.commit()
        
        return {
            "message": "Course deleted successfully",
            "details": {
                "course_id": course_id,
                "course_name": course.name,
                "lectures_deleted": len(lectures),
                "documents_deleted": total_documents_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")

@app.get("/courses", response_model=List[CourseResponse])
async def get_courses(db: Session = Depends(get_db)):
    """Get all courses with lecture counts."""
    try:
        courses = db.query(CourseDB).all()
        
        course_responses = []
        for course in courses:
            # Check if lectures table exists and has data
            try:
                lecture_count = db.query(LectureDB).filter(LectureDB.course_id == course.id).count()
            except Exception:
                # If lectures table doesn't exist yet, default to 0
                lecture_count = 0
            
            course_responses.append(CourseResponse(
                id=course.id,
                name=course.name,
                description=course.description,
                lecture_count=lecture_count,
                created_at=course.created_at
            ))
        
        return course_responses
        
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a specific course by ID."""
    try:
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check if lectures table exists and has data
        try:
            lecture_count = db.query(LectureDB).filter(LectureDB.course_id == course.id).count()
        except Exception:
            # If lectures table doesn't exist yet, default to 0
            lecture_count = 0
        
        return CourseResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            lecture_count=lecture_count,
            created_at=course.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/lectures", response_model=List[LectureResponse])
async def get_course_lectures(course_id: int, db: Session = Depends(get_db)):
    """Get all lectures in a specific course."""
    try:
        # Verify course exists
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Get lectures
        lectures = db.query(LectureDB).filter(LectureDB.course_id == course_id).all()
        
        lecture_responses = []
        for lecture in lectures:
            document_count = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture.id).count()
            lecture_responses.append(LectureResponse(
                id=lecture.id,
                title=lecture.title,
                description=lecture.description,
                lecture_date=lecture.lecture_date,
                created_at=lecture.created_at,
                course_id=lecture.course_id,
                document_count=document_count
            ))
        
        return lecture_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lectures for course {course_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Lecture Management Endpoints
@app.post("/courses/{course_id}/lectures", response_model=LectureResponse)
async def create_lecture(course_id: int, lecture: LectureCreate, db: Session = Depends(get_db)):
    """Create a new lecture in a course."""
    try:
        # Verify course exists
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Create new lecture
        db_lecture = LectureDB(
            title=lecture.title,
            description=lecture.description,
            lecture_date=lecture.lecture_date,
            course_id=course_id
        )
        
        db.add(db_lecture)
        db.commit()
        db.refresh(db_lecture)
        
        return LectureResponse(
            id=db_lecture.id,
            title=db_lecture.title,
            description=db_lecture.description,
            lecture_date=db_lecture.lecture_date,
            created_at=db_lecture.created_at,
            course_id=db_lecture.course_id,
            document_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lecture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lectures/{lecture_id}", response_model=LectureResponse)
async def get_lecture(lecture_id: int, db: Session = Depends(get_db)):
    """Get a specific lecture by ID."""
    try:
        lecture = db.query(LectureDB).filter(LectureDB.id == lecture_id).first()
        
        if not lecture:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        document_count = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture.id).count()
        
        return LectureResponse(
            id=lecture.id,
            title=lecture.title,
            description=lecture.description,
            lecture_date=lecture.lecture_date,
            created_at=lecture.created_at,
            course_id=lecture.course_id,
            document_count=document_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lecture {lecture_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lectures/{lecture_id}/documents", response_model=List[DocumentResponse])
async def get_lecture_documents(lecture_id: int, db: Session = Depends(get_db)):
    """Get all documents in a specific lecture."""
    try:
        # Verify lecture exists
        lecture = db.query(LectureDB).filter(LectureDB.id == lecture_id).first()
        if not lecture:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        # Get documents
        documents = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture_id).all()
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents for lecture {lecture_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/lectures/{lecture_id}")
async def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    """Delete a lecture and all its documents."""
    try:
        lecture = db.query(LectureDB).filter(LectureDB.id == lecture_id).first()
        if not lecture:
            raise HTTPException(status_code=404, detail="Lecture not found")
        
        logger.info(f"Deleting lecture {lecture_id}: {lecture.title}")
        
        # Get all documents in this lecture
        documents = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture_id).all()
        
        # Delete each document (this will handle cleanup of chunks, embeddings, AI notes, and files)
        for document in documents:
            # Delete AI notes
            ai_notes = db.query(AINotesDB).filter(AINotesDB.document_id == document.id).all()
            for note in ai_notes:
                db.delete(note)
            
            # Delete chunks and their embeddings
            chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document.id).all()
            embedding_ids_to_remove = []
            
            for chunk in chunks:
                if chunk.embedding_id:
                    embedding_ids_to_remove.append(chunk.embedding_id)
                db.delete(chunk)
            
            # Remove embeddings from vector store
            if embedding_ids_to_remove:
                try:
                    vector_store.delete_vectors(embedding_ids_to_remove)
                except Exception as e:
                    logger.warning(f"Failed to delete embeddings from vector store: {e}")
            
            # Delete associated files
            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete chunks file if it exists
            chunks_file = os.path.join(
                settings.CHUNKS_DIR, 
                f"document_{document.id}_chunks.json"
            )
            if os.path.exists(chunks_file):
                os.remove(chunks_file)
            
            # Delete document record
            db.delete(document)
        
        # Delete the lecture
        db.delete(lecture)
        db.commit()
        
        return {
            "message": "Lecture deleted successfully",
            "details": {
                "lecture_id": lecture_id,
                "lecture_title": lecture.title,
                "documents_deleted": len(documents)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lecture {lecture_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete lecture: {str(e)}")

@app.post("/courses/{course_id}/query")
async def query_course(
    course_id: int,
    query: QueryRequest,
    db: Session = Depends(get_db)
):
    """Query across all documents in a specific course using RAG."""
    try:
        # Verify course exists
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check if course has any documents through its lectures
        document_count = db.query(DocumentDB).join(LectureDB).filter(
            LectureDB.course_id == course_id,
            DocumentDB.processed == "completed"
        ).count()
        
        if document_count == 0:
            return {
                "answer": f"Course '{course.name}' has no processed documents yet. Please upload some documents first.",
                "citations": [],
                "chunks": [],
                "success": False
            }
        
        # Perform RAG query on the course
        result = rag_service.query_course(
            user_input=query.question,
            course_id=course_id,
            max_results=query.max_results or 5
        )
        
        return {
            "answer": result["answer"],
            "citations": result["citations"],
            "chunks": result.get("chunks", []),
            "success": result["success"],
            "model_info": result.get("model_info", {}),
            "course_info": {
                "course_id": course_id,
                "course_name": course.name,
                "document_count": document_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in course query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/rebuild-index")
async def rebuild_course_index(course_id: int, db: Session = Depends(get_db)):
    """Rebuild the course index from existing chunks."""
    try:
        # Verify course exists
        course = db.query(CourseDB).filter(CourseDB.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Get all lectures for this course
        lectures = db.query(LectureDB).filter(LectureDB.course_id == course_id).all()
        if not lectures:
            return {"message": f"No lectures found for course {course_id}"}
        
        total_chunks = 0
        total_documents = 0
        
        # Process each lecture
        for lecture in lectures:
            documents = db.query(DocumentDB).filter(DocumentDB.lecture_id == lecture.id).all()
            
            for document in documents:
                if document.processed != "completed":
                    continue
                
                # Get chunks for this document
                chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document.id).all()
                if not chunks:
                    continue
                
                # Prepare embeddings and metadata
                embeddings = []
                metadata_list = []
                
                for chunk in chunks:
                    # Regenerate embedding for this chunk
                    try:
                        embedding = embedding_service.encode_text(chunk.content)
                        embeddings.append(embedding)
                        
                        # Prepare metadata
                        metadata = json.loads(chunk.chunk_metadata) if chunk.chunk_metadata else {}
                        metadata.update({
                            "text": chunk.content,
                            "filename": document.filename,
                            "lecture_id": lecture.id,
                            "course_id": course_id,
                            "document_id": document.id,
                            "chunk_index": chunk.chunk_index
                        })
                        metadata_list.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for chunk {chunk.id}: {e}")
                        continue
                
                if embeddings and metadata_list:
                    # Add to course index
                    vector_ids = vector_store.add_course_vectors(
                        course_id=course_id,
                        document_id=document.id,
                        vectors=embeddings,
                        metadata_list=metadata_list
                    )
                    total_chunks += len(vector_ids)
                    total_documents += 1
                    logger.info(f"Added {len(vector_ids)} chunks from document {document.id} to course {course_id}")
        
        # Save the course index
        vector_store.save_course_index(course_id)
        
        return {
            "message": f"Successfully rebuilt course index for course {course_id}",
            "course_id": course_id,
            "course_name": course.name,
            "lectures_processed": len(lectures),
            "documents_processed": total_documents,
            "chunks_added": total_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding course index for course {course_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rebuild course index: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/status")
async def get_status():
    """Get system status and configuration."""
    return {
        "api": "healthy",
        "config": settings.get_status(),
        "services": {
            "embedding_service": embedding_service.is_available(),
            "vector_store": vector_store.is_available(),
            "document_processor": True,
            "rag_service": rag_service.is_configured()
        },
        "timestamp": datetime.now()
    }

@app.post("/documents/{document_id}/generate-notes")
async def generate_ai_notes(
    document_id: int,
    request: AINotesGenerate = AINotesGenerate(),
    db: Session = Depends(get_db)
):
    """Generate AI study notes for a document."""
    try:
        # Check if document exists
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is processed (handle both regular documents and audio files)
        if document.is_audio == "true":
            # For audio files, check transcription status
            if document.transcription_status != "completed":
                raise HTTPException(status_code=400, detail="Audio transcription is not yet completed")
        else:
            # For regular documents, check processing status
            if document.processed != "completed":
                raise HTTPException(status_code=400, detail="Document is not yet processed")
        
        # Check if notes already exist and regeneration is not requested
        existing_notes = db.query(AINotesDB).filter(AINotesDB.document_id == document_id).first()
        if existing_notes and not request.regenerate:
            return {
                "message": "AI notes already exist for this document",
                "notes_id": existing_notes.id,
                "generated_at": existing_notes.generated_at
            }
        
        # Get document chunks or use transcript for audio files
        chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document_id).all()
        
        if not chunks:
            # For audio files, try to use the transcript directly if chunks don't exist
            if document.is_audio == "true" and document.transcript:
                # Use the transcript directly for AI notes generation
                chunk_data = [{"content": document.transcript}]
            else:
                raise HTTPException(status_code=400, detail="No document chunks found and no transcript available")
        else:
            # Convert chunks to the format expected by the RAG service
            chunk_data = [{"content": chunk.content} for chunk in chunks]
        
        # Generate notes using RAG service
        result = rag_service.generate_document_notes(chunk_data, document.filename)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate notes"))
        
        # Save or update notes in database
        if existing_notes:
            # Update existing notes
            existing_notes.notes = result["notes"]
            existing_notes.generated_at = datetime.utcnow()
            existing_notes.model_used = result.get("model_used")
            db.commit()
            notes_record = existing_notes
        else:
            # Create new notes record
            notes_record = AINotesDB(
                document_id=document_id,
                notes=result["notes"],
                model_used=result.get("model_used")
            )
            db.add(notes_record)
            db.commit()
            db.refresh(notes_record)
        
        return {
            "message": "AI notes generated successfully",
            "notes_id": notes_record.id,
            "generated_at": notes_record.generated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{document_id}/notes", response_model=AINotesResponse)
async def get_ai_notes(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get AI-generated notes for a document."""
    try:
        # Check if document exists
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get AI notes
        notes = db.query(AINotesDB).filter(AINotesDB.document_id == document_id).first()
        if not notes:
            raise HTTPException(status_code=404, detail="No AI notes found for this document")
        
        return notes
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document chunks for viewing original content."""
    try:
        # Check if document exists
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get document chunks
        chunks = db.query(ChunkDB).filter(ChunkDB.document_id == document_id).order_by(ChunkDB.chunk_index).all()
        
        # Format chunks for frontend
        formatted_chunks = []
        for chunk in chunks:
            chunk_metadata = json.loads(chunk.chunk_metadata) if chunk.chunk_metadata else {}
            formatted_chunks.append({
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "metadata": chunk_metadata
            })
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "total_chunks": len(formatted_chunks),
            "chunks": formatted_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{document_id}/transcription-status")
async def get_transcription_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get transcription status for an audio document."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.is_audio != "true":
            raise HTTPException(status_code=400, detail="Document is not an audio file")
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "transcription_status": document.transcription_status,
            "audio_duration": document.audio_duration,
            "progress_percentage": 100 if document.transcription_status == "completed" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcription status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{document_id}/transcript")
async def get_transcript(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get transcript for an audio document."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.is_audio != "true":
            raise HTTPException(status_code=400, detail="Document is not an audio file")
        
        if document.transcription_status != "completed":
            raise HTTPException(status_code=400, detail="Transcription not completed yet")
        
        # Parse transcription metadata
        metadata = {}
        if document.transcription_metadata:
            try:
                metadata = json.loads(document.transcription_metadata)
            except:
                pass
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "transcript": document.transcript or "",
            "audio_duration": document.audio_duration,
            "transcription_metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/with-notes", response_model=List[DocumentWithNotesResponse])
async def get_documents_with_notes(db: Session = Depends(get_db)):
    """Get all documents that have AI notes."""
    try:
        # Query documents that have AI notes
        documents_with_notes = db.query(DocumentDB).join(AINotesDB).all()
        
        # Add course information
        result = []
        for doc in documents_with_notes:
            course = db.query(CourseDB).filter(CourseDB.id == doc.course_id).first()
            doc_response = DocumentWithNotesResponse(
                id=doc.id,
                filename=doc.filename,
                course_id=doc.course_id,
                course_name=course.name if course else "Unknown",
                has_notes=True,
                is_audio=doc.is_audio or "false",
                upload_date=doc.upload_date
            )
            result.append(doc_response)
        
        return result
    except Exception as e:
        logger.error(f"Error getting documents with notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details by ID."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/audio")
async def stream_audio(document_id: int, db: Session = Depends(get_db)):
    """Stream audio file."""
    try:
        document = db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.is_audio != "true":
            raise HTTPException(status_code=400, detail="Document is not an audio file")
        
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Return file response for streaming
        from fastapi.responses import FileResponse
        return FileResponse(
            document.file_path,
            media_type="audio/mpeg",
            filename=document.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
