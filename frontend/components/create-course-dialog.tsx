"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useRouter } from "next/navigation"
import { api, APIError } from "@/lib/api"
import { useAuth } from "@/components/auth/auth-provider"

interface CreateCourseDialogProps {
  children: React.ReactNode
}

export function CreateCourseDialog({ children }: CreateCourseDialogProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    description: "",
  })
  const router = useRouter()
  const { session } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!session?.session_id) {
      console.error("No session available")
      return
    }
    
    setLoading(true)

    try {
      const course = await api.createCourse(formData, session.session_id)
      setOpen(false)
      setFormData({ name: "", description: "" })
      router.push(`/courses/${course.id}`)
      router.refresh()
    } catch (error) {
      console.error("Failed to create course:", error)
      if (error instanceof APIError) {
        console.error(`API Error ${error.status}: ${error.message}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] bg-gray-900 border-gray-700 text-white">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="text-white">Create New Course</DialogTitle>
            <DialogDescription className="text-gray-400">Add a new course to organize your study materials and documents.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name" className="text-white">Course Name</Label>
              <Input
                id="name"
                placeholder="e.g., World War II History"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description" className="text-white">Description (Optional)</Label>
              <Textarea
                id="description"
                placeholder="Brief description of the course content..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="bg-gray-800 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)} className="border-gray-600 text-gray-300 hover:bg-gray-800">
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !formData.name.trim()} className="bg-blue-600 hover:bg-blue-700">
              {loading ? "Creating..." : "Create Course"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
