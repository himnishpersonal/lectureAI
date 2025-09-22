# 🎓 LectureAI Frontend

A modern Next.js frontend for the LectureAI educational RAG system, built with React, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Course Management**: Create, view, and manage educational courses
- **Document Upload**: Support for PDFs, Word docs, text files, and audio files
- **Audio Transcription**: Real-time status updates for audio processing
- **AI Study Notes**: Generate and view AI-powered study notes
- **RAG Chat Interface**: Contextual Q&A with source citations
- **Responsive Design**: Modern UI with shadcn/ui components
- **Real-time Updates**: Polling for processing status updates

## 🛠️ Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **State Management**: React hooks
- **HTTP Client**: Fetch API
- **Date Handling**: date-fns

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- LectureAI Backend running on `http://localhost:8000`

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env.local
   
   # Edit .env.local with your configuration
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

4. **Open in Browser**
   ```
   http://localhost:3000
   ```

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── courses/           # Course management pages
│   ├── documents/         # Document detail pages
│   ├── notes/            # Notes overview page
│   ├── chat/             # Chat interface page
│   └── layout.tsx        # Root layout
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── course-*.tsx      # Course-related components
│   ├── document-*.tsx    # Document-related components
│   ├── ai-notes-*.tsx    # AI notes components
│   └── chat-*.tsx        # Chat components
├── lib/                   # Utilities and configuration
│   ├── config.ts         # App configuration
│   └── utils.ts          # Utility functions
└── public/               # Static assets
```

## 🔧 Configuration

### API Configuration
Edit `lib/config.ts` to configure API endpoints:

```typescript
export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  POLLING_INTERVAL: 5000, // Status update polling interval
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
}
```

### Environment Variables
Create `.env.local` with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=LectureAI
```

## 📚 Key Components

### Course Management
- `CourseList`: Display and manage courses
- `CreateCourseDialog`: Create new courses
- `CourseDetails`: View course information and documents

### Document Management
- `DocumentList`: Display course documents with status
- `UploadDocumentDialog`: Upload documents and audio files
- `DocumentDetails`: View document content and AI notes

### AI Features
- `AINotesViewer`: Display AI-generated study notes
- `ChatInterface`: RAG-powered Q&A interface
- `TranscriptViewer`: View audio transcriptions

### Real-time Features
- Automatic polling for transcription status
- Real-time UI updates for processing states
- Progress indicators for long-running operations

## 🔌 API Integration

The frontend integrates with the LectureAI backend API:

### Course Endpoints
- `GET /courses` - List courses
- `POST /courses` - Create course
- `GET /courses/{id}/documents` - Get course documents

### Document Endpoints
- `POST /courses/{id}/documents` - Upload document/audio
- `DELETE /documents/{id}` - Delete document
- `GET /documents/{id}/notes` - Get AI notes
- `POST /documents/{id}/generate-notes` - Generate AI notes

### Audio Processing
- `GET /documents/{id}/transcription-status` - Check status
- `GET /documents/{id}/transcript` - Get transcript

### RAG Chat
- `POST /query` - Query documents with RAG

## 🎨 UI/UX Features

- **Dark/Light Mode**: Built-in theme switching
- **Responsive Design**: Mobile-first approach
- **Loading States**: Skeleton loaders and spinners
- **Error Handling**: User-friendly error messages
- **Accessibility**: ARIA labels and keyboard navigation
- **Animations**: Smooth transitions and micro-interactions

## 🚀 Build & Deploy

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run start
```

### Linting
```bash
npm run lint
```

## 🔄 Status Management

The frontend handles various processing states:

### Document States
- **Pending**: Uploaded, awaiting processing
- **Processing**: Being processed/transcribed
- **Completed**: Ready for use
- **Failed**: Processing failed

### Audio States
- **Pending**: Uploaded, awaiting transcription
- **Processing**: Being transcribed
- **Completed**: Transcript ready, AI notes generated
- **Failed**: Transcription failed

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check backend is running on `http://localhost:8000`
   - Verify `NEXT_PUBLIC_API_BASE_URL` in environment

2. **Components Not Loading**
   - Run `npm install` to install dependencies
   - Check for TypeScript errors with `npm run build`

3. **File Upload Issues**
   - Check file size limits in `lib/config.ts`
   - Verify supported file types

4. **Real-time Updates Not Working**
   - Check polling interval configuration
   - Verify backend WebSocket/polling endpoints

## 📞 Support

For technical support or questions about the frontend implementation, refer to:

- Backend API Documentation: `../BACKEND_API_DOCUMENTATION.md`
- Component documentation in individual files
- Next.js documentation: https://nextjs.org/docs

## 🔮 Future Enhancements

- WebSocket integration for real-time updates
- Offline support with service workers
- Advanced file preview capabilities
- Collaborative features
- Enhanced accessibility features