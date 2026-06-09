"use client"

import * as React from "react"
import { Citation } from "@/types/chat"
import { SourceViewer } from "@/components/chat/source-viewer"

interface SourceViewerContextType {
  openViewer: (citation: Citation) => void
}

const SourceViewerContext = React.createContext<SourceViewerContextType | undefined>(undefined)

export function SourceViewerProvider({ children }: { children: React.ReactNode }) {
  const [selectedCitation, setSelectedCitation] = React.useState<Citation | null>(null)
  const [isOpen, setIsOpen] = React.useState(false)

  const openViewer = React.useCallback((citation: Citation) => {
    setSelectedCitation(citation)
    setIsOpen(true)
  }, [])

  const closeViewer = React.useCallback(() => {
    setIsOpen(false)
    // Don't clear selectedCitation immediately to avoid layout shift in viewer during close animation
  }, [])

  return (
    <SourceViewerContext.Provider value={{ openViewer }}>
      {children}
      <SourceViewer
        citation={selectedCitation}
        isOpen={isOpen}
        onClose={closeViewer}
      />
    </SourceViewerContext.Provider>
  )
}

export const useSourceViewer = () => {
  const context = React.useContext(SourceViewerContext)
  if (context === undefined) {
    throw new Error("useSourceViewer must be used within a SourceViewerProvider")
  }
  return context
}
