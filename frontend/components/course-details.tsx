"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BookOpen, FileText, Mic, Calendar } from "lucide-react"
import { api, type Course, type Lecture, APIError } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface CourseDetailsProps {
  courseId: string
}

export function CourseDetails({ courseId }: CourseDetailsProps) {
  const [course, setCourse] = useState<Course | null>(null)
  const [lectureCount, setLectureCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchCourseDetails()
    }
  }, [courseId, session])

  const fetchCourseDetails = async () => {
    if (!session?.session_id) return
    
    try {
      const courseData = await api.getCourse(Number.parseInt(courseId), session.session_id)
      setCourse(courseData)
      
      // Use the lecture_count from the course data instead of fetching lectures
      setLectureCount(courseData.lecture_count)
    } catch (error) {
      console.error("Failed to fetch course details:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardHeader className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
        </CardHeader>
        <CardContent className="animate-pulse">
          <div className="flex gap-4">
            <div className="h-4 bg-gray-700 rounded w-20"></div>
            <div className="h-4 bg-gray-700 rounded w-20"></div>
            <div className="h-4 bg-gray-700 rounded w-24"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!course) {
    return (
      <Card className="bg-gray-900 border-gray-700">
        <CardContent className="text-center py-8">
          <p className="text-gray-400">Course not found</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-gray-900 border-gray-700">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <CardTitle className="text-2xl flex items-center gap-2 text-white">
              <BookOpen className="h-6 w-6 text-blue-400" />
              {course.name}
            </CardTitle>
            <CardDescription className="text-base text-gray-400">{course.description || "No description provided"}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-4">
          <Badge variant="outline" className="flex items-center gap-1 text-blue-400 border-blue-400">
            <BookOpen className="h-3 w-3" />
            {lectureCount} Lectures
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1 text-gray-400 border-gray-400">
            <Calendar className="h-3 w-3" />
            Created {new Date(course.created_at).toLocaleDateString()}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
