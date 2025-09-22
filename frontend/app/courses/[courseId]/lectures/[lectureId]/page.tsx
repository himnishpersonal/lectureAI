import { LecturePage } from "@/components/lecture-page"

interface LecturePageProps {
  params: Promise<{
    courseId: string
    lectureId: string
  }>
}

export default async function LecturePageRoute({ params }: LecturePageProps) {
  const { courseId, lectureId } = await params
  
  return (
    <LecturePage 
      courseId={Number.parseInt(courseId)}
      lectureId={Number.parseInt(lectureId)}
    />
  )
}
