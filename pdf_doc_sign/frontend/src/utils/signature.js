/**
 * signature.js — Shared constants for signature canvas dimensions.
 *
 * All signature input methods (Draw, Type, Upload) use the same
 * canvas size for consistency. Change these values to resize
 * all signature canvases across the app.
 */

export const SIGNATURE_CANVAS_WIDTH = 600;
export const SIGNATURE_CANVAS_HEIGHT = 200;

// Upload constraints
export const SIGNATURE_UPLOAD_MAX_SIZE_MB = 2;
export const SIGNATURE_UPLOAD_ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
