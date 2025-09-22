"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CreateCourseDialog } from "@/components/create-course-dialog"
import { api, type Course, APIError } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"
import Link from "next/link"
import {
  BookOpen,
  Plus,
  Loader2,
  MessageSquare,
} from "lucide-react"

export function Dashboard() {
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  const { session, user, usageStats } = useAuth()

  useEffect(() => {
    if (session?.session_id) {
      fetchDashboardData()
    }
  }, [session])

  const fetchDashboardData = async () => {
    if (!session?.session_id) return
    
    try {
      const coursesData = await api.getCourses(session.session_id)
      setCourses(coursesData.slice(0, 3)) // Show only first 3 courses
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-balance text-white">Welcome to LectureAI</h1>
        <p className="text-xl text-gray-400 text-pretty max-w-2xl mx-auto">
          Your intelligent study companion for processing course materials, generating AI notes, and contextual learning
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        <Card className="hover:shadow-lg transition-shadow bg-gray-900 border-gray-700">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4">
              <Plus className="h-6 w-6 text-blue-400" />
            </div>
            <CardTitle className="text-white">Create Course</CardTitle>
            <CardDescription className="text-gray-400">Start a new course to organize your study materials</CardDescription>
          </CardHeader>
          <CardContent>
            <CreateCourseDialog>
              <Button className="w-full bg-blue-600 hover:bg-blue-700" size="lg">
                <BookOpen className="h-4 w-4 mr-2" />
                New Course
              </Button>
            </CreateCourseDialog>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow bg-gray-900 border-gray-700">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4">
              <MessageSquare className="h-6 w-6 text-blue-400" />
            </div>
            <CardTitle className="text-white">AI Chat</CardTitle>
            <CardDescription className="text-gray-400">Ask questions about your course materials with intelligent search</CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/chat">
              <Button className="w-full bg-blue-600 hover:bg-blue-700" size="lg">
                <MessageSquare className="h-4 w-4 mr-2" />
                Start Chat
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="space-y-8">
          {/* Recent Courses */}
          <Card className="bg-gray-900 border-gray-700">
            <CardHeader>
              <CardTitle className="flex items-center text-white">
                <BookOpen className="h-5 w-5 mr-2 text-blue-400" />
                Recent Courses
              </CardTitle>
              <CardDescription className="text-gray-400">Your latest course activities</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : courses.length === 0 ? (
                <div className="text-center py-8">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-400">No courses yet. Create your first course to get started!</p>
                </div>
              ) : (
                <>
                  {courses.map((course, index) => (
                    <div key={course.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 ${index === 0 ? 'bg-blue-600/20' : index === 1 ? 'bg-green-600/20' : 'bg-purple-600/20'} rounded-lg flex items-center justify-center`}>
                          <BookOpen className={`h-5 w-5 ${index === 0 ? 'text-blue-400' : index === 1 ? 'text-green-400' : 'text-purple-400'}`} />
                        </div>
                        <div>
                          <p className="font-medium text-white">{course.name}</p>
                          <p className="text-sm text-gray-400">
                            {course.lecture_count} lecture{course.lecture_count !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline" className={index === 0 ? "text-blue-400 border-blue-400" : "text-gray-400 border-gray-400"}>
                        {index === 0 ? "Active" : "Ready"}
                      </Badge>
                    </div>
                  ))}
                  <Button variant="ghost" className="w-full text-gray-400 hover:text-white hover:bg-gray-800" onClick={() => window.location.href = '/courses'}>
                    View All Courses
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

        </div>
    </div>
  )
}
