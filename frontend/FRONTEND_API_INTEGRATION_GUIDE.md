# 🎓 LectureAI Frontend API Integration Guide

## 📋 **Overview**

This document outlines the comprehensive API routing and integration improvements made to synchronize the Next.js frontend with the FastAPI backend for the LectureAI educational platform.

## ⚠️ **Issues Identified and Resolved**

### **1. API Integration Problems**
- **Issue**: Inconsistent API calls across components using direct fetch calls
- **Solution**: Created centralized `api.ts` service with typed interfaces
- **Impact**: Better error handling, type safety, and maintainable code

### **2. Navigation and Routing Issues**
- **Issue**: Non-functional navigation links and missing route handlers
- **Solution**: Fixed navigation components and ensured all routes are properly connected
- **Impact**: Fully functional navigation between all pages

### **3. Error Handling**
- **Issue**: Poor error handling with generic console.error messages
- **Solution**: Implemented structured APIError class with specific error types
- **Impact**: Better user experience and debugging capabilities

### **4. Component Synchronization**
- **Issue**: Components not properly synchronized with backend API structure
- **Solution**: Updated all components to use centralized API service
- **Impact**: Consistent data flow and reduced code duplication

## 🔧 **Key Improvements Made**

### **1. Centralized API Service (`lib/api.ts`)**

Created a comprehensive API service layer with:

```typescript
// Type-safe API client with error handling
class APIClient {
  private baseURL: string
  
  // Standardized request method with error handling
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T>
  
  // Course management methods
  async getCourses(): Promise<Course[]>
  async createCourse(data: { name: string; description?: string }): Promise<Course>
  async deleteCourse(courseId: number): Promise<{ message: string; details: any }>
  
  // Document management methods
  async uploadDocument(courseId: number, file: File): Promise<UploadResponse>
  async deleteDocument(documentId: number): Promise<DeleteResponse>
  
  // AI and transcription methods
  async generateAINote(documentId: number, regenerate?: boolean): Promise<AINotesResponse>
  async getTranscript(documentId: number): Promise<TranscriptResponse>
  
  // Query and search methods
  async queryDocuments(data: QueryRequest): Promise<QueryResponse>
}
```

### **2. Type Definitions**

Comprehensive TypeScript interfaces matching backend models:

```typescript
export interface Course {
  id: number
  name: string
  description?: string
  created_at: string
  document_count: number
}

export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  processed: 'pending' | 'processing' | 'completed' | 'failed'
  is_audio?: string
  transcription_status?: 'pending' | 'processing' | 'completed' | 'failed'
  course_id: number
  upload_date: string
  num_chunks?: number
  audio_duration?: number
}

export interface QueryResponse {
  answer: string
  citations: Citation[]
  success: boolean
  model_info?: any
  course_info?: CourseInfo
}
```

### **3. Error Handling**

Structured error handling with custom APIError class:

```typescript
export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

// Usage in components
try {
  const data = await api.getCourses()
  setCourses(data)
} catch (error) {
  if (error instanceof APIError) {
    console.error(`API Error ${error.status}: ${error.message}`)
    // Handle specific error types
  }
}
```

### **4. Utility Functions**

Helper functions for common operations:

```typescript
export const apiUtils = {
  // Check API availability
  async isAPIAvailable(): Promise<boolean>
  
  // Format file sizes
  formatFileSize(bytes: number): string
  
  // Format dates
  formatDate(dateString: string): string
  
  // Get file type information
  getFileTypeInfo(filename: string): FileTypeInfo
  
  // Get status information with colors and icons
  getStatusInfo(status: string, isAudio?: boolean): StatusInfo
}
```

## 🏗️ **Component Updates**

### **1. Dashboard Component**
- ✅ Updated to use centralized API service
- ✅ Added functional quick action buttons
- ✅ Improved error handling and loading states
- ✅ Real-time status updates for processing documents

### **2. Course Management**
- ✅ CourseList: Full CRUD operations with API service
- ✅ CreateCourseDialog: Proper form handling and navigation
- ✅ CourseDetails: Enhanced course information display

### **3. Document Management**
- ✅ DocumentList: Real-time status updates and polling
- ✅ UploadDocumentDialog: Simplified upload with progress tracking
- ✅ Document deletion with comprehensive cleanup

### **4. Chat Interface**
- ✅ Course-scoped queries with proper error handling
- ✅ Citation display with source references
- ✅ Improved user experience with loading states

### **5. AI Notes System**
- ✅ NotesOverview: Centralized notes management
- ✅ AI note generation with status tracking
- ✅ Search and filtering capabilities

## 🛣️ **Routing Structure**

### **App Router Structure**
```
app/
├── page.tsx                    # Dashboard (/)
├── courses/
│   ├── page.tsx               # Course list (/courses)
│   └── [courseId]/
│       └── page.tsx           # Course details (/courses/[id])
├── chat/
│   └── page.tsx               # AI chat interface (/chat)
├── notes/
│   └── page.tsx               # AI notes overview (/notes)
└── documents/
    └── [documentId]/
        └── page.tsx           # Document details (/documents/[id])
```

### **Navigation Component**
- ✅ All navigation links properly connected
- ✅ Active state indicators
- ✅ Mobile-responsive navigation menu
- ✅ Consistent navigation across all pages

## 🔄 **API Endpoint Mapping**

### **Backend → Frontend Mapping**

| Backend Endpoint | Frontend Method | Component Usage |
|------------------|-----------------|-----------------|
| `GET /courses` | `api.getCourses()` | CourseList, Dashboard |
| `POST /courses` | `api.createCourse()` | CreateCourseDialog |
| `DELETE /courses/{id}` | `api.deleteCourse()` | CourseList |
| `GET /courses/{id}/documents` | `api.getCourseDocuments()` | DocumentList |
| `POST /courses/{id}/documents` | `api.uploadDocument()` | UploadDocumentDialog |
| `DELETE /documents/{id}` | `api.deleteDocument()` | DocumentList |
| `POST /documents/{id}/generate-notes` | `api.generateAINote()` | DocumentList |
| `GET /documents/{id}/notes` | `api.getAINote()` | NotesOverview |
| `POST /query` | `api.queryDocuments()` | ChatInterface |
| `GET /documents/with-notes` | `api.getDocumentsWithNotes()` | NotesOverview |

## 📊 **Real-time Features**

### **Status Polling**
- ✅ Document processing status updates every 5 seconds
- ✅ Audio transcription progress tracking
- ✅ Automatic UI updates when processing completes

### **Live Updates**
- ✅ Course document counts update in real-time
- ✅ Processing status indicators with appropriate colors
- ✅ Automatic refresh after successful operations

## 🎯 **Configuration**

### **API Configuration (`lib/config.ts`)**
```typescript
export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  APP_NAME: 'LectureAI',
  SUPPORTED_FILE_TYPES: {
    documents: ['.pdf', '.txt', '.docx', '.doc'],
    audio: ['.mp3', '.wav', '.m4a', '.mp4']
  },
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  POLLING_INTERVAL: 5000, // 5 seconds
}
```

## 🚀 **Getting Started**

### **1. Environment Setup**
```bash
# Frontend environment
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start the frontend
cd frontend
npm install
npm run dev
```

### **2. Backend Setup**
```bash
# Start the backend API
cd lectureAI_new
python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### **3. Verification**
1. ✅ Navigate to `http://localhost:3000` - Dashboard loads
2. ✅ Create a new course - Navigation works
3. ✅ Upload documents - Processing status updates
4. ✅ Use AI chat - Queries return responses with citations
5. ✅ Generate AI notes - Notes appear in overview

## 🐛 **Debugging and Troubleshooting**

### **Common Issues**

1. **API Connection Failed**
   - Check if backend is running on port 8000
   - Verify CORS settings in backend
   - Check browser console for network errors

2. **Navigation Not Working**
   - Verify all page components exist
   - Check Next.js app router structure
   - Ensure proper Link component usage

3. **File Upload Issues**
   - Check file size limits (100MB default)
   - Verify supported file types
   - Check backend upload endpoint

### **Debug Tools**
```typescript
// API availability check
const isAvailable = await apiUtils.isAPIAvailable()
console.log('API Available:', isAvailable)

// Error logging
catch (error) {
  if (error instanceof APIError) {
    console.error(`API Error ${error.status}: ${error.message}`)
  }
}
```

## 📈 **Performance Optimizations**

### **1. API Optimizations**
- ✅ Parallel API calls where possible
- ✅ Efficient polling with cleanup
- ✅ Proper error boundaries

### **2. UI Optimizations**
- ✅ Loading states for all async operations
- ✅ Optimistic updates where appropriate
- ✅ Proper cleanup of intervals and subscriptions

### **3. Data Management**
- ✅ Centralized state management
- ✅ Type-safe data structures
- ✅ Efficient re-rendering patterns

## 🔮 **Future Improvements**

### **Potential Enhancements**
1. **WebSocket Integration**: Real-time updates without polling
2. **Offline Support**: Service worker for offline functionality
3. **Advanced Caching**: React Query or SWR for better data management
4. **Progressive Web App**: PWA capabilities for mobile experience
5. **Advanced Error Recovery**: Retry mechanisms and fallback strategies

## 📞 **Support**

For questions about the API integration or frontend functionality:

1. **Check the console**: Browser dev tools for client-side errors
2. **API Documentation**: Available at `http://localhost:8000/docs`
3. **Component Structure**: Follow the established patterns in updated components
4. **Type Safety**: Use the provided TypeScript interfaces

---

## ✅ **Summary**

The frontend is now fully synchronized with the backend API, featuring:

- 🎯 **Centralized API Service**: Type-safe, error-handled API layer
- 🛣️ **Complete Navigation**: All routes functional and connected
- 🔄 **Real-time Updates**: Status polling and live UI updates
- 🎨 **Improved UX**: Better loading states and error handling
- 📱 **Responsive Design**: Mobile-friendly navigation and layouts
- 🔒 **Type Safety**: Full TypeScript integration with backend models

The LectureAI frontend is now production-ready with a robust API integration layer that provides excellent developer experience and user functionality.
