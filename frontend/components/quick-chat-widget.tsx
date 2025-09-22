"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { MessageSquare, Send, Sparkles } from "lucide-react"
import Link from "next/link"

export function QuickChatWidget() {
  const [question, setQuestion] = useState("")

  const suggestedQuestions = [
    "What are the main themes in my recent lectures?",
    "Summarize the key points from chapter 3",
    "What did the professor say about the French Revolution?",
    "Help me understand the concept of machine learning",
  ]

  const handleQuestionClick = (q: string) => {
    setQuestion(q)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          Quick Chat
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your materials..."
            className="flex-1"
          />
          <Link href={`/chat${question ? `?q=${encodeURIComponent(question)}` : ""}`}>
            <Button size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            Suggested Questions
          </p>
          <div className="space-y-1">
            {suggestedQuestions.map((q, index) => (
              <button
                key={index}
                onClick={() => handleQuestionClick(q)}
                className="text-xs text-muted-foreground hover:text-foreground text-left w-full p-2 rounded hover:bg-muted/50 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        <Link href="/chat">
          <Button variant="outline" className="w-full bg-transparent">
            Open Full Chat
          </Button>
        </Link>
      </CardContent>
    </Card>
  )
}
