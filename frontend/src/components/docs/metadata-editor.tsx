"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Document } from "@/hooks/use-documents"
import { toast } from "sonner"
import { Tag, FileText, Calendar } from "lucide-react"
import { format } from "date-fns"

interface MetadataEditorProps {
  document: Document;
  isOpen: boolean;
  onClose: () => void;
  onSave: (id: string, data: Partial<Document>) => Promise<{ success: boolean; error?: string }>;
}

export const MetadataEditor = ({ document, isOpen, onClose, onSave }: MetadataEditorProps) => {
  const [title, setTitle] = useState(document.title);
  const [isSaving, setIsSaving] = useState(false);

  // Extract tags from metadata if they exist, otherwise empty array
  const initialTags = (document.doc_metadata?.tags as string[]) || [];
  const [tags, setTags] = useState<string[]>(initialTags);
  const [newTag, setNewTag] = useState("");

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error("Title cannot be empty");
      return;
    }

    setIsSaving(true);
    const result = await onSave(document.id, {
      title,
      doc_metadata: {
        ...document.doc_metadata,
        tags,
      }
    });
    setIsSaving(false);

    if (result.success) {
      toast.success("Document updated successfully");
      onClose();
    } else {
      toast.error(result.error || "Failed to update document");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Document Metadata</DialogTitle>
          <DialogDescription>
            Update your document information for better retrieval and organization.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Document Title
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
              className="bg-zinc-50 dark:bg-zinc-800"
            />
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300 flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Tags
            </label>
            <div className="flex gap-2">
              <Input
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                placeholder="Add a tag..."
                onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
                className="bg-zinc-50 dark:bg-zinc-800"
              />
              <Button type="button" variant="outline" onClick={handleAddTag}>Add</Button>
            </div>
            <div className="flex flex-wrap gap-2 min-h-[32px]">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-blue-900 dark:hover:text-blue-100 font-bold"
                  >
                    ×
                  </button>
                </span>
              ))}
              {tags.length === 0 && (
                <span className="text-xs text-zinc-400 italic">No tags added yet</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t dark:border-zinc-800">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1">
                <FileText className="h-3 w-3" />
                File Info
              </span>
              <p className="text-xs text-zinc-600 dark:text-zinc-400 truncate">
                {document.doc_metadata?.content_type || "Unknown type"}
              </p>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                {document.doc_metadata?.file_size_bytes
                  ? `${(document.doc_metadata.file_size_bytes / 1024 / 1024).toFixed(2)} MB`
                  : "Unknown size"}
              </p>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Created At
              </span>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                {format(new Date(document.created_at), "PPP")}
              </p>
              <p className="text-[10px] text-zinc-400">
                {format(new Date(document.created_at), "p")}
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
