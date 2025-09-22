import { DocumentDetails } from "@/components/document-details"
import { AudioPlayer } from "@/components/audio-player"
import { config } from "@/lib/config"
import { TranscriptViewer } from "@/components/transcript-viewer"
import { AINotesViewer } from "@/components/ai-notes-viewer"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

interface DocumentPageProps {
  params: Promise<{
    documentId: string
  }>
}

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { documentId } = await params
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/courses">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Courses
          </Button>
        </Link>
      </div>

      <div className="space-y-8">
        <DocumentDetails documentId={documentId} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <AudioPlayer src={`${config.API_BASE_URL}/documents/${documentId}/audio`} title="Audio Lecture" />
            <TranscriptViewer documentId={Number.parseInt(documentId)} filename="lecture.mp3" />
          </div>

          <div>
            <AINotesViewer documentId={Number.parseInt(documentId)} />
          </div>
        </div>
      </div>
    </div>
  )
}
