"use client"

import * as React from "react"
import { Progress } from "@/components/ui/progress"
import { FileText, X, CheckCircle2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface UploadFileStatus {
  id: string
  file: File
  progress: number
  status: "uploading" | "completed" | "error"
  error?: string
}

interface UploadProgressProps {
  files: UploadFileStatus[]
  onRemove: (id: string) => void
  onCancel: (id: string) => void
}

export function UploadProgress({ files, onRemove, onCancel }: UploadProgressProps) {
  if (files.length === 0) return null

  return (
    <div className="mt-6 space-y-3">
      <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Uploads</h3>
      <div className="space-y-2">
        {files.map((fileStatus) => (
          <div
            key={fileStatus.id}
            className="flex items-center gap-3 p-3 rounded-lg border bg-white dark:bg-zinc-900 dark:border-zinc-800"
          >
            <div className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
              fileStatus.status === "completed" ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400" :
              fileStatus.status === "error" ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" :
              "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
            )}>
              <FileText className="h-5 w-5" />
            </div>

            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium truncate">{fileStatus.file.name}</p>
                <div className="flex items-center gap-2">
                  {fileStatus.status === "uploading" && (
                    <span className="text-xs text-zinc-500">{fileStatus.progress}%</span>
                  )}
                  {fileStatus.status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                  {fileStatus.status === "error" && <AlertCircle className="h-4 w-4 text-red-500" />}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                    onClick={() => fileStatus.status === "uploading" ? onCancel(fileStatus.id) : onRemove(fileStatus.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {fileStatus.status === "uploading" && (
                <Progress value={fileStatus.progress} className="h-1.5" />
              )}

              {fileStatus.status === "error" && (
                <p className="text-xs text-red-500 truncate">{fileStatus.error || "Upload failed"}</p>
              )}

              {fileStatus.status === "completed" && (
                <p className="text-xs text-green-600">Successfully uploaded and processing...</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
