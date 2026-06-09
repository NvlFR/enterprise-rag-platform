import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';

export interface SourcePreview {
  chunk_id: string;
  document_id: string;
  document_title: string;
  content: string;
  metadata: Record<string, unknown>;
  context: Array<{
    id: string;
    index: number;
    content: string;
    is_target: boolean;
  }>;
}

export const useSourcePreview = () => {
  const [data, setData] = useState<SourcePreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreview = useCallback(async (chunkId: string, windowSize: number = 2) => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/sources/${chunkId}`, {
        params: { window_size: windowSize }
      });
      setData(response.data);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch source preview';
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetchPreview };
};
