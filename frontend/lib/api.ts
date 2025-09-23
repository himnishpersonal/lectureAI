import { config } from './config'

// Types for API responses
export interface Course {
  id: number
  name: string
  description?: string
  created_at: string
  lecture_count: number
}

export interface Lecture {
  id: number
  title: string
  description?: string
  lecture_date?: string
  created_at: string
  course_id: number
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
  lecture_id: number
  upload_date: string
  num_chunks?: number
  audio_duration?: number
  transcript?: string
}

export interface AINote {
  id: number
  document_id: number
  notes: string
  generated_at: string
  model_used?: string
}

export interface QueryResponse {
  answer: string
  citations: Array<{
    filename: string
    text: string
    similarity_score: number
    chunk_index: number
  }>
  success: boolean
  model_info?: any
  course_info?: {
    course_id: number
    course_name: string
    document_count: number
  }
}

export interface DocumentChunk {
  chunk_index: number
  content: string
  metadata: any
}

export interface DocumentChunksResponse {
  document_id: number
  filename: string
  total_chunks: number
  chunks: DocumentChunk[]
}

// Authentication types
export interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
  daily_api_calls: number
  daily_api_limit: number
  total_documents: number
  total_storage_bytes: number
  storage_limit_bytes: number
}

export interface Session {
  session_id: string
  user: User
  expires_at: string
  created_at: string
}

export interface UsageStats {
  user_id: number
  username: string
  api_usage: {
    daily_calls: number
    daily_limit: number
    percentage: number
    remaining: number
  }
  storage_usage: {
    used_bytes: number
    limit_bytes: number
    percentage: number
    remaining_bytes: number
    used_mb: number
    limit_mb: number
  }
  document_count: number
}

export interface TranscriptResponse {
  document_id: number
  filename: string
  transcript: string
  audio_duration?: number
  transcription_metadata?: any
}

export interface DocumentWithNotes {
  id: number
  filename: string
  course_id: number
  course_name: string
  has_notes: boolean
  is_audio: string
  upload_date: string
}

// API Error class
export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

// Base API client
class APIClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    sessionId?: string
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    }
    
    // Add session ID if provided
    if (sessionId) {
      headers['X-Session-ID'] = sessionId
    }
    
    try {
      const response = await fetch(url, {
        headers,
        ...options,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new APIError(response.status, errorText || response.statusText)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof APIError) {
        throw error
      }
      throw new APIError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Course endpoints (updated to include session ID)
  async getCourses(sessionId?: string): Promise<Course[]> {
    return this.request<Course[]>('/courses', { method: 'GET' }, sessionId)
  }

  async getCourse(courseId: number, sessionId?: string): Promise<Course> {
    return this.request<Course>(`/courses/${courseId}`, { method: 'GET' }, sessionId)
  }

  async createCourse(data: { name: string; description?: string }, sessionId?: string): Promise<Course> {
    return this.request<Course>('/courses', {
      method: 'POST',
      body: JSON.stringify(data),
    }, sessionId)
  }

  async deleteCourse(courseId: number, sessionId?: string): Promise<{ message: string; details: any }> {
    return this.request(`/courses/${courseId}`, {
      method: 'DELETE',
    }, sessionId)
  }

  // Lecture endpoints
  async getCourseLectures(courseId: number, sessionId?: string): Promise<Lecture[]> {
    return this.request<Lecture[]>(`/courses/${courseId}/lectures`, { method: 'GET' }, sessionId)
  }

  async getLecture(lectureId: number, sessionId?: string): Promise<Lecture> {
    return this.request<Lecture>(`/lectures/${lectureId}`, { method: 'GET' }, sessionId)
  }

  async createLecture(courseId: number, data: { title: string; description?: string; lecture_date?: string }, sessionId?: string): Promise<Lecture> {
    return this.request<Lecture>(`/courses/${courseId}/lectures`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, sessionId)
  }

  async deleteLecture(lectureId: number, sessionId?: string): Promise<{ message: string; details: any }> {
    return this.request(`/lectures/${lectureId}`, {
      method: 'DELETE',
    }, sessionId)
  }

  async getLectureDocuments(lectureId: number, sessionId?: string): Promise<Document[]> {
    return this.request<Document[]>(`/lectures/${lectureId}/documents`, { method: 'GET' }, sessionId)
  }

  async uploadDocumentToLecture(lectureId: number, file: File, customName?: string): Promise<{ message: string; document_id: number; filename: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (customName) {
      formData.append('custom_name', customName)
    }

    const response = await fetch(`${this.baseURL}/lectures/${lectureId}/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new APIError(response.status, errorText || response.statusText)
    }

    return await response.json()
  }

  // Document endpoints
  async getDocuments(): Promise<Document[]> {
    return this.request<Document[]>('/documents')
  }

  async getDocument(documentId: number, sessionId?: string): Promise<Document> {
    return this.request<Document>(`/documents/${documentId}`, { method: 'GET' }, sessionId)
  }

  async getCourseDocuments(courseId: number, sessionId?: string): Promise<Document[]> {
    return this.request<Document[]>(`/courses/${courseId}/documents`, { method: 'GET' }, sessionId)
  }

  async deleteDocument(documentId: number, sessionId?: string): Promise<{ message: string; details: any }> {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    }, sessionId)
  }

  async uploadDocument(courseId: number, file: File, customName?: string): Promise<{ message: string; document_id: number; filename: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (customName) {
      formData.append('custom_name', customName)
    }

    const response = await fetch(`${this.baseURL}/courses/${courseId}/documents`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new APIError(response.status, errorText || response.statusText)
    }

    return await response.json()
  }

  // Document chunks
  async getDocumentChunks(documentId: number, sessionId?: string): Promise<DocumentChunksResponse> {
    return this.request<DocumentChunksResponse>(`/documents/${documentId}/chunks`, { method: 'GET' }, sessionId)
  }

  // Transcription endpoints
  async getTranscriptionStatus(documentId: number): Promise<{
    document_id: number
    filename: string
    transcription_status: string
    audio_duration?: number
    progress_percentage?: number
  }> {
    return this.request(`/documents/${documentId}/transcription-status`)
  }

  async getTranscript(documentId: number, sessionId?: string): Promise<TranscriptResponse> {
    return this.request<TranscriptResponse>(`/documents/${documentId}/transcript`, { method: 'GET' }, sessionId)
  }

  // AI Notes endpoints
  async generateAINote(documentId: number, regenerate = false, sessionId?: string): Promise<{
    message: string
    notes_id: number
    generated_at: string
  }> {
    return this.request(`/documents/${documentId}/generate-notes`, {
      method: 'POST',
      body: JSON.stringify({ regenerate }),
    }, sessionId)
  }

  async getAINote(documentId: number, sessionId?: string): Promise<AINote> {
    return this.request<AINote>(`/documents/${documentId}/notes`, { method: 'GET' }, sessionId)
  }

  async getDocumentsWithNotes(sessionId?: string): Promise<DocumentWithNotes[]> {
    return this.request<DocumentWithNotes[]>('/documents/with-notes', { method: 'GET' }, sessionId)
  }

  // Query endpoints
  async queryDocuments(data: {
    question: string
    course_id?: number
    document_ids?: number[]
    max_results?: number
  }): Promise<QueryResponse> {
    return this.request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async queryCourse(courseId: number, data: {
    question: string
    max_results?: number
  }): Promise<QueryResponse> {
    return this.request<QueryResponse>(`/courses/${courseId}/query`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health')
  }

  async getStatus(): Promise<{
    api: string
    config: any
    services: any
    timestamp: string
  }> {
    return this.request('/status')
  }

  // Authentication endpoints
  async login(username: string, password: string): Promise<Session> {
    return this.request<Session>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  }

  async register(username: string, email: string, password: string): Promise<Session> {
    return this.request<Session>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    })
  }

  async logout(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/logout', {
      method: 'POST',
    }, sessionId)
  }

  async getCurrentUser(sessionId: string): Promise<User> {
    return this.request<User>('/auth/me', {
      method: 'GET',
    }, sessionId)
  }

  async getUserUsageStats(sessionId: string): Promise<UsageStats> {
    return this.request<UsageStats>('/auth/usage', {
      method: 'GET',
    }, sessionId)
  }
}

// Export singleton instance
export const api = new APIClient(config.API_BASE_URL)

// Utility functions for common operations
export const apiUtils = {
  // Check if API is available
  async isAPIAvailable(): Promise<boolean> {
    try {
      await api.healthCheck()
      return true
    } catch {
      return false
    }
  },

  // Format file size
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
  },

  // Format date
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString()
  },

  // Get file type info
  getFileTypeInfo(filename: string): {
    isAudio: boolean
    extension: string
    icon: string
  } {
    const extension = filename.split('.').pop()?.toLowerCase() || ''
    const isAudio = ['mp3', 'wav', 'm4a', 'mp4'].includes(extension)
    
    return {
      isAudio,
      extension,
      icon: isAudio ? 'audio' : 'document'
    }
  },

  // Get status color and text
  getStatusInfo(status: string, isAudio = false): {
    color: string
    text: string
    icon: string
  } {
    if (isAudio) {
      switch (status) {
        case 'completed':
          return { color: 'green', text: 'Transcribed', icon: 'check' }
        case 'processing':
          return { color: 'yellow', text: 'Transcribing...', icon: 'clock' }
        case 'failed':
          return { color: 'red', text: 'Failed', icon: 'x' }
        default:
          return { color: 'gray', text: 'Pending', icon: 'clock' }
      }
    } else {
      switch (status) {
        case 'completed':
          return { color: 'green', text: 'Ready', icon: 'check' }
        case 'processing':
          return { color: 'yellow', text: 'Processing...', icon: 'clock' }
        case 'failed':
          return { color: 'red', text: 'Failed', icon: 'x' }
        default:
          return { color: 'gray', text: 'Pending', icon: 'clock' }
      }
    }
  }
}
