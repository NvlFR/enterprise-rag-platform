"use client"

import ProtectedRoute from "@/components/auth/protected-route"
import { ChatLayout } from "@/components/chat/chat-layout"
import { UploadZone } from "@/components/docs/upload-zone"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useDocuments } from "@/hooks/use-documents"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DocumentList } from "@/components/docs/document-list"
import { DocumentFilters } from "@/components/docs/document-filters"
import { useState } from "react"

export default function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [order, setOrder] = useState<'asc' | 'desc'>("desc");

  const { documents, loading, refetch, deleteDocument, updateDocument } = useDocuments({
    search,
    status,
    sort_by: sortBy,
    order,
  })

  const handleSortChange = (newSortBy: string, newOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy);
    setOrder(newOrder);
  };

  return (
    <ProtectedRoute>
      <ChatLayout>
        <div className="flex h-full flex-col bg-zinc-50 dark:bg-zinc-950">
          <header className="flex h-14 items-center justify-between border-b bg-white px-6 dark:bg-zinc-900">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <h1 className="text-sm font-semibold">Document Management</h1>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()} disabled={loading}>
              Refresh
            </Button>
          </header>

          <ScrollArea className="flex-1">
            <div className="mx-auto max-w-4xl p-8 space-y-12">
              <section className="space-y-6">
                <div className="space-y-1 text-center">
                  <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Upload Knowledge</h2>
                  <p className="text-zinc-500">Add documents to EKA&apos;s knowledge base to start chatting with them.</p>
                </div>
                <UploadZone onUploadComplete={() => refetch()} />
              </section>

              <section className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Your Documents</h3>
                  <span className="text-xs text-zinc-500 font-medium bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-full">
                    {documents.length} Files
                  </span>
                </div>

                <DocumentFilters
                  onSearch={setSearch}
                  onStatusChange={setStatus}
                  onSortChange={handleSortChange}
                  currentStatus={status}
                  currentSortBy={sortBy}
                  currentOrder={order}
                />

                {loading && documents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 space-y-3">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-blue-600" />
                    <p className="text-sm text-zinc-500">Loading documents...</p>
                  </div>
                ) : (
                  <DocumentList
                    documents={documents}
                    onDelete={deleteDocument}
                    onUpdate={updateDocument}
                    isFiltered={search !== "" || status !== "all"}
                  />
                )}
              </section>
            </div>
          </ScrollArea>
        </div>
      </ChatLayout>
    </ProtectedRoute>
  )
}
