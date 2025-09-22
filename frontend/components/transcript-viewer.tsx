"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Download, Copy, Search, Clock, CheckCircle, AlertCircle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { config } from "@/lib/config"

interface TranscriptViewerProps {
  documentId: number
  filename: string
  transcriptionStatus?: string
}

export function TranscriptViewer({ documentId, filename, transcriptionStatus }: TranscriptViewerProps) {
  const [transcript, setTranscript] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTranscript()
  }, [documentId, transcriptionStatus])

  const fetchTranscript = async () => {
    if (transcriptionStatus !== "completed") {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/transcript`)
      if (response.ok) {
        const data = await response.json()
        setTranscript(data.transcript || "")
      } else {
        setError("Failed to load transcript")
      }
    } catch (error) {
      console.error("Failed to fetch transcript:", error)
      setError("Failed to load transcript")
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcript)
  }

  const downloadTranscript = () => {
    const blob = new Blob([transcript], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${filename.replace(/\.[^/.]+$/, "")}_transcript.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getStatusBadge = () => {
    switch (transcriptionStatus) {
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
            Transcription Complete
          </Badge>
        )
      case "failed":
        return (
          <Badge variant="outline" className="text-red-600 border-red-200">
            <AlertCircle className="h-3 w-3 mr-1" />
            Transcription Failed
          </Badge>
        )
      default:
        return null
    }
  }

  const highlightSearchTerm = (text: string) => {
    if (!searchTerm.trim()) return text

    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi")
    return text.replace(regex, "<mark class='bg-yellow-200 dark:bg-yellow-800'>$1</mark>")
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Transcript
            </CardTitle>
            <CardDescription>{filename}</CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {transcriptionStatus === "pending" && (
          <div className="text-center py-8">
            <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Transcription Pending</h3>
            <p className="text-muted-foreground">
              Your audio file is queued for transcription. This usually takes a few minutes.
            </p>
          </div>
        )}

        {transcriptionStatus === "processing" && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold mb-2">Transcribing Audio</h3>
            <p className="text-muted-foreground">
              Please wait while we convert your audio to text. This may take several minutes depending on the file
              length.
            </p>
          </div>
        )}

        {transcriptionStatus === "failed" && (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Transcription Failed</h3>
            <p className="text-muted-foreground">
              We encountered an error while transcribing your audio file. Please try uploading again.
            </p>
          </div>
        )}

        {transcriptionStatus === "completed" && (
          <>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading transcript...</p>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Error Loading Transcript</h3>
                <p className="text-muted-foreground">{error}</p>
              </div>
            ) : (
              <>
                {/* Search and Actions */}
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search in transcript..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={copyToClipboard}>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </Button>
                    <Button variant="outline" size="sm" onClick={downloadTranscript}>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>

                {/* Transcript Content */}
                <ScrollArea className="h-96 w-full rounded-md border p-4">
                  {transcript ? (
                    <div
                      className="text-sm leading-relaxed whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: highlightSearchTerm(transcript),
                      }}
                    />
                  ) : (
                    <p className="text-muted-foreground text-center py-8">No transcript available</p>
                  )}
                </ScrollArea>

                {/* Word Count */}
                {transcript && (
                  <div className="text-xs text-muted-foreground text-right">
                    {transcript.split(/\s+/).filter((word) => word.length > 0).length} words
                  </div>
                )}
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
