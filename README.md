# 🎓 LectureAI - Intelligent Course Assistant

An AI-powered educational platform that transforms lectures and documents into interactive learning experiences using RAG (Retrieval-Augmented Generation) technology.

## ✨ Features

- **📚 Course Management**: Create and organize courses with multiple documents
- **🎵 Audio Transcription**: Upload lecture audio files and get automatic transcripts using Faster Whisper
- **🤖 AI-Generated Notes**: Automatically generate study notes from documents and transcripts
- **💬 Intelligent Chat**: Ask questions about your course materials with AI-powered responses
- **📄 Document Processing**: Support for PDF, DOCX, TXT files with automatic chunking and embedding
- **🔍 Smart Search**: Find relevant information across all your course materials
- **🎨 Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## 🏗️ Architecture

### Backend (FastAPI)
- **API Server**: FastAPI with automatic documentation
- **Database**: SQLite with SQLAlchemy ORMcvfcd
- **Vector Store**: FAISS for semantic search
- **AI Services**: OpenAI/OpenRouter integration for LLM responses
- **Transcription**: Faster Whisper for audio processing
- **Embeddings**: Sentence Transformers for document vectorization

### Frontend (Next.js)
- **Framework**: Next.js 15 with TypeScript
- **UI Components**: shadcn/ui component library
- **Styling**: Tailwind CSS with custom theme
- **State Management**: React hooks and context
- **File Upload**: Drag-and-drop with progress tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd lectureAI_new
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Run the backend**
   ```bash
   uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the frontend**
   ```bash
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
lectureAI_new/
├── backend/
│   ├── api.py              # FastAPI application
│   ├── models.py           # Database models
│   ├── services/           # Business logic services
│   │   ├── rag_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   ├── transcription_service.py
│   │   └── document_processor.py
│   └── utils/
│       └── config.py       # Configuration management
├── frontend/
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/               # Utilities and config
│   └── public/            # Static assets
├── data/                  # Database and embeddings
├── requirements.txt       # Python dependencies
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./data/lectureai.db

# AI Services
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# File Storage
UPLOAD_DIR=./data/uploads
CHUNKS_DIR=./data/chunks
EMBEDDINGS_DIR=./data/embeddings

# Application
APP_URL=http://localhost:3000
```

### Frontend Configuration

Update `frontend/lib/config.ts`:

```typescript
export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  POLLING_INTERVAL: 5000,
};
```

## 🎯 Usage

1. **Create a Course**: Start by creating a new course
2. **Upload Materials**: Add documents (PDF, DOCX, TXT) or audio files (MP3, WAV, M4A)
3. **Generate Notes**: Let AI create study notes from your materials
4. **Ask Questions**: Use the chat interface to query your course content
5. **Review Content**: View transcripts, original documents, and AI-generated summaries

## 🛠️ Development

### Backend Development
- API endpoints are documented at `/docs`
- Database migrations handled automatically
- Logs available in console output

### Frontend Development
- Hot reload enabled in development mode
- TypeScript for type safety
- Component-based architecture

## 📝 API Endpoints

### Core Endpoints
- `GET /courses` - List all courses
- `POST /courses` - Create new course
- `GET /courses/{id}/documents` - Get course documents
- `POST /courses/{id}/documents` - Upload document to course
- `POST /query` - Query documents with AI
- `POST /documents/{id}/generate-notes` - Generate AI notes

### Document Management
- `GET /documents/{id}` - Get document details
- `GET /documents/{id}/notes` - Get AI notes
- `GET /documents/{id}/transcript` - Get transcript
- `DELETE /documents/{id}` - Delete document

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Next.js for the React framework
- shadcn/ui for beautiful components
- OpenAI/Anthropic for AI capabilities
- Faster Whisper for audio transcription

---

**Built with ❤️ for better education**