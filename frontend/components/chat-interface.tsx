"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Send, Bot, User, BookOpen, FileText, Mic, ExternalLink } from "lucide-react"
import { api, type Course, type QueryResponse, APIError } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface Citation {
  filename: string
  text: string
  similarity_score: number
  chunk_index: number
}

interface ChatMessage {
  id: string
  type: "user" | "assistant"
  content: string
  citations?: Citation[]
  timestamp: Date
}

export function ChatInterface() {
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourse, setSelectedCourse] = useState<string>("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchCourses()
    }
  }, [session])

  useEffect(() => {
    // Scroll to bottom when new messages are added
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const fetchCourses = async () => {
    if (!session?.session_id) return
    
    try {
      const data = await api.getCourses(session.session_id)
      setCourses(data)
      if (data.length > 0) {
        setSelectedCourse(data[0].id.toString())
      }
    } catch (error) {
      console.error("Failed to fetch courses:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    }
  }

  const sendMessage = async () => {
    if (!inputValue.trim() || !selectedCourse || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const data = await api.queryDocuments({
        question: userMessage.content,
        course_id: Number.parseInt(selectedCourse),
        max_results: 5,
      })

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.answer,
        citations: data.citations,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Failed to send message:", error)
      let errorContent = "I'm sorry, I'm having trouble connecting right now. Please try again later."
      
      if (error instanceof APIError) {
        if (error.status === 404) {
          errorContent = "I'm sorry, the selected course was not found. Please select a different course."
        } else if (error.status === 400) {
          errorContent = "I'm sorry, there was an issue with your request. Please try rephrasing your question."
        } else {
          errorContent = "I'm sorry, I encountered an error while processing your question. Please try again."
        }
      }
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: errorContent,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getFileIcon = (filename: string) => {
    const extension = filename.split(".").pop()?.toLowerCase()
    if (["mp3", "wav", "m4a", "mp4"].includes(extension || "")) {
      return <Mic className="h-3 w-3 text-secondary" />
    }
    return <FileText className="h-3 w-3 text-primary" />
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-12rem)]">
      {/* Course Selection */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Select Course
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={selectedCourse} onValueChange={setSelectedCourse}>
            <SelectTrigger>
              <SelectValue placeholder="Choose a course to chat about" />
            </SelectTrigger>
            <SelectContent>
              {courses.map((course) => (
                <SelectItem key={course.id} value={course.id.toString()}>
                  {course.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Chat Messages</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0">
          <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
            {messages.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
                <p className="text-muted-foreground mb-4">
                  Ask questions about your course materials and I'll provide answers with source citations.
                </p>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Try asking:</p>
                  <p>"What did the professor say about the French Revolution?"</p>
                  <p>"Summarize the key points from chapter 3"</p>
                  <p>"What are the main themes in the lecture?"</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex gap-3 ${message.type === "user" ? "justify-end" : ""}`}>
                    {message.type === "assistant" && (
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div className={`flex-1 max-w-[80%] ${message.type === "user" ? "order-first" : ""}`}>
                      <div
                        className={`rounded-lg p-3 ${
                          message.type === "user"
                            ? "bg-primary text-primary-foreground ml-auto"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-muted-foreground">{formatTimestamp(message.timestamp)}</span>
                      </div>
                      {/* Citations */}
                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-3 space-y-2">
                          <p className="text-xs font-medium text-muted-foreground">Sources:</p>
                          {message.citations.map((citation, index) => (
                            <Card key={index} className="p-3 bg-background/50">
                              <div className="flex items-start gap-2">
                                {getFileIcon(citation.filename)}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <p className="text-xs font-medium truncate">{citation.filename}</p>
                                    <Badge variant="outline" className="text-xs">
                                      {Math.round(citation.similarity_score * 100)}% match
                                    </Badge>
                                  </div>
                                  <p className="text-xs text-muted-foreground line-clamp-2">{citation.text}</p>
                                </div>
                                <Button variant="ghost" size="sm">
                                  <ExternalLink className="h-3 w-3" />
                                </Button>
                              </div>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>
                    {message.type === "user" && (
                      <div className="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="h-4 w-4 text-secondary" />
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                          <span className="text-sm text-muted-foreground">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedCourse
                    ? "Ask a question about your course materials..."
                    : "Select a course first to start chatting"
                }
                disabled={!selectedCourse || isLoading}
                className="flex-1"
              />
              <Button onClick={sendMessage} disabled={!inputValue.trim() || !selectedCourse || isLoading} size="icon">
                <Send className="h-4 w-4" />
              </Button>
            </div>
            {selectedCourse && (
              <p className="text-xs text-muted-foreground mt-2">
                Chatting about: {courses.find((c) => c.id.toString() === selectedCourse)?.name}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
