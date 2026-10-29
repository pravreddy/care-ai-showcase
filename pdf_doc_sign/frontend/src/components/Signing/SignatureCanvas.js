/**
 * SignatureCanvas.js — Hand-drawn signature input via canvas.
 * Uses CanvasPreview for consistent canvas styling.
 *
 * Props:
 *   onSave(blob) — called with PNG blob when user clicks "Use This Signature"
 */
import React, { useRef, useState } from 'react';
import { Box, Button } from '@mui/material';
import CanvasPreview from '../Common/CanvasPreview';
import { SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT } from '../../utils/signature';

export default function SignatureCanvas({ onSave }) {
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);

  const getCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: (clientX - rect.left) * (canvas.width / rect.width),
      y: (clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const startDraw = (e) => {
    e.preventDefault();
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getCoords(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setDrawing(true);
  };

  const draw = (e) => {
    if (!drawing) return;
    e.preventDefault();
    const ctx = canvasRef.current.getContext('2d');
    const { x, y } = getCoords(e);
    ctx.lineTo(x, y);
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    setHasDrawn(true);
  };

  const stopDraw = () => setDrawing(false);

  const clearCanvas = () => {
    canvasRef.current.getContext('2d').clearRect(0, 0, SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT);
    setHasDrawn(false);
  };

  const saveSignature = () => {
    if (!hasDrawn) return;
    canvasRef.current.toBlob((blob) => { if (blob) onSave(blob); }, 'image/png');
  };

  return (
    <Box>
      <CanvasPreview
        canvasRef={canvasRef}
        cursor="crosshair"
        touchAction="none"
        onMouseDown={startDraw}
        onMouseMove={draw}
        onMouseUp={stopDraw}
        onMouseLeave={stopDraw}
        onTouchStart={startDraw}
        onTouchMove={draw}
        onTouchEnd={stopDraw}
      />
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button variant="outlined" size="small" onClick={clearCanvas}>Clear</Button>
        <Button variant="contained" size="small" onClick={saveSignature} disabled={!hasDrawn}>
          Use This Signature
        </Button>
      </Box>
    </Box>
  );
}
