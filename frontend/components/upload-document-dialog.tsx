"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, Mic, X, CheckCircle, AlertCircle, Edit3 } from "lucide-react"
import { cn } from "@/lib/utils"
import { api, APIError } from "@/lib/api"

interface UploadDocumentDialogProps {
  children: React.ReactNode
  lectureId?: number
  courseId?: string
  onDocumentUploaded?: () => void
}

interface UploadFile {
  file: File
  id: string
  customName: string
  progress: number
  status: "pending" | "uploading" | "success" | "error"
  error?: string
}

export function UploadDocumentDialog({ children, lectureId, courseId, onDocumentUploaded }: UploadDocumentDialogProps) {
  const [open, setOpen] = useState(false)
  const [files, setFiles] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)


  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      customName: file.name.replace(/\.[^/.]+$/, ""), // Remove file extension for custom name
      progress: 0,
      status: "pending" as const,
    }))
    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
      "audio/mpeg": [".mp3"],
      "audio/wav": [".wav"],
      "audio/mp4": [".m4a"],
      "video/mp4": [".mp4"],
    },
    multiple: true,
  })

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const updateCustomName = (id: string, customName: string) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, customName } : f)))
  }

  const uploadFiles = async () => {
    if (files.length === 0) return

    setUploading(true)

    for (const uploadFile of files) {
      if (uploadFile.status !== "pending") continue

      try {
        // Update status to uploading
        setFiles((prev) =>
          prev.map((f) => (f.id === uploadFile.id ? { ...f, status: "uploading" as const, progress: 0 } : f)),
        )

        try {
          let result
          if (lectureId) {
            result = await api.uploadDocumentToLecture(lectureId, uploadFile.file, uploadFile.customName)
          } else if (courseId) {
            result = await api.uploadDocument(Number.parseInt(courseId), uploadFile.file, uploadFile.customName)
          } else {
            throw new Error("Either lectureId or courseId must be provided")
          }
          
          setFiles((prev) =>
            prev.map((f) => (f.id === uploadFile.id ? { ...f, status: "success" as const, progress: 100 } : f)),
          )
        } catch (uploadError) {
          let errorMessage = "Upload failed"
          if (uploadError instanceof APIError) {
            errorMessage = `Upload failed: ${uploadError.message}`
          }
          setFiles((prev) =>
            prev.map((f) => (f.id === uploadFile.id ? { ...f, status: "error" as const, error: errorMessage } : f)),
          )
        }
      } catch (error) {
        setFiles((prev) =>
          prev.map((f) => (f.id === uploadFile.id ? { ...f, status: "error" as const, error: "Upload failed" } : f)),
        )
      }
    }

    setUploading(false)
    onDocumentUploaded?.()
  }

  const resetDialog = () => {
    setFiles([])
    setUploading(false)
  }

  const handleClose = () => {
    if (!uploading) {
      setOpen(false)
      // Reset after a delay to avoid visual glitch
      setTimeout(resetDialog, 300)
    }
  }

  const getFileIcon = (file: File) => {
    if (file.type.startsWith("audio/") || file.type === "video/mp4") {
      return <Mic className="h-5 w-5 text-secondary" />
    }
    return <FileText className="h-5 w-5 text-primary" />
  }

  const getFileTypeLabel = (file: File) => {
    if (file.type.startsWith("audio/") || file.type === "video/mp4") {
      return "Audio"
    }
    return "Document"
  }

  const allCompleted = files.length > 0 && files.every((f) => f.status === "success" || f.status === "error")
  const hasErrors = files.some((f) => f.status === "error")

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[600px] bg-gray-900 border-gray-700 text-white">
        <DialogHeader>
          <DialogTitle className="text-white">Upload Course Materials</DialogTitle>
          <DialogDescription className="text-gray-400">
            Upload documents (PDF, DOC, DOCX, TXT) and audio files (MP3, WAV, M4A, MP4) to your course
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50",
              uploading && "pointer-events-none opacity-50",
            )}
          >
            <input {...getInputProps()} />
            <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-primary font-medium">Drop the files here...</p>
            ) : (
              <div className="space-y-2">
                <p className="font-medium">Drag & drop files here, or click to select</p>
                <p className="text-sm text-muted-foreground">Supports PDF, DOC, DOCX, TXT, MP3, WAV, M4A, MP4</p>
              </div>
            )}
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-4 max-h-60 overflow-y-auto">
              {files.map((uploadFile) => (
                <div key={uploadFile.id} className="p-4 bg-gray-800 border border-gray-600 rounded-lg">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">{getFileIcon(uploadFile.file)}</div>
                    <div className="flex-1 min-w-0 space-y-3">
                      {/* File Info */}
                      <div className="flex items-center justify-between">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-300 truncate">{uploadFile.file.name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">{getFileTypeLabel(uploadFile.file)}</span>
                            <span className="text-xs text-gray-500">•</span>
                            <span className="text-xs text-gray-500">
                              {(uploadFile.file.size / 1024 / 1024).toFixed(1)} MB
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {uploadFile.status === "pending" && !uploading && (
                            <Button variant="ghost" size="sm" onClick={() => removeFile(uploadFile.id)} className="text-gray-400 hover:text-white">
                              <X className="h-3 w-3" />
                            </Button>
                          )}
                          {uploadFile.status === "success" && <CheckCircle className="h-4 w-4 text-green-500" />}
                          {uploadFile.status === "error" && <AlertCircle className="h-4 w-4 text-red-500" />}
                        </div>
                      </div>

                      {/* Custom Name Input */}
                      {uploadFile.status === "pending" && !uploading && (
                        <div className="space-y-2">
                          <Label htmlFor={`name-${uploadFile.id}`} className="text-sm text-gray-300 flex items-center gap-2">
                            <Edit3 className="h-3 w-3" />
                            Custom Name
                          </Label>
                          <Input
                            id={`name-${uploadFile.id}`}
                            value={uploadFile.customName}
                            onChange={(e) => updateCustomName(uploadFile.id, e.target.value)}
                            placeholder="Enter a custom name for this file..."
                            className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-blue-500"
                          />
                        </div>
                      )}

                      {/* Upload Progress */}
                      {uploadFile.status === "uploading" && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-300">Uploading...</span>
                            <span className="text-gray-400">{uploadFile.progress}%</span>
                          </div>
                          <Progress value={uploadFile.progress} className="h-2" />
                        </div>
                      )}

                      {/* Error Message */}
                      {uploadFile.status === "error" && uploadFile.error && (
                        <div className="text-sm text-red-400 bg-red-900/20 p-2 rounded">
                          {uploadFile.error}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={handleClose} disabled={uploading} className="border-gray-600 text-gray-300 hover:bg-gray-800">
              {allCompleted ? "Close" : "Cancel"}
            </Button>
            <div className="flex gap-2">
              {allCompleted && hasErrors && (
                <Button variant="outline" onClick={() => setFiles((prev) => prev.filter((f) => f.status !== "error"))}>
                  Remove Failed
                </Button>
              )}
              <Button onClick={uploadFiles} disabled={files.length === 0 || uploading || allCompleted} className="bg-blue-600 hover:bg-blue-700">
                {uploading ? "Uploading..." : `Upload ${files.length} File${files.length !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
