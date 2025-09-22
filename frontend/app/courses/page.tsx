import { CourseList } from "@/components/course-list"
import { CreateCourseDialog } from "@/components/create-course-dialog"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { AuthGuard } from "@/components/auth/auth-guard"

export default function CoursesPage() {
  return (
    <AuthGuard>
      <div className="container mx-auto px-4 py-8 bg-black min-h-screen">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-balance text-white">My Courses</h1>
            <p className="text-gray-400 text-pretty">Manage your courses and organize your study materials</p>
          </div>
          <CreateCourseDialog>
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 mr-2" />
              New Course
            </Button>
          </CreateCourseDialog>
        </div>
        <CourseList />
      </div>
    </AuthGuard>
  )
}
