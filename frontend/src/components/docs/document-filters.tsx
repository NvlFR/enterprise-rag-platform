"use client"

import { Search, Filter, SortAsc, SortDesc } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { useDebounce } from "@/hooks/use-debounce"

interface DocumentFiltersProps {
  onSearch: (query: string) => void;
  onStatusChange: (status: string) => void;
  onSortChange: (sortBy: string, order: 'asc' | 'desc') => void;
  currentStatus: string;
  currentSortBy: string;
  currentOrder: 'asc' | 'desc';
}

export const DocumentFilters = ({
  onSearch,
  onStatusChange,
  onSortChange,
  currentStatus,
  currentSortBy,
  currentOrder,
}: DocumentFiltersProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 500);

  useEffect(() => {
    onSearch(debouncedSearch);
  }, [debouncedSearch, onSearch]);

  const toggleSort = () => {
    const newOrder = currentOrder === "asc" ? "desc" : "asc";
    onSortChange(currentSortBy, newOrder);
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white dark:bg-zinc-900 p-4 rounded-xl border dark:border-zinc-800 shadow-sm">
      <div className="relative w-full md:max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
        <Input
          placeholder="Search by filename..."
          className="pl-9 bg-zinc-50 dark:bg-zinc-800 border-none ring-offset-transparent focus-visible:ring-1 focus-visible:ring-blue-500"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="flex items-center gap-3 w-full md:w-auto">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-zinc-400" />
          <select
            className="bg-zinc-50 dark:bg-zinc-800 text-sm border-none rounded-md px-2 py-1.5 focus:ring-1 focus:ring-blue-500 outline-none min-w-[120px]"
            value={currentStatus}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="uploaded">Uploaded</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="h-6 w-px bg-zinc-200 dark:bg-zinc-700 mx-1" />

        <div className="flex items-center gap-2">
          <select
            className="bg-zinc-50 dark:bg-zinc-800 text-sm border-none rounded-md px-2 py-1.5 focus:ring-1 focus:ring-blue-500 outline-none min-w-[120px]"
            value={currentSortBy}
            onChange={(e) => onSortChange(e.target.value, currentOrder)}
          >
            <option value="created_at">Date Created</option>
            <option value="title">Filename</option>
          </select>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-zinc-500"
            onClick={toggleSort}
          >
            {currentOrder === "asc" ? (
              <SortAsc className="h-4 w-4" />
            ) : (
              <SortDesc className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
