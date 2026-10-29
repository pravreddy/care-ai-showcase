/**
 * errorHandling.js — Centralised error message extraction for API responses.
 *
 * Usage:
 *   import { getApiErrorMessage, getUploadErrorMessage } from '../utils/errorHandling';
 *
 *   catch (err) {
 *     setError(getApiErrorMessage(err));
 *   }
 */

// ─── Generic API error extraction ───────────────────────────
// Works for any Django REST Framework response.
export const getApiErrorMessage = (err, fallback = 'Something went wrong. Please try again.') => {
  // Network / connection error
  if (err.message === 'Network Error') {
    return 'Network error — please check your internet connection and try again.';
  }

  const status = err.response?.status;
  const data = err.response?.data;

  // Common HTTP status codes
  if (status === 401) return 'Session expired. Please log in again.';
  if (status === 403) return data?.error || data?.detail || 'You do not have permission to do this.';
  if (status === 404) return data?.error || data?.detail || 'Not found.';
  if (status === 429) return 'Too many requests. Please wait a moment and try again.';
  if (status === 500) return data?.error || 'Server error. Please try again later.';
  if (status === 502) return 'Service temporarily unavailable. Please try again in a moment.';
  if (status === 503) return 'Service is undergoing maintenance. Please try again shortly.';

  // Django REST Framework field-level errors (e.g. { "email": ["This field is required."] })
  if (data && typeof data === 'object' && !data.error && !data.detail) {
    const fieldErrors = extractDjangoFieldErrors(data);
    if (fieldErrors) return fieldErrors;
  }

  // Explicit error/detail keys
  if (data?.error) return data.error;
  if (data?.detail) return data.detail;
  if (data?.message) return data.message;

  // Non-field errors from DRF
  if (data?.non_field_errors) {
    return Array.isArray(data.non_field_errors)
      ? data.non_field_errors.join(' ')
      : data.non_field_errors;
  }

  return fallback;
};


// ─── Upload-specific error extraction ───────────────────────
export const getUploadErrorMessage = (err, maxFileSizeMB = 10) => {
  const status = err.response?.status;
  const data = err.response?.data;

  const statusMessages = {
    403: 'Document limit reached. Upgrade your plan to upload more documents.',
    413: `File is too large for the server. Maximum size is ${maxFileSizeMB} MB. Try compressing the PDF first using smallpdf.com or ilovepdf.com.`,
  };

  if (statusMessages[status]) return statusMessages[status];

  // Django file field validation error
  if (data?.file) {
    return Array.isArray(data.file) ? data.file.join(' ') : data.file;
  }

  return getApiErrorMessage(err, 'Failed to upload document. Please try again or use a smaller file.');
};


// ─── Signing-specific error extraction ──────────────────────
export const getSigningErrorMessage = (err) => {
  const status = err.response?.status;

  if (status === 404) return 'This signing link is invalid or has expired.';

  return getApiErrorMessage(err, 'Failed to submit signature. Please try again.');
};


// ─── Document operation errors ──────────────────────────────
export const getDocumentErrorMessage = (err, operation = 'process') => {
  const status = err.response?.status;

  if (status === 404) return 'Document not found. It may have been deleted.';
  if (status === 403) return 'You do not have permission to access this document.';

  return getApiErrorMessage(err, `Failed to ${operation} document. Please try again.`);
};


// ─── File validation (client-side, before upload) ───────────
const ALLOWED_UPLOAD_TYPES = {
  'application/pdf': 'pdf',
  'application/msword': 'doc',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
  'image/jpeg': 'jpg',
  'image/png': 'png',
};

export const validateUploadFile = (file, { maxSizeMB = 20 } = {}) => {
  if (!file) return 'Please select a file.';

  // Check by MIME type OR extension (some browsers report wrong MIME for .docx)
  const ext = file.name.split('.').pop().toLowerCase();
  const allowedExts = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'];
  const mimeAllowed = ALLOWED_UPLOAD_TYPES[file.type];
  const extAllowed = allowedExts.includes(ext);

  if (!mimeAllowed && !extAllowed) {
    return 'Invalid file type. Supported formats: PDF, DOC, DOCX, JPG, PNG.';
  }

  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    return `File is too large (${sizeMB} MB). Maximum size is ${maxSizeMB} MB.`;
  }

  return null; // No error
};


// ─── Helper: extract Django field-level errors ──────────────
function extractDjangoFieldErrors(data) {
  const errors = [];
  for (const [field, msgs] of Object.entries(data)) {
    if (Array.isArray(msgs)) {
      const fieldName = field.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());
      errors.push(`${fieldName}: ${msgs.join(' ')}`);
    } else if (typeof msgs === 'string') {
      errors.push(msgs);
    }
  }
  return errors.length > 0 ? errors.join(' ') : null;
}
