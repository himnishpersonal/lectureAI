"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  ArrowLeft, 
  FileText, 
  Mic, 
  Brain, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Calendar
} from "lucide-react"
import { api, type Document, type DocumentChunksResponse, type AINote, APIError, apiUtils } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface DocumentViewerPageProps {
  courseId: number
  lectureId: number
  documentId: number
}

export function DocumentViewerPage({ courseId, lectureId, documentId }: DocumentViewerPageProps) {
  const router = useRouter()
  const [document, setDocument] = useState<Document | null>(null)
  const [content, setContent] = useState<string>("")
  const [aiNotes, setAiNotes] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"content" | "notes">("content")
  const [notesAvailable, setNotesAvailable] = useState(false)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchDocumentData()
    }
  }, [documentId, session])

  const fetchDocumentData = async () => {
    if (!session?.session_id) return
    
    try {
      const [documentData, chunksResponse, notesResponse] = await Promise.all([
        api.getDocument(documentId, session.session_id),
        api.getDocumentChunks(documentId, session.session_id),
        api.getAINote(documentId, session.session_id).catch(() => null)
      ])

      setDocument(documentData)

      // Combine chunks into full content
      const fullContent = chunksResponse.chunks.map(chunk => chunk.content).join('\n\n')
      setContent(fullContent)

      // Set AI notes
      if (notesResponse && notesResponse.notes) {
        setAiNotes(notesResponse.notes)
        setNotesAvailable(true)
      }
    } catch (error) {
      console.error("Failed to fetch document data:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBackToLecture = () => {
    router.push(`/courses/${courseId}/lectures/${lectureId}`)
  }

  const getStatusIcon = () => {
    if (!document) return null
    
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
    if (!document) return null
    
    return document.is_audio === "true" ? (
      <Mic className="h-5 w-5 text-blue-400" />
    ) : (
      <FileText className="h-5 w-5 text-green-400" />
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-6">
            <Button variant="ghost" size="sm" onClick={handleBackToLecture}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Lecture
            </Button>
          </div>
          
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <CardTitle className="text-white">Loading Document...</CardTitle>
              </div>
            </CardHeader>
          </Card>
        </div>
      </div>
    )
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-6">
            <Button variant="ghost" size="sm" onClick={handleBackToLecture}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Lecture
            </Button>
          </div>
          
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Document Not Found</CardTitle>
              <CardDescription className="text-gray-400">
                The requested document could not be found.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={handleBackToLecture}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Lecture
          </Button>
        </div>

        {/* Document Info */}
        <Card className="bg-gray-900 border-gray-700 mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                {getFileIcon()}
                <div>
                  <CardTitle className="text-white text-xl">{document.filename}</CardTitle>
                  <CardDescription className="text-gray-400 mt-1">
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        {getStatusIcon()}
                        <span className="capitalize">{document.processed}</span>
                      </div>
                      <span>•</span>
                      <span>{apiUtils.formatFileSize(document.file_size)}</span>
                      <span>•</span>
                      <span>{new Date(document.upload_date).toLocaleDateString()}</span>
                    </div>
                  </CardDescription>
                </div>
              </div>
              <Badge variant="outline" className="text-gray-400 border-gray-600">
                {document.is_audio === "true" ? "Audio File" : "Document"}
              </Badge>
            </div>
          </CardHeader>
        </Card>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Content Tab Navigation */}
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <div className="flex gap-2 border-b border-gray-600 pb-4">
                <Button
                  variant={activeTab === "content" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTab("content")}
                  className={activeTab === "content" ? "bg-blue-600 hover:bg-blue-700" : "text-gray-400 hover:text-white"}
                >
                  {document.is_audio === "true" ? "Transcript" : "Content"}
                </Button>
                <Button
                  variant={activeTab === "notes" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setActiveTab("notes")}
                  className={activeTab === "notes" ? "bg-blue-600 hover:bg-blue-700" : "text-gray-400 hover:text-white"}
                >
                  <Brain className="h-4 w-4 mr-1" />
                  AI Notes
                  {!notesAvailable && (
                    <span className="ml-1 text-xs text-yellow-400">(Not Available)</span>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] w-full">
                <div className="pr-4">
                  {activeTab === "content" ? (
                    <pre className="whitespace-pre-wrap text-sm text-gray-300 leading-relaxed">
                      {content || "No content available"}
                    </pre>
                  ) : (
                    <div className="text-sm text-gray-300 leading-relaxed">
                      {notesAvailable ? (
                        <div dangerouslySetInnerHTML={{ __html: aiNotes.replace(/\n/g, '<br>') }} />
                      ) : (
                        <div className="text-center py-8">
                          <Brain className="h-12 w-12 text-gray-500 mx-auto mb-4" />
                          <p className="text-gray-400 mb-4">AI notes not available</p>
                          <p className="text-gray-500 text-sm">
                            AI notes may not have been generated for this document yet.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Document Metadata */}
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Document Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">File Type:</span>
                  <p className="text-white">{document.file_type}</p>
                </div>
                <div>
                  <span className="text-gray-400">File Size:</span>
                  <p className="text-white">{apiUtils.formatFileSize(document.file_size)}</p>
                </div>
                <div>
                  <span className="text-gray-400">Upload Date:</span>
                  <p className="text-white">{new Date(document.upload_date).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-gray-400">Status:</span>
                  <p className="text-white capitalize">{document.processed}</p>
                </div>
                {document.num_chunks && (
                  <div>
                    <span className="text-gray-400">Chunks:</span>
                    <p className="text-white">{document.num_chunks}</p>
                  </div>
                )}
                {document.is_audio === "true" && document.audio_duration && (
                  <div>
                    <span className="text-gray-400">Duration:</span>
                    <p className="text-white">{Math.round(document.audio_duration)}s</p>
                  </div>
                )}
              </div>

              {document.is_audio === "true" && (
                <div className="pt-4 border-t border-gray-600">
                  <h4 className="text-white font-medium mb-2">Audio Information</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Transcription:</span>
                      <p className="text-white capitalize">{document.transcription_status || "pending"}</p>
                    </div>
                    {document.audio_duration && (
                      <div>
                        <span className="text-gray-400">Duration:</span>
                        <p className="text-white">{Math.round(document.audio_duration)} seconds</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {notesAvailable && (
                <div className="pt-4 border-t border-gray-600">
                  <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                    <Brain className="h-4 w-4" />
                    AI Notes Available
                  </h4>
                  <p className="text-gray-400 text-sm">
                    AI-generated study notes are ready for this document.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
