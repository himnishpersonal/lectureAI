import { DocumentViewerPage } from "@/components/document-viewer-page"

interface DocumentPageProps {
  params: Promise<{
    courseId: string
    lectureId: string
    documentId: string
  }>
}

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { courseId, lectureId, documentId } = await params
  
  return (
    <DocumentViewerPage 
      courseId={Number.parseInt(courseId)}
      lectureId={Number.parseInt(lectureId)}
      documentId={Number.parseInt(documentId)}
    />
  )
}
