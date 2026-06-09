"use client"

import * as React from "react"
import { Citation } from "@/types/chat"
import { SourcePopover } from "./source-popover"
import { cn } from "@/lib/utils"

interface CitationMarkerProps {
  id: string
  citations: Citation[]
}

export function CitationMarker({ id, citations }: CitationMarkerProps) {
  const citation = citations.find((c) => c.id.toString() === id)

  if (!citation) {
    return <span className="text-zinc-400">[{id}]</span>
  }

  return (
    <SourcePopover citation={citation}>
      <button
        type="button"
        className={cn(
          "inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-sm bg-blue-100 text-[10px] font-bold text-blue-700 hover:bg-blue-200 focus:outline-none focus:ring-1 focus:ring-blue-400 focus:ring-offset-1 dark:bg-blue-900/40 dark:text-blue-300 dark:hover:bg-blue-900/60 transition-colors mx-0.5 align-top mt-0.5",
        )}
      >
        {id}
      </button>
    </SourcePopover>
  )
}
