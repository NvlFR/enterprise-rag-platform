import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '@/lib/api-client';
import axios from 'axios';

export interface Document {
  id: string;
  title: string;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  file_path: string;
  s3_key: string;
  created_at: string;
  doc_metadata?: {
    original_filename?: string;
    content_type?: string;
    file_size_bytes?: number;
    page_count?: number;
  };
}

export interface UseDocumentsOptions {
  pollingInterval?: number;
  search?: string;
  status?: string;
  sort_by?: string;
  order?: 'asc' | 'desc';
}

export const useDocuments = (options: UseDocumentsOptions = {}) => {
  const {
    pollingInterval = 5000,
    search,
    status,
    sort_by = 'created_at',
    order = 'desc'
  } = options;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchDocuments = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const params: Record<string, any> = {
        sort_by,
        order,
      };
      if (search) params.search = search;
      if (status && status !== 'all') params.status = status;

      const response = await apiClient.get('/documents', { params });
      setDocuments(response.data);
      setError(null);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch documents');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [search, status, sort_by, order]);

  const deleteDocument = async (id: string) => {
    try {
      await apiClient.delete(`/documents/${id}`);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
      return { success: true };
    } catch (err: unknown) {
      let message = 'Failed to delete document';
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.message || message;
      }
      return { success: false, error: message };
    }
  };

  const updateDocument = async (id: string, data: Partial<Document>) => {
    try {
      const response = await apiClient.patch(`/documents/${id}`, data);
      setDocuments((prev) =>
        prev.map((doc) => (doc.id === id ? response.data : doc))
      );
      return { success: true, data: response.data };
    } catch (err: unknown) {
      let message = 'Failed to update document';
      if (axios.isAxiosError(err)) {
        message = err.response?.data?.detail || err.message || message;
      }
      return { success: false, error: message };
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDocuments();
  }, [fetchDocuments]);

  // Polling logic
  useEffect(() => {
    const needsPolling = documents.some(
      (doc) => doc.status === 'uploaded' || doc.status === 'processing'
    );

    if (needsPolling && !pollingTimer.current) {
      pollingTimer.current = setInterval(() => {
        fetchDocuments(false);
      }, pollingInterval);
    } else if (!needsPolling && pollingTimer.current) {
      clearInterval(pollingTimer.current);
      pollingTimer.current = null;
    }

    return () => {
      if (pollingTimer.current) {
        clearInterval(pollingTimer.current);
        pollingTimer.current = null;
      }
    };
  }, [documents, fetchDocuments, pollingInterval]);

  return {
    documents,
    loading,
    error,
    refetch: fetchDocuments,
    deleteDocument,
    updateDocument
  };
};
