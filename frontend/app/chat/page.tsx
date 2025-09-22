import { ChatInterface } from "@/components/chat-interface"
import { MessageSquare } from "lucide-react"

export default function ChatPage() {
  return (
    <div className="container mx-auto px-4 py-8 h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-balance flex items-center gap-2">
            <MessageSquare className="h-8 w-8 text-primary" />
            AI Chat
          </h1>
          <p className="text-muted-foreground text-pretty">
            Ask questions about your course materials and get intelligent answers with source citations
          </p>
        </div>
      </div>
      <ChatInterface />
    </div>
  )
}
