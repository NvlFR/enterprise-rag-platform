"use client"

import * as React from "react"
import { Citation } from "@/types/chat"
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover"
import { FileText, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSourceViewer } from "@/context/source-viewer-context"

interface SourcePopoverProps {
  citation: Citation
  children: React.ReactNode
}

export function SourcePopover({ citation, children }: SourcePopoverProps) {
  const { openViewer } = useSourceViewer()

  return (
    <Popover>
      <PopoverTrigger render={children} />
      <PopoverContent align="start" className="w-80">
        <PopoverHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
              <FileText className="h-4 w-4" />
            </div>
            <PopoverTitle className="truncate">{citation.source}</PopoverTitle>
          </div>
          {citation.page && (
            <PopoverDescription>Page {citation.page}</PopoverDescription>
          )}
        </PopoverHeader>
        <div className="mt-2 text-xs text-zinc-600 dark:text-zinc-400 line-clamp-4 leading-relaxed italic border-l-2 border-zinc-200 dark:border-zinc-800 pl-3 py-1">
          &quot;{citation.text}&quot;
        </div>
        <div className="mt-4 flex justify-end">
          <Button
            variant="outline"
            size="xs"
            className="gap-1"
            onClick={() => openViewer(citation)}
          >
            <span>View Source</span>
            <ExternalLink className="h-3 w-3" />
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
