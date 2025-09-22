"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  ArrowLeft, 
  FileText, 
  Calendar, 
  Plus,
  Loader2
} from "lucide-react"
import { api, type Lecture, type Course, APIError } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"
import { LectureDocumentsViewer } from "@/components/lecture-documents-viewer"
import { UploadDocumentDialog } from "@/components/upload-document-dialog"

interface LecturePageProps {
  courseId: number
  lectureId: number
}

export function LecturePage({ courseId, lectureId }: LecturePageProps) {
  const router = useRouter()
  const [lecture, setLecture] = useState<Lecture | null>(null)
  const [course, setCourse] = useState<Course | null>(null)
  const [loading, setLoading] = useState(true)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchLectureData()
    }
  }, [courseId, lectureId, session])

  const fetchLectureData = async () => {
    if (!session?.session_id) return
    
    try {
      const [lectureData, courseData] = await Promise.all([
        api.getLecture(lectureId, session.session_id),
        api.getCourse(courseId, session.session_id)
      ])

      setLecture(lectureData)
      setCourse(courseData)
    } catch (error) {
      console.error("Failed to fetch lecture data:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBackToCourse = () => {
    router.push(`/courses/${courseId}`)
  }

  const handleDocumentUploaded = () => {
    // Refresh the page to show new documents
    fetchLectureData()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-6">
            <Button variant="ghost" size="sm" onClick={handleBackToCourse}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Course
            </Button>
          </div>
          
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <CardTitle className="text-white">Loading Lecture...</CardTitle>
              </div>
            </CardHeader>
          </Card>
        </div>
      </div>
    )
  }

  if (!lecture || !course) {
    return (
      <div className="min-h-screen bg-black text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center gap-4 mb-6">
            <Button variant="ghost" size="sm" onClick={handleBackToCourse}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Course
            </Button>
          </div>
          
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Lecture Not Found</CardTitle>
              <CardDescription className="text-gray-400">
                The requested lecture could not be found.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={handleBackToCourse}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Course
          </Button>
        </div>

        {/* Lecture Info */}
        <Card className="bg-gray-900 border-gray-700 mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-white text-2xl">{lecture.title}</CardTitle>
                <CardDescription className="text-gray-400 mt-2">
                  {course.name}
                </CardDescription>
                {lecture.description && (
                  <p className="text-gray-300 mt-3">{lecture.description}</p>
                )}
                <div className="flex items-center gap-4 text-sm text-gray-400 mt-4">
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    <span>{lecture.document_count} materials</span>
                  </div>
                  {lecture.lecture_date && (
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      <span>{new Date(lecture.lecture_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>Created {new Date(lecture.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                <UploadDocumentDialog 
                  lectureId={lectureId} 
                  onDocumentUploaded={handleDocumentUploaded}
                >
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="h-4 w-4 mr-2" />
                    Upload Material
                  </Button>
                </UploadDocumentDialog>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Documents */}
        <LectureDocumentsViewer 
          lectureId={lectureId}
          lectureTitle={lecture.title}
          courseId={courseId}
        />
      </div>
    </div>
  )
}
