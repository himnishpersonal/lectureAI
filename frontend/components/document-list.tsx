"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  FileText,
  Mic,
  Download,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  MoreVertical,
  Eye,
  Brain,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { formatDistanceToNow } from "date-fns"
import { api, type Document, APIError, apiUtils } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface DocumentListProps {
  courseId: string
}

export function DocumentList({ courseId }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchDocuments()
      // Set up polling for processing status updates
      const interval = setInterval(fetchDocuments, 5000)
      return () => clearInterval(interval)
    }
  }, [courseId, session])

  const fetchDocuments = async () => {
    if (!session?.session_id) return
    
    try {
      const data = await api.getCourseDocuments(Number.parseInt(courseId), session.session_id)
      setDocuments(data)
    } catch (error) {
      console.error("Failed to fetch documents:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const deleteDocument = async (documentId: number) => {
    if (!session?.session_id) return
    
    try {
      await api.deleteDocument(documentId, session.session_id)
      setDocuments(documents.filter((doc) => doc.id !== documentId))
    } catch (error) {
      console.error("Failed to delete document:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    }
  }

  const generateNotes = async (documentId: number) => {
    if (!session?.session_id) return
    
    try {
      await api.generateAINote(documentId, false, session.session_id)
      // Refresh documents to show updated status
      fetchDocuments()
    } catch (error) {
      console.error("Failed to generate notes:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    }
  }


  const getStatusBadge = (doc: Document) => {
    if (doc.is_audio === "true") {
      switch (doc.transcription_status) {
        case "pending":
          return (
            <Badge variant="outline" className="text-yellow-600 border-yellow-200">
              <Clock className="h-3 w-3 mr-1" />
              Transcription Pending
            </Badge>
          )
        case "processing":
          return (
            <Badge variant="outline" className="text-blue-600 border-blue-200">
              <Clock className="h-3 w-3 mr-1" />
              Transcribing...
            </Badge>
          )
        case "completed":
          return (
            <Badge variant="outline" className="text-green-600 border-green-200">
              <CheckCircle className="h-3 w-3 mr-1" />
              Transcribed
            </Badge>
          )
        case "failed":
          return (
            <Badge variant="outline" className="text-red-600 border-red-200">
              <AlertCircle className="h-3 w-3 mr-1" />
              Transcription Failed
            </Badge>
          )
      }
    }

    switch (doc.processed) {
      case "pending":
        return (
          <Badge variant="outline" className="text-yellow-600 border-yellow-200">
            <Clock className="h-3 w-3 mr-1" />
            Processing Pending
          </Badge>
        )
      case "processing":
        return (
          <Badge variant="outline" className="text-blue-600 border-blue-200">
            <Clock className="h-3 w-3 mr-1" />
            Processing...
          </Badge>
        )
      case "completed":
        return (
          <Badge variant="outline" className="text-green-600 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Ready
          </Badge>
        )
      case "failed":
        return (
          <Badge variant="outline" className="text-red-600 border-red-200">
            <AlertCircle className="h-3 w-3 mr-1" />
            Processing Failed
          </Badge>
        )
    }
  }

  const formatFileSize = apiUtils.formatFileSize

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-3 bg-muted rounded w-full mb-2"></div>
              <div className="h-3 bg-muted rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No materials uploaded yet</h3>
          <p className="text-muted-foreground mb-4">
            Upload documents and audio files to get started with AI-powered study notes
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {documents.map((doc) => (
        <Card key={doc.id} className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
            <div className="space-y-1 flex-1">
              <CardTitle className="text-base flex items-center gap-2">
                {doc.is_audio === "true" ? (
                  <Mic className="h-4 w-4 text-secondary" />
                ) : (
                  <FileText className="h-4 w-4 text-primary" />
                )}
                <span className="line-clamp-1">{doc.filename}</span>
              </CardTitle>
              <CardDescription className="text-xs">
                {formatFileSize(doc.file_size)} • {formatDistanceToNow(new Date(doc.upload_date), { addSuffix: true })}
              </CardDescription>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Eye className="h-4 w-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </DropdownMenuItem>
                {(doc.processed === "completed" || doc.transcription_status === "completed") && (
                  <DropdownMenuItem onClick={() => generateNotes(doc.id)}>
                    <Brain className="h-4 w-4 mr-2" />
                    Generate AI Notes
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem className="text-destructive" onClick={() => deleteDocument(doc.id)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Status Badge */}
            <div className="flex items-center justify-between">
              {getStatusBadge(doc)}
              {doc.is_audio === "true" && doc.audio_duration && (
                <span className="text-xs text-muted-foreground">{formatDuration(doc.audio_duration)}</span>
              )}
            </div>

            {/* Processing Progress for Audio */}
            {doc.is_audio === "true" && doc.transcription_status === "processing" && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Transcribing audio...</span>
                  <span>Processing</span>
                </div>
                <Progress value={undefined} className="h-1" />
              </div>
            )}

            {/* Processing Progress for Documents */}
            {doc.processed === "processing" && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Processing document...</span>
                  <span>Processing</span>
                </div>
                <Progress value={undefined} className="h-1" />
              </div>
            )}

            {/* File Type Badge and Actions */}
            <div className="flex items-center justify-between">
              <Badge variant="secondary" className="text-xs">
                {doc.is_audio === "true" ? "Audio File" : "Document"}
              </Badge>
              {(doc.processed === "completed" || doc.transcription_status === "completed") && (
                <Button size="sm" variant="outline" onClick={() => generateNotes(doc.id)}>
                  <Brain className="h-3 w-3 mr-1" />
                  AI Notes
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
