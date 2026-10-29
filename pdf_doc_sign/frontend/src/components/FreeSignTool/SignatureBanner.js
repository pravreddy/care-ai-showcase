/**
 * PlacingBanner — Alert bar shown when user is in "placing" mode.
 * Works for signature, text, and date placement.
 * Props:
 *   mode        — 'signature' | 'text' | 'date'
 *   sigSize     — current size (only shown for signature)
 *   setSigSize  — size setter (only used for signature)
 *   onCancel    — cancel placing mode
 */
import React from 'react';
import { Alert, Button, Slider, Typography } from '@mui/material';

const LABELS = {
  signature: 'Click on the PDF where you want to place your signature.',
  text: 'Click on the PDF where you want to place your text.',
  date: 'Click on the PDF where you want to place the date.',
};

export default function SignatureBanner({ mode = 'signature', sigSize, setSigSize, onCancel }) {
  return (
    <Alert severity="info" sx={{ mb: 2 }} data-testid="placing-banner">
      {LABELS[mode] || LABELS.signature}
      {mode === 'signature' && (
        <>
          {' '}Use the slider to adjust size.
          <Slider
            value={sigSize}
            onChange={(_, v) => setSigSize(v)}
            min={50} max={400}
            sx={{ ml: 2, width: 200, display: 'inline-block', verticalAlign: 'middle' }}
            data-testid="size-slider"
          />
        </>
      )}
      <Button size="small" onClick={onCancel} sx={{ ml: 2 }}>Cancel</Button>
    </Alert>
  );
}
