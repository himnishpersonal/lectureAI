"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Brain, Eye, Download, CheckCircle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { config } from "@/lib/config"
import Link from "next/link"

interface AINote {
  id: number
  content: string
  generated_at: string
  document_id: number
}

interface NotesSummaryCardProps {
  documentId: number
  filename: string
}

export function NotesSummaryCard({ documentId, filename }: NotesSummaryCardProps) {
  const [notes, setNotes] = useState<AINote | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNotes()
  }, [documentId])

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/notes`)
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
      }
    } catch (error) {
      console.error("Failed to fetch AI notes:", error)
    } finally {
      setLoading(false)
    }
  }

  const getPreview = (content: string) => {
    // Get first 150 characters and add ellipsis
    return content.length > 150 ? content.substring(0, 150) + "..." : content
  }

  const downloadNotes = () => {
    if (!notes?.content) return

    const blob = new Blob([notes.content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `ai_notes_${filename.replace(/\.[^/.]+$/, "")}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-4 bg-muted rounded w-3/4"></div>
          <div className="h-3 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="h-3 bg-muted rounded w-full mb-2"></div>
          <div className="h-3 bg-muted rounded w-2/3"></div>
        </CardContent>
      </Card>
    )
  }

  if (!notes) {
    return null
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="h-4 w-4 text-primary" />
              AI Study Notes
            </CardTitle>
            <CardDescription className="text-xs">{filename}</CardDescription>
          </div>
          <Badge variant="outline" className="text-green-600 border-green-200 text-xs">
            <CheckCircle className="h-3 w-3 mr-1" />
            Ready
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground line-clamp-3">{getPreview(notes.content)}</p>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Generated {formatDistanceToNow(new Date(notes.generated_at), { addSuffix: true })}</span>
          <span>{notes.content.split(/\s+/).filter((word) => word.length > 0).length} words</span>
        </div>

        <div className="flex gap-2">
          <Link href={`/documents/${documentId}`} className="flex-1">
            <Button size="sm" variant="outline" className="w-full bg-transparent">
              <Eye className="h-3 w-3 mr-1" />
              View
            </Button>
          </Link>
          <Button size="sm" variant="outline" onClick={downloadNotes}>
            <Download className="h-3 w-3 mr-1" />
            Download
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
