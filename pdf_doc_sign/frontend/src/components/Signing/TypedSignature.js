/**
 * TypedSignature.js — Text-to-canvas signature input.
 * Uses CanvasPreview for consistent canvas styling.
 *
 * Props:
 *   signerName - default name to pre-fill
 *   onSave(blob) — called with PNG blob when user clicks "Use This Signature"
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Button, TextField } from '@mui/material';
import CanvasPreview from '../Common/CanvasPreview';

export default function TypedSignature({ signerName, onSave }) {
  const [name, setName] = useState(signerName || '');
  const canvasRef = useRef(null);

  const generateSignature = useCallback(() => {
    if (!name.trim() || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = 'italic 48px "Georgia", "Times New Roman", serif';
    ctx.fillStyle = '#000';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(name, canvas.width / 2, canvas.height / 2);
  }, [name]);

  useEffect(() => { generateSignature(); }, [generateSignature]);

  const saveSignature = () => {
    if (!name.trim()) return;
    canvasRef.current.toBlob((blob) => { if (blob) onSave(blob); }, 'image/png');
  };

  return (
    <Box>
      <TextField
        fullWidth size="small" label="Type your name"
        value={name} onChange={(e) => setName(e.target.value)}
        sx={{ mb: 2 }}
      />
      <CanvasPreview canvasRef={canvasRef} />
      <Button variant="contained" size="small" onClick={saveSignature} disabled={!name.trim()}>
        Use This Signature
      </Button>
    </Box>
  );
}
