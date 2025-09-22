"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Mic, Download, Calendar, HardDrive, Clock, CheckCircle, AlertCircle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { config } from "@/lib/config"

interface Document {
  id: number
  filename: string
  is_audio: string
  transcription_status?: string
  processed: string
  file_size: number
  upload_date: string
  audio_duration?: number
}

interface DocumentDetailsProps {
  documentId: string
}

export function DocumentDetails({ documentId }: DocumentDetailsProps) {
  const [document, setDocument] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDocument()
  }, [documentId])

  const fetchDocument = async () => {
    try {
      // Note: This endpoint doesn't exist in the API, so we'll simulate it
      // In a real implementation, you'd need to add this endpoint to the backend
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}`)
      if (response.ok) {
        const data = await response.json()
        setDocument(data)
      }
    } catch (error) {
      console.error("Failed to fetch document:", error)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
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

  if (loading) {
    return (
      <Card>
        <CardHeader className="animate-pulse">
          <div className="h-6 bg-muted rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-muted rounded w-3/4"></div>
        </CardHeader>
        <CardContent className="animate-pulse">
          <div className="flex gap-4">
            <div className="h-4 bg-muted rounded w-20"></div>
            <div className="h-4 bg-muted rounded w-20"></div>
            <div className="h-4 bg-muted rounded w-24"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!document) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <p className="text-muted-foreground">Document not found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <CardTitle className="text-2xl flex items-center gap-2">
              {document.is_audio === "true" ? (
                <Mic className="h-6 w-6 text-secondary" />
              ) : (
                <FileText className="h-6 w-6 text-primary" />
              )}
              {document.filename}
            </CardTitle>
            <CardDescription className="text-base">
              {document.is_audio === "true" ? "Audio File" : "Document"}
            </CardDescription>
          </div>
          <div className="flex flex-col items-end gap-2">
            {getStatusBadge(document)}
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{formatFileSize(document.file_size)}</p>
              <p className="text-xs text-muted-foreground">File Size</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">
                {formatDistanceToNow(new Date(document.upload_date), { addSuffix: true })}
              </p>
              <p className="text-xs text-muted-foreground">Uploaded</p>
            </div>
          </div>

          {document.is_audio === "true" && document.audio_duration && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{formatDuration(document.audio_duration)}</p>
                <p className="text-xs text-muted-foreground">Duration</p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{document.is_audio === "true" ? "Audio" : "Document"}</p>
              <p className="text-xs text-muted-foreground">Type</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
