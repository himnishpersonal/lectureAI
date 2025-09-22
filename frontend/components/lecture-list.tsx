"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreVertical, FileText, Calendar, Plus, Trash2, Edit } from "lucide-react"
import { api, Lecture } from "@/lib/api"
import { CreateLectureDialog } from "./create-lecture-dialog"
import { UploadDocumentDialog } from "./upload-document-dialog"
import { LectureDocumentsViewer } from "./lecture-documents-viewer"
import { useAuth } from "@/components/auth/auth-provider"

interface LectureListProps {
  courseId: number
}

export function LectureList({ courseId }: LectureListProps) {
  const [lectures, setLectures] = useState<Lecture[]>([])
  const [loading, setLoading] = useState(true)
  const [viewingMaterialsFor, setViewingMaterialsFor] = useState<number | null>(null)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchLectures()
    }
  }, [courseId, session])

  const fetchLectures = async () => {
    if (!session?.session_id) return
    
    try {
      const lecturesData = await api.getCourseLectures(courseId, session.session_id)
      setLectures(lecturesData)
    } catch (error) {
      console.error("Failed to fetch lectures:", error)
      // If lectures don't exist yet, just show empty state
      setLectures([])
    } finally {
      setLoading(false)
    }
  }

  const deleteLecture = async (lectureId: number) => {
    if (!confirm("Are you sure you want to delete this lecture? This will also delete all documents in the lecture.")) {
      return
    }

    if (!session?.session_id) return

    try {
      await api.deleteLecture(lectureId, session.session_id)
      setLectures(lectures.filter(lecture => lecture.id !== lectureId))
    } catch (error) {
      console.error("Failed to delete lecture:", error)
      alert("Failed to delete lecture. Please try again.")
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse bg-gray-900 border-gray-700">
            <CardHeader>
              <div className="h-4 bg-gray-700 rounded w-3/4"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-3 bg-gray-700 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (lectures.length === 0) {
    return (
      <div className="text-center py-12">
        <Card className="bg-gray-900 border-gray-700">
          <CardContent className="pt-6">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2 text-white">No lectures yet</h3>
            <p className="text-gray-400 mb-4">
              Create your first lecture to start organizing your course materials
            </p>
            <CreateLectureDialog courseId={courseId} onLectureCreated={fetchLectures}>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Create First Lecture
              </Button>
            </CreateLectureDialog>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">Lectures</h2>
          <p className="text-gray-400">Organize your course materials by lecture</p>
        </div>
        <CreateLectureDialog courseId={courseId} onLectureCreated={fetchLectures}>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            New Lecture
          </Button>
        </CreateLectureDialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {lectures.map((lecture) => (
          <Card key={lecture.id} className="hover:shadow-lg transition-shadow bg-gray-900 border-gray-700 hover:border-gray-600">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <div className="space-y-1 flex-1">
                <CardTitle className="text-lg line-clamp-1 text-white">{lecture.title}</CardTitle>
                <CardDescription className="line-clamp-2 text-gray-400">
                  {lecture.description || "No description provided"}
                </CardDescription>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-gray-800">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-gray-800 border-gray-600 shadow-lg">
                  <DropdownMenuItem className="text-gray-300 hover:bg-gray-700 focus:bg-gray-700">
                    <Edit className="h-4 w-4 mr-2" />
                    Edit Lecture
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    className="text-red-400 hover:bg-gray-700 focus:bg-gray-700" 
                    onClick={() => deleteLecture(lecture.id)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Lecture
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 text-sm text-gray-400">
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
              </div>
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-gray-400 border-gray-600">
                  Created {new Date(lecture.created_at).toLocaleDateString()}
                </Badge>
                <div className="flex gap-2">
                  <UploadDocumentDialog lectureId={lecture.id} onDocumentUploaded={() => fetchLectures()}>
                    <Button size="sm" variant="outline" className="border-gray-600 text-gray-300 hover:bg-gray-800">
                      Upload
                    </Button>
                  </UploadDocumentDialog>
                  <Button 
                    size="sm" 
                    className="bg-blue-600 hover:bg-blue-700"
                    onClick={() => setViewingMaterialsFor(viewingMaterialsFor === lecture.id ? null : lecture.id)}
                  >
                    {viewingMaterialsFor === lecture.id ? "Hide Materials" : "View Materials"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Materials Viewer */}
      {viewingMaterialsFor && (
        <div className="mt-6">
          <LectureDocumentsViewer 
            lectureId={viewingMaterialsFor} 
            lectureTitle={lectures.find(l => l.id === viewingMaterialsFor)?.title || "Unknown Lecture"}
            courseId={courseId}
          />
        </div>
      )}
    </div>
  )
}
