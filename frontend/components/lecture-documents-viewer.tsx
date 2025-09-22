"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  FileText, 
  Mic, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Eye,
  Calendar
} from "lucide-react"
import { api, type Document, APIError, apiUtils } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface LectureDocumentsViewerProps {
  lectureId: number
  lectureTitle: string
  courseId: number
}

export function LectureDocumentsViewer({ lectureId, lectureTitle, courseId }: LectureDocumentsViewerProps) {
  const router = useRouter()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchDocuments()
    }
  }, [lectureId, session])

  const fetchDocuments = async () => {
    if (!session?.session_id) return
    
    try {
      const documentsData = await api.getLectureDocuments(lectureId, session.session_id)
      setDocuments(documentsData)
    } catch (error) {
      console.error("Failed to fetch lecture documents:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDocumentClick = (document: Document) => {
    // Navigate to the dedicated document page
    router.push(`/courses/${courseId}/lectures/${lectureId}/documents/${document.id}`)
  }

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <CardTitle className="text-white">Loading Materials...</CardTitle>
          </div>
        </CardHeader>
      </Card>
    )
  }

  if (documents.length === 0) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {lectureTitle} - Materials
          </CardTitle>
          <CardDescription className="text-gray-400">
            No materials uploaded yet
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500 text-sm">
            Upload documents or audio files to see them here.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {lectureTitle} - Materials ({documents.length})
        </CardTitle>
        <CardDescription className="text-gray-400">
          Click on any material to view its content and AI notes
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {documents.map((document) => (
          <DocumentCard 
            key={document.id} 
            document={document} 
            onClick={() => handleDocumentClick(document)}
          />
        ))}
      </CardContent>
    </Card>
  )
}

interface DocumentCardProps {
  document: Document
  onClick: () => void
}

function DocumentCard({ document, onClick }: DocumentCardProps) {
  const getStatusIcon = () => {
    switch (document.processed) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "processing":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />
    }
  }

  const getFileIcon = () => {
    return document.is_audio === "true" ? (
      <Mic className="h-4 w-4 text-blue-400" />
    ) : (
      <FileText className="h-4 w-4 text-green-400" />
    )
  }

  return (
    <Card 
      className="bg-gray-800 border-gray-600 hover:bg-gray-750 cursor-pointer transition-colors"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getFileIcon()}
            <div>
              <h4 className="font-medium text-white">{document.filename}</h4>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                {getStatusIcon()}
                <span className="capitalize">{document.processed}</span>
                <span>•</span>
                <span>{apiUtils.formatFileSize(document.file_size)}</span>
                <span>•</span>
                <span>{new Date(document.upload_date).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-400">View</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
