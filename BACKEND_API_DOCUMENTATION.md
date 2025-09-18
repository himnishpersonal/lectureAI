# 🎓 LectureAI Backend API Documentation

## 📋 **System Overview**

**LectureAI** is an AI-powered educational RAG (Retrieval-Augmented Generation) system that processes course materials (documents and audio lectures), generates intelligent study notes, and provides contextual Q&A capabilities.

### **Core Technologies:**
- **FastAPI** (Python backend)
- **SQLAlchemy** (ORM with SQLite database)
- **Faster Whisper** (audio transcription)
- **OpenRouter API** (LLM integration)
- **Vector embeddings** (RAG search)
- **Async processing** (for long-running tasks)

---

## 🗄️ **Database Schema**

### **Tables:**
1. **`courses`** - Course containers
2. **`documents`** - Files (documents + audio with transcripts)
3. **`chunks`** - Text segments for RAG search
4. **`ai_notes`** - AI-generated study notes

### **Key Document Fields:**
```python
# Regular Documents vs Audio Files
is_audio: "true" | "false"
transcription_status: "pending" | "processing" | "completed" | "failed"
processed: "pending" | "processing" | "completed" | "failed"
transcript: str  # Full transcript text for audio
audio_duration: float  # Seconds
```

---

## 🔌 **API Endpoints**

### **🎯 Base URL:** `http://localhost:8000`

### **📚 Course Management**
```http
GET    /courses                    # List all courses
POST   /courses                    # Create new course
GET    /courses/{course_id}/documents  # Get course documents
```

### **📄 Document Management**
```http
POST   /courses/{course_id}/documents   # Upload document/audio
DELETE /documents/{document_id}         # Delete document + cleanup
```

### **🎵 Audio Processing**
```http
GET /documents/{document_id}/transcription-status  # Check transcription
GET /documents/{document_id}/transcript            # Get full transcript
```

### **🤖 AI Notes**
```http
POST /documents/{document_id}/generate-notes  # Generate AI study notes
GET  /documents/{document_id}/notes           # Retrieve existing notes
```

### **🔍 RAG Search & Chat**
```http
POST /query  # Query documents with RAG (course-scoped)
GET  /documents/{document_id}/chunks  # Get document chunks
```

---

## 📊 **Data Flow Architecture**

### **Document Upload Flow:**
1. **File Upload** → Saved to `/data/uploads/`
2. **Document Processing** → Text extraction + chunking
3. **Embedding Generation** → Vector embeddings for search
4. **Database Storage** → Document + chunks + embeddings

### **Audio Upload Flow:**
1. **Audio Upload** → Saved with `transcription_status="pending"`
2. **Async Transcription** → Faster Whisper processing
3. **Text Processing** → Transcript chunking + embeddings
4. **Auto AI Notes** → Generated after 0.5s delay
5. **Status Updates** → `transcription_status="completed"`

### **RAG Query Flow:**
1. **User Query** → Vector similarity search
2. **Context Retrieval** → Relevant chunks from course
3. **LLM Generation** → Contextual response with citations
4. **Response** → Answer + source references

---

## 🎛️ **Request/Response Models**

### **Document Upload**
```python
# POST /courses/{course_id}/documents
Content-Type: multipart/form-data
files: UploadFile

# Response
{
  "id": 123,
  "filename": "lecture.mp3",
  "is_audio": "true",
  "transcription_status": "pending",
  "file_size": 15728640,
  "upload_date": "2025-09-15T10:30:00"
}
```

### **AI Notes Generation**
```python
# POST /documents/{document_id}/generate-notes
{
  "regenerate": false  # Optional: force regeneration
}

# Response
{
  "message": "AI notes generated successfully",
  "notes_id": 456,
  "generated_at": "2025-09-15T10:35:00"
}
```

### **RAG Query**
```python
# POST /query
{
  "query": "What did the professor say about French resistance?",
  "course_id": 1,
  "max_results": 5
}

# Response
{
  "answer": "The professor discussed...",
  "citations": [
    {
      "filename": "yale_ww2_lecture.mp3",
      "text": "relevant excerpt...",
      "similarity_score": 0.89,
      "chunk_index": 12
    }
  ]
}
```

### **Document Deletion**
```python
# DELETE /documents/{document_id}
# Response
{
  "message": "Document deleted successfully",
  "details": {
    "document_id": 123,
    "filename": "lecture.mp3",
    "ai_notes_deleted": 1,
    "chunks_deleted": 25,
    "embeddings_deleted": 25,
    "files_deleted": 2
  }
}
```

---

## 🔧 **File System Structure**
```
data/
├── uploads/           # Original uploaded files
├── chunks/           # JSON chunk files
├── vectors/          # Vector embeddings (course-based)
└── journalism.db     # SQLite database
```

---

## ⚡ **Key Features for Frontend**

### **Real-time Status Updates**
- Audio transcription progress tracking
- Auto-refresh for processing files
- Status indicators: pending → processing → completed

### **Document Types Support**
- **Documents:** PDF, TXT, DOCX
- **Audio:** MP3, WAV, M4A, MP4
- **Processing:** Text extraction vs transcription

### **AI Capabilities**
- **Study Notes:** Auto-generated from content
- **RAG Search:** Course-scoped intelligent search
- **Contextual Chat:** Q&A with source citations

### **Data Management**
- **Complete Cleanup:** Delete removes all associated data
- **Course Organization:** Documents grouped by course
- **Chunk Visibility:** Access to processed segments

---

## 🚨 **Error Handling**

### **Common Error Responses:**
```python
# 404 Not Found
{"detail": "Document not found"}

# 400 Bad Request  
{"detail": "Document is not yet processed"}

# 500 Internal Server Error
{"detail": "Failed to delete document: [reason]"}
```

### **Audio-Specific Errors:**
- `"Audio transcription is not yet completed"`
- `"No document chunks found and no transcript available"`

---

## 🎯 **Frontend Integration Notes**

1. **Async Operations:** Handle long-running transcription with polling
2. **File Type Detection:** Check `is_audio` field for UI rendering
3. **Status Management:** Different workflows for documents vs audio
4. **Course Context:** All operations are course-scoped
5. **Cleanup Awareness:** Deletion removes ALL associated data
6. **Citation Display:** RAG responses include source references

This backend provides a complete educational content management system with AI-powered features, ready for any frontend framework integration.

---

## 📞 **Contact & Support**

For questions about this API documentation or backend implementation details, please reach out to the development team.

**Backend Server:** Running on `http://localhost:8000`
**API Documentation:** Available at `http://localhost:8000/docs` (Swagger UI)
