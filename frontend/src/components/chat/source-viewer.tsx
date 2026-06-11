"use client"

import * as React from "react"
import { Citation } from "@/types/chat"
import { useSourcePreview } from "@/hooks/use-source-preview"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Loader2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

interface SourceViewerProps {
  citation: Citation | null
  isOpen: boolean
  onClose: () => void
}

export function SourceViewer({ citation, isOpen, onClose }: SourceViewerProps) {
  const { data, loading, error, fetchPreview } = useSourcePreview()

  React.useEffect(() => {
    if (isOpen && citation?.chunk_id) {
      fetchPreview(citation.chunk_id)
    }
  }, [isOpen, citation, fetchPreview])

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-600" />
            <DialogTitle className="text-lg truncate">
              {citation?.source || "Source Preview"}
            </DialogTitle>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4">
              <AlertCircle className="h-12 w-12 text-destructive/50" />
              <div className="space-y-2">
                <p className="font-semibold text-zinc-900 dark:text-zinc-100">Failed to load source</p>
                <p className="text-sm text-zinc-500 max-w-xs">{error}</p>
              </div>
            </div>
          ) : data ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              <ScrollArea className="flex-1 p-6">
                <div className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider">Document Context</h3>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {data.context.map((c) => (
                        <div
                          key={c.id}
                          className={cn(
                            "p-4 rounded-lg mb-4 leading-relaxed transition-colors",
                            c.is_target
                              ? "bg-blue-50 border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800"
                              : "bg-zinc-50 border border-zinc-100 dark:bg-zinc-900/40 dark:border-zinc-800"
                          )}
                        >
                          {c.is_target && (
                            <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:bg-blue-900 dark:text-blue-300 mb-2">
                              CITED SECTION
                            </span>
                          )}
                          <p className={cn(
                            "text-zinc-800 dark:text-zinc-200",
                            c.is_target ? "font-medium" : "opacity-70"
                          )}>
                            {c.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-6 border-t space-y-4">
                    <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider">Metadata</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {Object.entries(data.metadata || {}).map(([key, value]) => (
                        <div key={key} className="space-y-1">
                          <p className="font-medium text-zinc-500 capitalize">{key.replace(/_/g, ' ')}</p>
                          <p className="text-zinc-900 dark:text-zinc-100 truncate">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </ScrollArea>
              {data.presigned_url && (
                <div className="h-64 border-t border-zinc-200 dark:border-zinc-800">
                  <iframe
                    src={data.presigned_url}
                    className="w-full h-full"
                    title="PDF Preview"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-zinc-400">
              No data available
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
