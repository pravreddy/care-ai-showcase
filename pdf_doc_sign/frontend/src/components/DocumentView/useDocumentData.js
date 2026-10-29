import { useState, useEffect, useCallback } from 'react';
import { documentService } from '../../services/api';
import { getDocumentErrorMessage } from '../../utils/errorHandling';

/**
 * Custom hook for loading document data and audit logs.
 * Provides reload() to refresh after actions (remind, download, etc).
 */
export function useDocumentData(id) {
  const [document, setDocument] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [doc, logs] = await Promise.all([
        documentService.get(id),
        documentService.auditLog(id).catch(() => []),
      ]);
      setDocument(doc);
      setAuditLog(logs || []);
      setError('');
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'load'));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  return { document, auditLog, loading, error, setError, reload: load };
}

/**
 * Status → MUI color mapping.
 */
export function getStatusColor(status) {
  switch (status) {
    case 'SIGNED': return 'success';
    case 'PENDING': return 'warning';
    case 'DRAFT': return 'default';
    case 'EXPIRED': case 'CANCELLED': return 'error';
    default: return 'default';
  }
}
