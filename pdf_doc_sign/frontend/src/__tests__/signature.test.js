import { SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT, SIGNATURE_UPLOAD_MAX_SIZE_MB, SIGNATURE_UPLOAD_ACCEPTED_TYPES } from '../utils/signature';

describe('Signature canvas constants', () => {
  test('canvas width is positive', () => { expect(SIGNATURE_CANVAS_WIDTH).toBeGreaterThan(0); });
  test('canvas height is positive', () => { expect(SIGNATURE_CANVAS_HEIGHT).toBeGreaterThan(0); });
  test('landscape aspect ratio', () => { expect(SIGNATURE_CANVAS_WIDTH).toBeGreaterThan(SIGNATURE_CANVAS_HEIGHT); });
  test('expected defaults', () => { expect(SIGNATURE_CANVAS_WIDTH).toBe(600); expect(SIGNATURE_CANVAS_HEIGHT).toBe(200); });
});

describe('Upload constraints', () => {
  test('max size is reasonable', () => { expect(SIGNATURE_UPLOAD_MAX_SIZE_MB).toBeGreaterThanOrEqual(1); expect(SIGNATURE_UPLOAD_MAX_SIZE_MB).toBeLessThanOrEqual(20); });
  test('accepts PNG and JPEG', () => { expect(SIGNATURE_UPLOAD_ACCEPTED_TYPES).toContain('image/png'); expect(SIGNATURE_UPLOAD_ACCEPTED_TYPES).toContain('image/jpeg'); });
  test('is non-empty array', () => { expect(Array.isArray(SIGNATURE_UPLOAD_ACCEPTED_TYPES)).toBe(true); expect(SIGNATURE_UPLOAD_ACCEPTED_TYPES.length).toBeGreaterThan(0); });
  test('does not accept PDFs', () => { expect(SIGNATURE_UPLOAD_ACCEPTED_TYPES).not.toContain('application/pdf'); });
});
