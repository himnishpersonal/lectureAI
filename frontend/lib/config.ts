export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  APP_NAME: 'LectureAI',
  APP_DESCRIPTION: 'AI-Powered Educational RAG System for Academic Learning',
  SUPPORTED_FILE_TYPES: {
    documents: ['.pdf', '.txt', '.docx', '.doc'],
    audio: ['.mp3', '.wav', '.m4a', '.mp4']
  },
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  POLLING_INTERVAL: 5000, // 5 seconds for status updates
}
