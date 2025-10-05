"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Brain, Download, Copy, RefreshCw, CheckCircle, AlertCircle, Sparkles, Save, FileText, FileImage } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { config } from "@/lib/config"
import { useTheme } from "@/contexts/theme-context"

interface AINote {
  id: number
  notes: string
  generated_at: string
  document_id: number
  model_used?: string
}

interface RichAINotesViewerProps {
  documentId: number
}

export function RichAINotesViewer({ documentId }: RichAINotesViewerProps) {
  const [notes, setNotes] = useState<AINote | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState("")
  const [saving, setSaving] = useState(false)
  const [viewMode, setViewMode] = useState<"formatted" | "edit">("formatted")
  const { livMode, setLivMode, primaryColor, primaryColor300, primaryColor600 } = useTheme()

  useEffect(() => {
    fetchNotes()
  }, [documentId])

  const fetchNotes = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/notes`)
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
        setEditedContent(data?.notes || "")
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

  const convertMarkdownToHtml = (markdown: string): string => {
    if (!markdown) return ""
    
    const headerColor = livMode ? "#f9a8d4" : "#60a5fa"
    const accentColor = livMode ? "#fda4af" : "#93c5fd"
    const borderColor = livMode ? "#ec4899" : "#3b82f6"
    
    let html = markdown
      // Convert headers
      .replace(/^## (.*$)/gim, `<h2 class="text-xl font-bold mt-6 mb-4 border-b border-gray-600 pb-2" style="color: ${headerColor}">$1</h2>`)
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mt-4 mb-3 text-gray-200">$1</h3>')
      
      // Convert numbered definitions
      .replace(/^(\d+)\.\s+\*\*([^*]+)\*\*:\s*(.*)$/gim, 
        `<div class="mb-4 p-3 bg-gray-800 rounded-lg border-l-4" style="border-color: ${borderColor}"><div class="font-semibold mb-1" style="color: ${accentColor}">$1. $2</div><div class="text-sm text-gray-300">$3</div></div>`)
      
      // Convert definition list items
      .replace(/^-\s+\*\*([^*]+)\*\*:\s*(.*)$/gim, 
        `<div class="mb-2 ml-4"><span class="font-semibold" style="color: ${accentColor}">$1:</span><span class="text-sm ml-2 text-gray-300">$2</span></div>`)
      
      // Convert section headers
      .replace(/^\*\*([^*]+)\*\*(\s*\([^)]+\))?:?$/gim, 
        '<h4 class="text-base font-semibold mt-4 mb-2 text-gray-200">$1$2</h4>')
      
      // Convert regular bullet points
      .replace(/^-\s+(.*)$/gim, '<li class="text-gray-300 mb-1">$1</li>')
      
      // Wrap consecutive list items in ul tags
      .replace(/(<li[^>]*>.*?<\/li>\s*)+/gs, '<ul class="list-disc list-inside mb-4 space-y-1 ml-4">$&</ul>')
      
      // Convert inline bold text
      .replace(/\*\*([^*]+)\*\*/g, `<strong class="font-semibold" style="color: ${accentColor}">$1</strong>`)
      
      // Convert line breaks
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>')

    return html
  }

  const saveNotes = async () => {
    if (!notes) return
    
    setSaving(true)
    try {
      const response = await fetch(`${config.API_BASE_URL}/documents/${documentId}/notes`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: editedContent }),
      })

      if (response.ok) {
        setNotes({ ...notes, notes: editedContent })
        setViewMode("formatted")
      } else {
        setError("Failed to save notes")
      }
    } catch (error) {
      console.error("Failed to save notes:", error)
      setError("Failed to save notes")
    } finally {
      setSaving(false)
    }
  }

  const convertHtmlToMarkdown = (html: string): string => {
    // Basic HTML to markdown conversion
    return html
      .replace(/<h2[^>]*>(.*?)<\/h2>/g, '## $1')
      .replace(/<h3[^>]*>(.*?)<\/h3>/g, '### $1')
      .replace(/<h4[^>]*>(.*?)<\/h4>/g, '**$1**')
      .replace(/<strong[^>]*>(.*?)<\/strong>/g, '**$1**')
      .replace(/<li[^>]*>(.*?)<\/li>/g, '- $1')
      .replace(/<ul[^>]*>|<\/ul>/g, '')
      .replace(/<div[^>]*>(.*?)<\/div>/g, '$1')
      .replace(/<span[^>]*>(.*?)<\/span>/g, '$1')
      .replace(/<br\s*\/?>/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  }

  const copyToClipboard = () => {
    if (editedContent) {
      // Copy as plain text
      const textContent = editedContent.replace(/<[^>]*>/g, '')
      navigator.clipboard.writeText(textContent)
    }
  }

  const exportToPdf = async () => {
    try {
      const { jsPDF } = await import('jspdf')
      const html2canvas = await import('html2canvas')
      
      // Convert markdown to formatted HTML
      const formattedHtml = convertMarkdownToHtml(editedContent)
      
      // Create a temporary div with the formatted content
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = formattedHtml
      tempDiv.style.width = '800px'
      tempDiv.style.padding = '40px'
      tempDiv.style.backgroundColor = '#ffffff'
      tempDiv.style.color = '#000000'
      tempDiv.style.fontFamily = 'Arial, sans-serif'
      tempDiv.style.lineHeight = '1.6'
      document.body.appendChild(tempDiv)

      const canvas = await html2canvas.default(tempDiv, {
        backgroundColor: '#ffffff',
        scale: 2
      })
      
      document.body.removeChild(tempDiv)

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF()
      const imgWidth = 210
      const pageHeight = 295
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      let heightLeft = imgHeight

      let position = 0

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }

      pdf.save(`ai_notes_${documentId}.pdf`)
    } catch (error) {
      console.error('Failed to export PDF:', error)
      setError('Failed to export PDF')
    }
  }

  const exportToDocx = async () => {
    try {
      const htmlDocx = await import('html-docx-js/dist/html-docx') as any
      
      // Convert markdown to formatted HTML
      const formattedHtml = convertMarkdownToHtml(editedContent)
      
      // Choose colors based on theme
      const primaryColor = livMode ? '#ec4899' : '#2563eb'
      const accentColor = livMode ? '#fda4af' : '#93c5fd'
      
      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>AI Study Notes</title>
          <style>
            body { 
              font-family: Arial, sans-serif; 
              line-height: 1.6;
              color: #1f2937;
              max-width: 800px;
              margin: 0 auto;
              padding: 40px;
            }
            h2 { 
              color: ${primaryColor}; 
              border-bottom: 2px solid #e5e7eb; 
              padding-bottom: 8px;
              margin-top: 24px;
              margin-bottom: 16px;
              font-size: 24px;
            }
            h3 { 
              color: #374151; 
              margin-top: 20px;
              margin-bottom: 12px;
              font-size: 18px;
            }
            h4 {
              color: #4b5563;
              margin-top: 16px;
              margin-bottom: 8px;
              font-size: 16px;
            }
            p {
              margin-bottom: 12px;
            }
            strong { 
              color: ${primaryColor};
              font-weight: 600;
            }
            ul {
              margin-bottom: 16px;
              padding-left: 24px;
            }
            li {
              margin-bottom: 8px;
            }
            div[style*="border-l-4"] {
              background: #f9fafb;
              padding: 12px;
              margin: 16px 0;
              border-left: 4px solid ${primaryColor};
              border-radius: 4px;
            }
          </style>
        </head>
        <body>
          ${formattedHtml}
        </body>
        </html>
      `
      
      const docxBlob = htmlDocx.asBlob(htmlContent)
      const url = URL.createObjectURL(docxBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai_notes_${documentId}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export DOCX:', error)
      setError('Failed to export DOCX')
    }
  }


  const cancelEditing = () => {
    setViewMode("formatted")
    if (notes) {
      setEditedContent(notes.notes)
    }
  }

  const formatMarkdownForDisplay = (markdown: string) => {
    const htmlContent = convertMarkdownToHtml(markdown)
    return htmlContent
  }

  return (
    <Card className="h-full bg-gray-900 border-gray-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2 text-white">
              <Brain className={`h-5 w-5 ${livMode ? "text-pink-400" : "text-blue-400"}`} />
              AI Study Notes
            </CardTitle>
            <CardDescription className="text-gray-400">
              AI-generated comprehensive study notes with rich text editing
            </CardDescription>
          </div>
          {notes && (
            <Badge variant="outline" className="text-green-400 border-green-600">
              <CheckCircle className="h-3 w-3 mr-1" />
              Generated {formatDistanceToNow(new Date(notes.generated_at), { addSuffix: true })}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading AI notes...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2 text-white">Error Loading Notes</h3>
            <p className="text-gray-400 mb-4">{error}</p>
            <Button onClick={() => fetchNotes()} variant="outline" className="border-gray-600 text-gray-300">
              Try Again
            </Button>
          </div>
        ) : !notes ? (
          <div className="text-center py-8">
            <Sparkles className="h-12 w-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2 text-white">No AI Notes Yet</h3>
            <p className="text-gray-400 mb-4">
              Generate comprehensive study notes from your document or audio content using AI.
            </p>
            <Button onClick={() => generateNotes(false)} disabled={generating} size="lg" className={livMode ? "bg-pink-600 hover:bg-pink-700" : "bg-blue-600 hover:bg-blue-700"}>
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
            <div className="flex flex-wrap gap-2 items-center">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Liv Mode:</span>
                <button
                  onClick={() => setLivMode(!livMode)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${livMode ? "bg-pink-600" : "bg-blue-600"}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      livMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              <Button variant="outline" size="sm" onClick={copyToClipboard} className="border-gray-600 text-gray-300">
                <Copy className="h-4 w-4 mr-2" />
                Copy Notes
              </Button>
              <Button variant="outline" size="sm" onClick={exportToPdf} className="border-gray-600 text-gray-300">
                <FileImage className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
              <Button variant="outline" size="sm" onClick={exportToDocx} className="border-gray-600 text-gray-300">
                <FileText className="h-4 w-4 mr-2" />
                Export DOCX
              </Button>
              <Button variant="outline" size="sm" onClick={() => generateNotes(true)} disabled={generating} className="border-gray-600 text-gray-300">
                {generating ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Regenerate
              </Button>
            </div>

            <Separator className="bg-gray-700" />

            {/* Notes Display/Editor */}
            <div className="min-h-[500px]">
              <div className="flex gap-2 mb-4">
                <Button 
                  variant={viewMode === "formatted" ? "default" : "outline"} 
                  size="sm" 
                  onClick={() => setViewMode("formatted")}
                  className={livMode ? "bg-pink-600 hover:bg-pink-700" : "bg-blue-600 hover:bg-blue-700"}
                >
                  📖 Formatted View
                </Button>
                <Button 
                  variant={viewMode === "edit" ? "default" : "outline"} 
                  size="sm" 
                  onClick={() => setViewMode("edit")}
                  className={livMode ? "bg-pink-600 hover:bg-pink-700" : "bg-blue-600 hover:bg-blue-700"}
                >
                  ✏️ Edit Mode
                </Button>
              </div>

              {viewMode === "edit" ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Edit Notes (Markdown)</h3>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={saveNotes} disabled={saving} className={`bg-${primaryColor600} hover:bg-${primaryColor600}/80`}>
                        <Save className="h-4 w-4 mr-2" />
                        {saving ? "Saving..." : "Save"}
                      </Button>
                      <Button size="sm" onClick={cancelEditing} variant="outline" className="border-gray-600 text-gray-300">
                        Cancel
                      </Button>
                    </div>
                  </div>
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="w-full h-[400px] p-4 bg-gray-800 border border-gray-600 rounded-lg text-gray-300 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Edit your AI notes here using Markdown formatting..."
                  />
                  <div className="text-xs text-gray-500">
                    {editedContent.split(/\s+/).filter((word) => word.length > 0).length} words • Markdown formatting supported
                  </div>
                </div>
              ) : (
                <ScrollArea className="h-[500px] w-full rounded-md border border-gray-700 p-6 bg-gray-800">
                  <div 
                    className="prose prose-sm max-w-none text-gray-300"
                    dangerouslySetInnerHTML={{ __html: formatMarkdownForDisplay(editedContent) }}
                  />
                </ScrollArea>
              )}
            </div>

            {/* Word Count */}
            <div className="text-xs text-gray-500 text-right">
              {notes.notes.split(/\s+/).filter((word) => word.length > 0).length} words
            </div>
          </>
        )}

        {generating && (
          <div className="bg-gray-800 rounded-lg p-4 text-center border border-gray-700">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
              <span className="text-sm font-medium text-white">Generating AI Notes</span>
            </div>
            <p className="text-xs text-gray-400">
              This may take a few moments while our AI analyzes your content and creates comprehensive study notes.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
