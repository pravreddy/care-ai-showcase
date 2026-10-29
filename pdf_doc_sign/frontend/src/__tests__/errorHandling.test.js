/**
 * errorHandling.test.js — Tests for centralised error message extraction.
 */
import {
  getApiErrorMessage, getUploadErrorMessage,
  getSigningErrorMessage, getDocumentErrorMessage, validateUploadFile,
} from '../utils/errorHandling';

const mockError = (status, data = {}) => ({ response: { status, data } });
const networkError = () => ({ message: 'Network Error' });

describe('getApiErrorMessage', () => {
  test('returns network error message', () => { expect(getApiErrorMessage(networkError())).toContain('Network error'); });
  test('returns 401 message', () => { expect(getApiErrorMessage(mockError(401))).toBe('Session expired. Please log in again.'); });
  test('returns 403 with custom error', () => { expect(getApiErrorMessage(mockError(403, { error: 'No access' }))).toBe('No access'); });
  test('returns 403 default', () => { expect(getApiErrorMessage(mockError(403))).toBe('You do not have permission to do this.'); });
  test('returns 404 default', () => { expect(getApiErrorMessage(mockError(404))).toBe('Not found.'); });
  test('returns 429 message', () => { expect(getApiErrorMessage(mockError(429))).toContain('Too many requests'); });
  test('returns 500 default', () => { expect(getApiErrorMessage(mockError(500))).toContain('Server error'); });
  test('extracts Django field errors', () => {
    const msg = getApiErrorMessage(mockError(400, { email: ['This field is required.'] }));
    expect(msg).toContain('Email');
  });
  test('extracts Django non_field_errors array', () => {
    expect(getApiErrorMessage(mockError(400, { non_field_errors: ['Invalid credentials', 'Account locked'] }))).toBe('Non field errors: Invalid credentials Account locked');
  });
  test('returns default fallback', () => { expect(getApiErrorMessage({})).toBe('Something went wrong. Please try again.'); });
});

describe('getUploadErrorMessage', () => {
  test('returns 403 document limit', () => { expect(getUploadErrorMessage(mockError(403))).toContain('Document limit reached'); });
  test('returns Django file error', () => { expect(getUploadErrorMessage(mockError(400, { file: ['Invalid PDF'] }))).toBe('Invalid PDF'); });
  test('falls back for network error', () => { expect(getUploadErrorMessage(networkError())).toContain('Network error'); });
});

describe('getSigningErrorMessage', () => {
  test('returns expired for 404', () => { expect(getSigningErrorMessage(mockError(404))).toContain('invalid or has expired'); });
  test('returns fallback for unknown', () => { expect(getSigningErrorMessage({})).toContain('Failed to submit signature'); });
});

describe('getDocumentErrorMessage', () => {
  test('returns not found for 404', () => { expect(getDocumentErrorMessage(mockError(404))).toContain('not found'); });
  test('includes operation in fallback', () => { expect(getDocumentErrorMessage({}, 'download')).toContain('Failed to download document'); });
});

describe('validateUploadFile', () => {
  const pdf   = (size) => ({ type: 'application/pdf',  name: 'test.pdf',  size });
  const docx  = (size) => ({ type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', name: 'test.docx', size });
  const png   = (size) => ({ type: 'image/png',         name: 'test.png',  size });
  const exe   = (size) => ({ type: 'application/octet-stream', name: 'bad.exe', size });

  test('returns error for null file', () => {
    expect(validateUploadFile(null)).toBe('Please select a file.');
  });
  test('returns null for valid PDF', () => {
    expect(validateUploadFile(pdf(1024 * 1024))).toBeNull();
  });
  test('returns null for valid DOCX', () => {
    expect(validateUploadFile(docx(1024 * 1024))).toBeNull();
  });
  test('returns null for valid PNG', () => {
    expect(validateUploadFile(png(1024 * 1024))).toBeNull();
  });
  test('rejects unsupported type (.exe)', () => {
    expect(validateUploadFile(exe(1024))).toContain('Invalid file type');
  });
  test('rejects over 20MB', () => {
    expect(validateUploadFile(pdf(21 * 1024 * 1024))).toContain('too large');
  });
  test('accepts at 20MB limit', () => {
    expect(validateUploadFile(pdf(20 * 1024 * 1024))).toBeNull();
  });
  test('accepts 11MB PDF (under new 20MB limit)', () => {
    expect(validateUploadFile(pdf(11 * 1024 * 1024))).toBeNull();
  });
});
