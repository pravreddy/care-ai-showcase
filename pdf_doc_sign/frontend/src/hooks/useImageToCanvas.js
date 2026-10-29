/**
 * useImageToCanvas.js — Custom hook for loading an image file onto a canvas.
 *
 * Handles file validation, FileReader, Image loading, and centered drawing
 * on a fixed-size canvas with white background.
 *
 * Uses shared constants from utils/signature.js for canvas dimensions
 * and upload constraints.
 *
 * Usage:
 *   const { preview, error, processFile, save, clear } = useImageToCanvas(canvasRef, onSave);
 */
import { useState, useCallback } from 'react';
import {
  SIGNATURE_CANVAS_WIDTH,
  SIGNATURE_CANVAS_HEIGHT,
  SIGNATURE_UPLOAD_MAX_SIZE_MB,
  SIGNATURE_UPLOAD_ACCEPTED_TYPES,
} from '../utils/signature';

export default function useImageToCanvas(canvasRef, onSave) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');

  const drawToCanvas = useCallback((img) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Clear to fully transparent instead of painting white behind the
    // image — uploaded PNGs with real transparency are preserved, and
    // any surrounding padding stays transparent so it doesn't cover PDF
    // content when the signature is placed into a field.
    ctx.clearRect(0, 0, SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT);

    const padding = 16;
    const maxW = SIGNATURE_CANVAS_WIDTH - padding * 2;
    const maxH = SIGNATURE_CANVAS_HEIGHT - padding * 2;
    const ratio = Math.min(maxW / img.width, maxH / img.height, 1);
    const w = img.width * ratio;
    const h = img.height * ratio;
    const x = (SIGNATURE_CANVAS_WIDTH - w) / 2;
    const y = (SIGNATURE_CANVAS_HEIGHT - h) / 2;

    ctx.drawImage(img, x, y, w, h);

    // Chroma-key out any (near-)white background that came from a JPG or
    // a flattened PNG. Without this the uploaded signature embeds as an
    // opaque rectangle over whatever PDF content sits behind the field
    // (table borders above/below, underlines, etc.). Matches DigiSigner.
    try {
      const threshold = 230;
      const range = 255 - threshold;
      const imageData = ctx.getImageData(0, 0, SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const lightness = (Math.max(r, g, b) + Math.min(r, g, b)) / 2;
        if (lightness > threshold) {
          const originalAlpha = data[i + 3];
          data[i + 3] = Math.max(0, Math.round(originalAlpha * (255 - lightness) / range));
        }
      }
      ctx.putImageData(imageData, 0, 0);
    } catch {
      // getImageData can throw on cross-origin canvases — fine to skip,
      // the signature will still render (just without transparency).
    }
  }, [canvasRef]);

  const processFile = useCallback((file) => {
    if (!file) return;
    setError('');

    if (!SIGNATURE_UPLOAD_ACCEPTED_TYPES.includes(file.type)) {
      setError('Please upload a PNG, JPG, or WebP image.');
      return;
    }
    if (file.size > SIGNATURE_UPLOAD_MAX_SIZE_MB * 1024 * 1024) {
      setError(`Image is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${SIGNATURE_UPLOAD_MAX_SIZE_MB} MB.`);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      setPreview(dataUrl);

      const img = new Image();
      img.onload = () => drawToCanvas(img);
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  }, [drawToCanvas]);

  const save = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !preview) return;
    canvas.toBlob((blob) => {
      if (blob) onSave(blob);
    }, 'image/png');
  }, [canvasRef, preview, onSave]);

  const clear = useCallback(() => {
    setPreview(null);
    setError('');
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.getContext('2d').clearRect(0, 0, SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT);
    }
  }, [canvasRef]);

  return { preview, error, processFile, save, clear };
}
