"use client"

import ProtectedRoute from "@/components/auth/protected-route"
import { ChatLayout } from "@/components/chat/chat-layout"
import { UploadZone } from "@/components/docs/upload-zone"
import { FileText, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useDocuments } from "@/hooks/use-documents"
import { ScrollArea } from "@/components/ui/scroll-area"
import { formatDistanceToNow } from "date-fns"

export default function DocumentsPage() {
  const { documents, loading, refetch } = useDocuments()

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

                {loading && documents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 space-y-3">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-300 border-t-blue-600" />
                    <p className="text-sm text-zinc-500">Loading documents...</p>
                  </div>
                ) : documents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed rounded-2xl bg-white dark:bg-zinc-900 dark:border-zinc-800">
                    <div className="h-12 w-12 rounded-full bg-zinc-50 flex items-center justify-center dark:bg-zinc-800 mb-4">
                      <FileText className="h-6 w-6 text-zinc-400" />
                    </div>
                    <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">No documents yet</p>
                    <p className="text-xs text-zinc-500 mt-1 text-center max-w-[200px]">Upload files above to see them listed here.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {documents.map((doc: { id: string; title: string; status: string; created_at: string; doc_metadata?: { content_type?: string } }) => (
                      <div
                        key={doc.id}
                        className="group relative flex items-center gap-4 p-4 rounded-xl border bg-white hover:border-blue-200 hover:shadow-sm transition-all dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-zinc-700"
                      >
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-zinc-900 truncate dark:text-zinc-100">{doc.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className={cn(
                              "text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider",
                              doc.status === "completed" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                              doc.status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                              doc.status === "processing" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" :
                              "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                            )}>
                              {doc.status}
                            </span>
                            <span className="text-[10px] text-zinc-400 font-medium bg-zinc-50 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                              {doc.doc_metadata?.content_type?.split('/')[1]?.toUpperCase() || "FILE"}
                            </span>
                            <span className="text-[10px] text-zinc-400">
                              {formatDistanceToNow(new Date(doc.created_at || new Date().toISOString()), { addSuffix: true })}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </ScrollArea>
        </div>
      </ChatLayout>
    </ProtectedRoute>
  )
}
