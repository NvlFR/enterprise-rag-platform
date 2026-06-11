"use client"

import { FileText, Trash2, Edit2 } from "lucide-react"
import { StatusBadge } from "./status-badge"
import { formatDistanceToNow } from "date-fns"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useState } from "react"
import { toast } from "sonner"
import { Document } from "@/hooks/use-documents"
import { MetadataEditor } from "./metadata-editor"

interface DocumentListProps {
  documents: Document[];
  onDelete: (id: string) => Promise<{ success: boolean; error?: string }>;
  onUpdate: (id: string, data: Partial<Document>) => Promise<{ success: boolean; data?: any; error?: string }>;
  isFiltered?: boolean;
}

export const DocumentList = ({ documents, onDelete, onUpdate, isFiltered }: DocumentListProps) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const [editingDoc, setEditingDoc] = useState<Document | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const handleDeleteClick = (id: string) => {
    setDeletingId(id);
    setIsDeleteDialogOpen(true);
  };

  const handleEditClick = (doc: Document) => {
    setEditingDoc(doc);
    setIsEditorOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingId) return;

    setIsDeleting(true);
    const result = await onDelete(deletingId);
    setIsDeleting(false);
    setIsDeleteDialogOpen(false);
    setDeletingId(null);

    if (result.success) {
      toast.success("Document deleted successfully");
    } else {
      toast.error(result.error || "Failed to delete document");
    }
  };

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed rounded-2xl bg-white dark:bg-zinc-900 dark:border-zinc-800">
        <div className="h-12 w-12 rounded-full bg-zinc-50 flex items-center justify-center dark:bg-zinc-800 mb-4">
          <FileText className="h-6 w-6 text-zinc-400" />
        </div>
        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
          {isFiltered ? "No matching documents" : "No documents yet"}
        </p>
        <p className="text-xs text-zinc-500 mt-1 text-center max-w-[200px]">
          {isFiltered
            ? "Try adjusting your search or filters to find what you're looking for."
            : "Upload files above to see them listed here."}
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="group relative flex items-center gap-4 p-4 rounded-xl border bg-white hover:border-blue-200 hover:shadow-sm transition-all dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-zinc-700"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
            <FileText className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-zinc-900 truncate dark:text-zinc-100" title={doc.title}>
              {doc.title}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <StatusBadge status={doc.status} />
              <span className="text-[10px] text-zinc-400 font-medium bg-zinc-50 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                {doc.doc_metadata?.content_type?.split('/')[1]?.toUpperCase() || "FILE"}
              </span>
              <span className="text-[10px] text-zinc-400">
                {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-zinc-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
              onClick={() => handleEditClick(doc)}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-zinc-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              onClick={() => handleDeleteClick(doc.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}

      {editingDoc && (
        <MetadataEditor
          document={editingDoc}
          isOpen={isEditorOpen}
          onClose={() => setIsEditorOpen(false)}
          onSave={onUpdate}
        />
      )}

      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this document? This action cannot be undone and all associated chunks and embeddings will be removed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
