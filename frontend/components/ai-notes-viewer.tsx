"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Brain, Download, Copy, RefreshCw, CheckCircle, AlertCircle, Sparkles } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { config } from "@/lib/config"

interface AINote {
  id: number
  content: string
  generated_at: string
  document_id: number
}

interface AINotesViewerProps {
  documentId: number
}

export function AINotesViewer({ documentId }: AINotesViewerProps) {
  const [notes, setNotes] = useState<AINote | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchNotes()
  }, [documentId])

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/notes`)
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
        setError(null)
      } else if (response.status === 404) {
        setNotes(null)
        setError(null)
      } else {
        setError("Failed to load AI notes")
      }
    } catch (error) {
      console.error("Failed to fetch AI notes:", error)
      setError("Failed to load AI notes")
    } finally {
      setLoading(false)
    }
  }

  const generateNotes = async (regenerate = false) => {
    setGenerating(true)
    setError(null)

    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/generate-notes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ regenerate }),
      })

      if (response.ok) {
        // Wait a moment then fetch the new notes
        setTimeout(() => {
          fetchNotes()
        }, 1000)
      } else {
        setError("Failed to generate AI notes")
      }
    } catch (error) {
      console.error("Failed to generate AI notes:", error)
      setError("Failed to generate AI notes")
    } finally {
      setGenerating(false)
    }
  }

  const copyToClipboard = () => {
    if (notes?.content) {
      navigator.clipboard.writeText(notes.content)
    }
  }

  const downloadNotes = () => {
    if (!notes?.content) return

    const blob = new Blob([notes.content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `ai_notes_${documentId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatNotesContent = (content: string) => {
    // Simple formatting for better readability
    return content.split("\n").map((line, index) => {
      // Headers (lines starting with #)
      if (line.startsWith("# ")) {
        return (
          <h3 key={index} className="text-lg font-semibold mt-6 mb-3 text-foreground">
            {line.substring(2)}
          </h3>
        )
      }
      // Subheaders (lines starting with ##)
      if (line.startsWith("## ")) {
        return (
          <h4 key={index} className="text-base font-medium mt-4 mb-2 text-foreground">
            {line.substring(3)}
          </h4>
        )
      }
      // Bullet points (lines starting with -)
      if (line.startsWith("- ")) {
        return (
          <li key={index} className="ml-4 mb-1 text-sm">
            {line.substring(2)}
          </li>
        )
      }
      // Empty lines
      if (line.trim() === "") {
        return <br key={index} />
      }
      // Regular paragraphs
      return (
        <p key={index} className="mb-2 text-sm leading-relaxed">
          {line}
        </p>
      )
    })
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              AI Study Notes
            </CardTitle>
            <CardDescription>AI-generated comprehensive study notes from your content</CardDescription>
          </div>
          {notes && (
            <Badge variant="outline" className="text-green-600 border-green-200">
              <CheckCircle className="h-3 w-3 mr-1" />
              Generated {formatDistanceToNow(new Date(notes.generated_at), { addSuffix: true })}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading AI notes...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Notes</h3>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => fetchNotes()} variant="outline">
              Try Again
            </Button>
          </div>
        ) : !notes ? (
          <div className="text-center py-8">
            <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No AI Notes Yet</h3>
            <p className="text-muted-foreground mb-4">
              Generate comprehensive study notes from your document or audio content using AI.
            </p>
            <Button onClick={() => generateNotes(false)} disabled={generating} size="lg">
              {generating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  Generating Notes...
                </>
              ) : (
                <>
                  <Brain className="h-4 w-4 mr-2" />
                  Generate AI Notes
                </>
              )}
            </Button>
          </div>
        ) : (
          <>
            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={copyToClipboard}>
                <Copy className="h-4 w-4 mr-2" />
                Copy Notes
              </Button>
              <Button variant="outline" size="sm" onClick={downloadNotes}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={() => generateNotes(true)} disabled={generating}>
                {generating ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Regenerate
              </Button>
            </div>

            <Separator />

            {/* Notes Content */}
            <ScrollArea className="h-96 w-full rounded-md border p-4">
              <div className="prose prose-sm max-w-none">{formatNotesContent(notes.content)}</div>
            </ScrollArea>

            {/* Word Count */}
            <div className="text-xs text-muted-foreground text-right">
              {notes.content.split(/\s+/).filter((word) => word.length > 0).length} words
            </div>
          </>
        )}

        {generating && (
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span className="text-sm font-medium">Generating AI Notes</span>
            </div>
            <p className="text-xs text-muted-foreground">
              This may take a few moments while our AI analyzes your content and creates comprehensive study notes.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
