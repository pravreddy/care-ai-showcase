/**
 * CanvasPreview.js — Reusable canvas wrapper with consistent styling.
 *
 * Used by SignatureCanvas, TypedSignature, and UploadSignature
 * for a uniform look across all signature input methods.
 *
 * Defaults to SIGNATURE_CANVAS_WIDTH × SIGNATURE_CANVAS_HEIGHT
 * from utils/signature.js. Override via props if needed.
 */
import React from 'react';
import { Box } from '@mui/material';
import { SIGNATURE_CANVAS_WIDTH, SIGNATURE_CANVAS_HEIGHT } from '../../utils/signature';

export default function CanvasPreview({
  canvasRef,
  width = SIGNATURE_CANVAS_WIDTH,
  height = SIGNATURE_CANVAS_HEIGHT,
  cursor = 'default',
  touchAction,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onMouseLeave,
  onTouchStart,
  onTouchMove,
  onTouchEnd,
}) {
  return (
    <Box
      sx={{
        border: '2px dashed #ccc',
        borderRadius: 2,
        mb: 2,
        bgcolor: 'white',
        overflow: 'hidden',
        ...(touchAction && { touchAction }),
      }}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ width: '100%', height: 'auto', display: 'block', cursor }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseLeave}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      />
    </Box>
  );
}
