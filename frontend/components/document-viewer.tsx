"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  FileText, 
  Mic, 
  ChevronDown, 
  ChevronRight, 
  Brain, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2
} from "lucide-react"
import { api, type Document, type DocumentChunksResponse, type AINote, type TranscriptResponse, APIError, apiUtils } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface DocumentViewerProps {
  document: Document
}

export function DocumentViewer({ document }: DocumentViewerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [content, setContent] = useState<string>("")
  const [aiNotes, setAiNotes] = useState<string>("")
  const [loading, setLoading] = useState(false)
  const [contentLoaded, setContentLoaded] = useState(false)
  const [notesLoaded, setNotesLoaded] = useState(false)
  const [activeTab, setActiveTab] = useState<"content" | "notes">("content")
  const { session } = useAuth()

  const isAudio = document.is_audio === "true"
  const isProcessed = isAudio 
    ? document.transcription_status === "completed"
    : document.processed === "completed"

  const getStatusInfo = () => {
    if (isAudio) {
      switch (document.transcription_status) {
        case "completed":
          return { icon: CheckCircle, text: "Transcribed", color: "text-green-400" }
        case "processing":
          return { icon: Clock, text: "Transcribing...", color: "text-yellow-400" }
        case "failed":
          return { icon: AlertCircle, text: "Failed", color: "text-red-400" }
        default:
          return { icon: Clock, text: "Pending", color: "text-gray-400" }
      }
    } else {
      switch (document.processed) {
        case "completed":
          return { icon: CheckCircle, text: "Ready", color: "text-green-400" }
        case "processing":
          return { icon: Clock, text: "Processing...", color: "text-yellow-400" }
        case "failed":
          return { icon: AlertCircle, text: "Failed", color: "text-red-400" }
        default:
          return { icon: Clock, text: "Pending", color: "text-gray-400" }
      }
    }
  }

  const loadContent = async () => {
    if (contentLoaded || !isProcessed || !session?.session_id) return
    
    setLoading(true)
    try {
      if (isAudio) {
        // Load transcript
        const transcript = await api.getTranscript(document.id, session.session_id)
        setContent(transcript.transcript)
      } else {
        // Load document chunks
        const chunks = await api.getDocumentChunks(document.id, session.session_id)
        const fullContent = chunks.chunks.map(chunk => chunk.content).join('\n\n')
        setContent(fullContent)
      }
      setContentLoaded(true)
    } catch (error) {
      console.error("Failed to load content:", error)
      setContent("Failed to load content")
    } finally {
      setLoading(false)
    }
  }

  const loadAiNotes = async () => {
    if (notesLoaded || !isProcessed || !session?.session_id) return
    
    try {
      const notes = await api.getAINote(document.id, session.session_id)
      setAiNotes(notes.notes)
      setNotesLoaded(true)
    } catch (error) {
      console.error("Failed to load AI notes:", error)
      // Try to generate notes if they don't exist
      try {
        await api.generateAINote(document.id, false, session.session_id)
        const notes = await api.getAINote(document.id, session.session_id)
        setAiNotes(notes.notes)
        setNotesLoaded(true)
      } catch (generateError) {
        console.error("Failed to generate AI notes:", generateError)
        setAiNotes("AI notes not available")
        setNotesLoaded(true)
      }
    }
  }

  const handleToggle = () => {
    const newIsOpen = !isOpen
    setIsOpen(newIsOpen)
    
    if (newIsOpen && isProcessed) {
      loadContent()
      loadAiNotes()
    }
  }

  const handleTabChange = (tab: "content" | "notes") => {
    setActiveTab(tab)
    if (tab === "content" && !contentLoaded) {
      loadContent()
    } else if (tab === "notes" && !notesLoaded) {
      loadAiNotes()
    }
  }

  const statusInfo = getStatusInfo()
  const StatusIcon = statusInfo.icon

  return (
    <Card className="bg-gray-900 border-gray-700 hover:border-gray-600 transition-colors">
      <Collapsible open={isOpen} onOpenChange={handleToggle}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-gray-800/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {isAudio ? (
                  <Mic className="h-5 w-5 text-blue-400" />
                ) : (
                  <FileText className="h-5 w-5 text-green-400" />
                )}
                <div className="flex-1">
                  <CardTitle className="text-left text-white">{document.filename}</CardTitle>
                  <CardDescription className="text-left text-gray-400">
                    {apiUtils.formatFileSize(document.file_size)} • {apiUtils.formatDate(document.upload_date)}
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="outline" className={`${statusInfo.color} border-current`}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {statusInfo.text}
                </Badge>
                {isOpen ? (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                )}
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0">
            {!isProcessed ? (
              <div className="text-center py-8 text-gray-400">
                <StatusIcon className="h-8 w-8 mx-auto mb-2" />
                <p>Document is still being processed</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Tab Navigation */}
                <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
                  <Button
                    variant={activeTab === "content" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => handleTabChange("content")}
                    className={`flex-1 ${
                      activeTab === "content" 
                        ? "bg-blue-600 hover:bg-blue-700 text-white" 
                        : "text-gray-400 hover:text-white hover:bg-gray-700"
                    }`}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    {isAudio ? "Transcript" : "Content"}
                  </Button>
                  <Button
                    variant={activeTab === "notes" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => handleTabChange("notes")}
                    className={`flex-1 ${
                      activeTab === "notes" 
                        ? "bg-blue-600 hover:bg-blue-700 text-white" 
                        : "text-gray-400 hover:text-white hover:bg-gray-700"
                    }`}
                  >
                    <Brain className="h-4 w-4 mr-2" />
                    AI Notes
                  </Button>
                </div>

                {/* Content Area */}
                <div className="min-h-[300px]">
                  {loading ? (
                    <div className="text-center py-8 text-gray-400">
                      <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
                      <p>Loading {activeTab === "content" ? "content" : "AI notes"}...</p>
                    </div>
                  ) : (
                    <ScrollArea className="h-80 w-full rounded-md border border-gray-700 bg-gray-800">
                      <div className="p-4">
                        {activeTab === "content" ? (
                          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
                            {content || "No content available"}
                          </pre>
                        ) : (
                          <div className="text-sm text-gray-300 whitespace-pre-wrap">
                            {aiNotes ? (
                              aiNotes
                            ) : (
                              <div className="text-center py-8 text-gray-400">
                                <Brain className="h-8 w-8 mx-auto mb-2" />
                                <p>No AI notes available</p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
