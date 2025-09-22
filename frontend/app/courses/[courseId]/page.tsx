import { CourseDetails } from "@/components/course-details"
import { LectureList } from "@/components/lecture-list"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

interface CoursePageProps {
  params: Promise<{
    courseId: string
  }>
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { courseId } = await params
  
  return (
    <div className="container mx-auto px-4 py-8 bg-black min-h-screen">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/courses">
          <Button variant="ghost" size="sm" className="text-white hover:bg-gray-800">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Courses
          </Button>
        </Link>
      </div>

      <div className="space-y-8">
        <CourseDetails courseId={courseId} />
        <LectureList courseId={Number.parseInt(courseId)} />
      </div>
    </div>
  )
}
