/**
 * useUpload.js — Custom hook for document upload with progress tracking.
 *
 * Usage:
 *   const { uploading, progress, error, success, handleUpload, setError, clearMessages } = useUpload(onSuccess);
 *   handleUpload(file, title);
 */
import { useState, useCallback, useRef } from 'react';
import { documentService } from '../services/api';
import { getUploadErrorMessage, validateUploadFile } from '../utils/errorHandling';

const MAX_FILE_SIZE_MB = 20; // 20MB to accommodate images/office docs before server-side conversion

export default function useUpload(onSuccess) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const progressInterval = useRef(null);

  const clearMessages = useCallback(() => {
    setError('');
    setSuccess('');
  }, []);

  const handleUpload = useCallback(async (file, title) => {
    // Client-side validation
    const validationError = validateUploadFile(file, { maxSizeMB: MAX_FILE_SIZE_MB });
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!title?.trim()) {
      setError('Please enter a document title.');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');
    setProgress(0);

    // Simulate progress while uploading
    progressInterval.current = setInterval(() => {
      setProgress(p => Math.min(p + 10, 90));
    }, 200);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title.trim());

      const result = await documentService.upload(formData);

      clearInterval(progressInterval.current);
      setProgress(100);

      // Build success message
      let msg = `Document "${result.title}" uploaded successfully!`;
      if (result.was_compressed) {
        msg += ` (Optimised — ${result.compression_savings}% smaller)`;
      }
      setSuccess(msg);

      if (onSuccess) onSuccess(result);
    } catch (err) {
      clearInterval(progressInterval.current);
      setProgress(0);
      setError(getUploadErrorMessage(err, MAX_FILE_SIZE_MB));
    } finally {
      setUploading(false);
    }
  }, [onSuccess]);

  return {
    uploading,
    progress,
    error,
    success,
    handleUpload,
    setError,
    setSuccess,
    clearMessages,
    maxFileSizeMB: MAX_FILE_SIZE_MB,
  };
}
