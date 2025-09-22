import { NotesOverview } from "@/components/notes-overview"
import { Brain } from "lucide-react"

export default function NotesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-balance flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            AI Study Notes
          </h1>
          <p className="text-muted-foreground text-pretty">
            View and manage all your AI-generated study notes across all courses
          </p>
        </div>
      </div>
      <NotesOverview />
    </div>
  )
}
