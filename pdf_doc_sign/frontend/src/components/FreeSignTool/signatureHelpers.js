/**
 * signatureHelpers.js — Pure utility functions for the free sign tool.
 * No React, no state — just data transforms.
 */

export const CHECKMARK_DATA_URL = (() => {
  try {
    const c = document.createElement('canvas');
    c.width = 40; c.height = 40;
    const ctx = c.getContext('2d');
    ctx.strokeStyle = '#2e7d32';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(6, 20); ctx.lineTo(16, 30); ctx.lineTo(34, 10);
    ctx.stroke();
    return c.toDataURL('image/png');
  } catch { return ''; }
})();

export function generateTypedSignature(text, fontCss, color) {
  if (!text?.trim()) return null;
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  const fontSize = 52;
  const font = `italic ${fontSize}px ${fontCss}`;
  ctx.font = font;
  // Tight-bound the canvas to the actual text metrics so the PNG has no
  // excess transparent padding — otherwise the overlay Box ends up taller
  // than the visible text and covers adjacent table borders.
  const metrics = ctx.measureText(text);
  const ascent  = metrics.actualBoundingBoxAscent  || fontSize * 0.85;
  const descent = metrics.actualBoundingBoxDescent || fontSize * 0.25;
  const pad = 4;
  const w = Math.ceil(metrics.width) + pad * 2;
  const h = Math.ceil(ascent + descent) + pad * 2;
  c.width = w; c.height = h;
  // Re-set font (canvas resize resets context state)
  ctx.font = font;
  ctx.fillStyle = color || '#1a1a1a';
  ctx.fillText(text, pad, pad + ascent);
  return c.toDataURL('image/png');
}

export function generateTextDataUrl(text, fontSize, color, mode) {
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d');
  const font = mode === 'date'
    ? `${fontSize}px "Courier New", monospace`
    : `${fontSize}px Arial, sans-serif`;
  ctx.font = font;
  const pad = 6;
  c.width = Math.ceil(ctx.measureText(text).width) + pad * 2;
  c.height = Math.ceil(fontSize * 1.4) + pad;
  ctx.font = font;
  ctx.fillStyle = color;
  ctx.fillText(text, pad, fontSize + pad * 0.5);
  return c.toDataURL('image/png');
}

export function dataUrlToBytes(dataUrl) {
  const bin = atob(dataUrl.split(',')[1]);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr;
}

/**
 * Load an image data URL, chroma-key out its (near-)white background, and
 * return a new PNG data URL with proper transparency.
 *
 * Why: users routinely upload scanned/photographed signatures that are
 * either JPGs (no alpha) or flattened PNGs with a white background. When
 * embedded into the final PDF via pdf-lib.embedPng these produce a visible
 * off-white rectangle sitting over whatever PDF content is behind the
 * signature (e.g. table borders above/below the field). DigiSigner and
 * other e-sig tools handle this by alpha-keying the background at upload
 * time — this helper does the same.
 *
 * Pixels brighter than `threshold` fade linearly to transparent; pure
 * white becomes fully transparent. Dark ink is untouched. Anti-aliased
 * edges between ink and background get a proportional alpha which keeps
 * the signature looking smooth against any PDF background colour.
 */
export function stripWhiteBackground(sourceDataUrl, threshold = 230) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      try {
        const c = document.createElement('canvas');
        c.width = img.naturalWidth;
        c.height = img.naturalHeight;
        const ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, c.width, c.height);
        const data = imageData.data;
        const range = 255 - threshold;
        for (let i = 0; i < data.length; i += 4) {
          const r = data[i], g = data[i + 1], b = data[i + 2];
          const lightness = (Math.max(r, g, b) + Math.min(r, g, b)) / 2;
          if (lightness > threshold) {
            // Linear fade: threshold -> alpha unchanged,  255 -> alpha 0
            const originalAlpha = data[i + 3];
            const fadedAlpha = Math.round(originalAlpha * (255 - lightness) / range);
            data[i + 3] = Math.max(0, fadedAlpha);
          }
        }
        ctx.putImageData(imageData, 0, 0);
        resolve(c.toDataURL('image/png'));
      } catch (err) {
        reject(err);
      }
    };
    img.onerror = () => reject(new Error('Failed to load image for background removal'));
    img.src = sourceDataUrl;
  });
}
