import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export const useDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/documents');
      setDocuments(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return { documents, loading, error, refetch: fetchDocuments };
};
