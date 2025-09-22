"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { api } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface CreateLectureDialogProps {
  children: React.ReactNode
  courseId: number
  onLectureCreated?: () => void
}

export function CreateLectureDialog({ children, courseId, onLectureCreated }: CreateLectureDialogProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    lecture_date: ""
  })
  const { session } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) return
    if (!session?.session_id) {
      console.error("No session available")
      return
    }

    setLoading(true)
    try {
      const lectureData = {
        title: formData.title,
        description: formData.description || undefined,
        lecture_date: formData.lecture_date || undefined
      }
      
      await api.createLecture(courseId, lectureData, session.session_id)
      setOpen(false)
      setFormData({ title: "", description: "", lecture_date: "" })
      onLectureCreated?.()
    } catch (error) {
      console.error("Failed to create lecture:", error)
      alert("Failed to create lecture. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setOpen(false)
    setFormData({ title: "", description: "", lecture_date: "" })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] bg-gray-900 border-gray-700 text-white">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="text-white">Create New Lecture</DialogTitle>
            <DialogDescription className="text-gray-400">Add a new lecture to organize your course materials.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title" className="text-white">Lecture Title</Label>
              <Input
                id="title"
                placeholder="e.g., Introduction to Machine Learning"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                className="bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description" className="text-white">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="Brief description of the lecture content..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="lecture_date" className="text-white">Lecture Date (Optional)</Label>
              <Input
                id="lecture_date"
                type="date"
                value={formData.lecture_date}
                onChange={(e) => setFormData({ ...formData, lecture_date: e.target.value })}
                className="bg-gray-800 border-gray-600 text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} className="border-gray-600 text-gray-300 hover:bg-gray-800">
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !formData.title.trim()} className="bg-blue-600 hover:bg-blue-700">
              {loading ? "Creating..." : "Create Lecture"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
