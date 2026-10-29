/**
 * UploadSignature.js — Upload a PNG/JPG image of your signature.
 *
 * Uses useImageToCanvas hook for file processing and canvas rendering.
 * Uses CanvasPreview for consistent canvas styling.
 * Uses shared constants from utils/signature.js.
 *
 * Props:
 *   onSave(blob) — called with PNG blob when user clicks "Use This Signature"
 */
import React, { useRef } from 'react';
import { Box, Button, Typography, Alert } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import useImageToCanvas from '../../hooks/useImageToCanvas';
import CanvasPreview from '../Common/CanvasPreview';
import { SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT, SIGNATURE_UPLOAD_MAX_SIZE_MB } from '../../utils/signature';

export default function UploadSignature({ onSave }) {
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const { preview, error, processFile, save, clear } = useImageToCanvas(canvasRef, onSave);

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); e.stopPropagation(); };

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <input
        ref={fileInputRef}
        type="file"
        accept=".png,.jpg,.jpeg,.webp"
        style={{ display: 'none' }}
        onChange={(e) => { if (e.target.files?.[0]) processFile(e.target.files[0]); }}
      />

      {!preview ? (
        <Box
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          sx={{
            border: '2px dashed #ccc', borderRadius: 2, p: 4, mb: 2,
            bgcolor: 'white', textAlign: 'center', cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': { borderColor: '#1565c0', bgcolor: 'rgba(21, 101, 192, 0.04)' },
          }}
        >
          <CloudUploadIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
          <Typography variant="body1" color="text.secondary">
            Click or drag an image of your signature
          </Typography>
          <Typography variant="caption" color="text.disabled">
            PNG, JPG, or WebP · Max {SIGNATURE_UPLOAD_MAX_SIZE_MB} MB
          </Typography>
        </Box>
      ) : (
        <CanvasPreview canvasRef={canvasRef} />
      )}

      {/* Hidden canvas for processFile to draw onto before preview shows */}
      {!preview && (
        <canvas ref={canvasRef} width={SIGNATURE_CANVAS_WIDTH} height={SIGNATURE_CANVAS_HEIGHT} style={{ display: 'none' }} />
      )}

      {preview && (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" size="small" onClick={() => { clear(); if (fileInputRef.current) fileInputRef.current.value = ''; }}>
            Change Image
          </Button>
          <Button variant="contained" size="small" onClick={save}>
            Use This Signature
          </Button>
        </Box>
      )}
    </Box>
  );
}
