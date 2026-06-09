"use client"

import * as React from "react"
import { useDropzone } from "react-dropzone"
import { Upload } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { UploadProgress, UploadFileStatus } from "./upload-progress"
import apiClient from "@/lib/api-client"
import { toast } from "sonner"
import axios from "axios"

interface UploadZoneProps {
  onUploadComplete?: () => void
}

export function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const [uploads, setUploads] = React.useState<UploadFileStatus[]>([])
  const abortControllers = React.useRef<Record<string, AbortController>>({})

  const uploadFile = React.useCallback(async (upload: UploadFileStatus) => {
    const formData = new FormData()
    formData.append("file", upload.file)

    const controller = new AbortController()
    abortControllers.current[upload.id] = controller

    try {
      await apiClient.post("/documents", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        signal: controller.signal,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || upload.file.size)
          )
          setUploads((prev) =>
            prev.map((u) => (u.id === upload.id ? { ...u, progress } : u))
          )
        },
      })

      setUploads((prev) =>
        prev.map((u) => (u.id === upload.id ? { ...u, status: "completed", progress: 100 } : u))
      )

      toast.success(`${upload.file.name} uploaded successfully`)
      onUploadComplete?.()
    } catch (error: unknown) {
      if (axios.isCancel(error)) return

      let errorMessage = "Upload failed"
      if (axios.isAxiosError(error)) {
        errorMessage = error.response?.data?.detail || error.message
      } else if (error instanceof Error) {
        errorMessage = error.message
      }

      setUploads((prev) =>
        prev.map((u) => (u.id === upload.id ? { ...u, status: "error", error: errorMessage } : u))
      )
    } finally {
      delete abortControllers.current[upload.id]
    }
  }, [onUploadComplete])

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    const newUploads = acceptedFiles.map((file) => ({
      id: crypto.randomUUID(),
      file,
      progress: 0,
      status: "uploading" as const,
    }))

    setUploads((prev) => [...newUploads, ...prev])

    newUploads.forEach((upload) => {
      uploadFile(upload)
    })
  }, [uploadFile])

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    noClick: true,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    onDropRejected: (fileRejections) => {
      fileRejections.forEach((rejection) => {
        const error = rejection.errors[0]
        const message = error.code === "file-too-large"
          ? "File is too large (max 50MB)"
          : error.code === "file-invalid-type"
          ? "Invalid file type. Only PDF, DOCX, and TXT are supported."
          : error.message

        toast.error(`Could not upload ${rejection.file.name}`, {
          description: message,
        })
      })
    },
  })

  const removeUpload = (id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id))
  }

  const cancelUpload = (id: string) => {
    abortControllers.current[id]?.abort()
    removeUpload(id)
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={cn(
          "relative group cursor-pointer rounded-2xl border-2 border-dashed p-12 transition-all duration-200 ease-in-out",
          isDragActive
            ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/10"
            : "border-zinc-200 hover:border-zinc-300 dark:border-zinc-800 dark:hover:border-zinc-700"
        )}
        onClick={open}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center text-center space-y-4">
          <div className={cn(
            "flex h-16 w-16 items-center justify-center rounded-full bg-zinc-100 transition-colors group-hover:bg-blue-100 dark:bg-zinc-900 dark:group-hover:bg-blue-900/30",
            isDragActive && "bg-blue-100 dark:bg-blue-900/30"
          )}>
            <Upload className={cn(
              "h-8 w-8 text-zinc-500 transition-colors group-hover:text-blue-600 dark:group-hover:text-blue-400",
              isDragActive && "text-blue-600 dark:text-blue-400"
            )} />
          </div>
          <div className="space-y-1">
            <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              {isDragActive ? "Drop your files here" : "Click or drag files to upload"}
            </p>
            <p className="text-sm text-zinc-500">
              Support PDF, DOCX, and TXT (max. 50MB)
            </p>
          </div>
          <Button variant="outline" className="mt-2" onClick={(e) => { e.stopPropagation(); open(); }}>
            Select Files
          </Button>
        </div>
      </div>

      <UploadProgress
        files={uploads}
        onRemove={removeUpload}
        onCancel={cancelUpload}
      />
    </div>
  )
}
