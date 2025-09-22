"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BookOpen, FileText, Mic, MoreVertical, Trash2, Edit } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { api, type Course, APIError } from "@/lib/api"
import Link from "next/link"
import { useAuth } from "@/components/auth/auth-provider"

export function CourseList() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const { session } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchCourses()
    }
  }, [session])

  const fetchCourses = async () => {
    if (!session?.session_id) return
    
    try {
      const data = await api.getCourses(session.session_id)
      setCourses(data)
    } catch (error) {
      console.error("Failed to fetch courses:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const deleteCourse = async (courseId: number) => {
    if (!session?.session_id) return
    
    try {
      await api.deleteCourse(courseId, session.session_id)
      setCourses(courses.filter((course) => course.id !== courseId))
    } catch (error) {
      console.error("Failed to delete course:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
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

  if (courses.length === 0) {
    return (
      <Card className="text-center py-12 bg-gray-900 border-gray-700">
        <CardContent>
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2 text-white">No courses yet</h3>
          <p className="text-gray-400 mb-4">
            Create your first course to start organizing your study materials
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {courses.map((course) => (
        <Card key={course.id} className="hover:shadow-lg transition-shadow bg-gray-900 border-gray-700 hover:border-gray-600">
          <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
            <div className="space-y-1 flex-1">
              <CardTitle className="text-lg line-clamp-1 text-white">{course.name}</CardTitle>
              <CardDescription className="line-clamp-2 text-gray-400">
                {course.description || "No description provided"}
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
                  Edit Course
                </DropdownMenuItem>
                <DropdownMenuItem 
                  className="text-red-400 hover:bg-gray-700 focus:bg-gray-700" 
                  onClick={() => deleteCourse(course.id)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Course
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                <span>{course.lecture_count || 0} lectures</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-gray-400 border-gray-600">
                Created {new Date(course.created_at).toLocaleDateString()}
              </Badge>
              <Link href={`/courses/${course.id}`}>
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">View Course</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
