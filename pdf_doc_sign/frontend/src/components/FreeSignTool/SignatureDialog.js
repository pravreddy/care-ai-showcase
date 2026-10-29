/**
 * SignatureDialog — Modal for creating signatures via Draw / Type / Upload.
 * Features: 6 font style previews, colour picker (black/blue/green),
 * draw canvas with clear, image upload preview.
 */
import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Tabs, Tab, Button, TextField, Paper, Box, Typography, Stack,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { SIG_FONTS, SIG_COLORS } from './freeSignConfig';

export default function SignatureDialog({
  open, onClose, onConfirm,
  sigCanvasRef, sigTab, setSigTab,
  typedText, setTypedText,
  sigImageUrl, onSigUpload,
  isDrawing, setIsDrawing,
  sigColor, setSigColor,
  selectedFont, setSelectedFont,
}) {
  const color = sigColor || '#1a1a1a';
  const font = selectedFont || SIG_FONTS[0].css;

  // ── Draw handlers ──────────────────────────────────────────────────────
  const getPos = (e) => {
    const canvas = sigCanvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top)  * scaleY,
    };
  };

  const startDraw = (e) => {
    setIsDrawing(true);
    const ctx = sigCanvasRef.current.getContext('2d');
    const pos = getPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    const ctx = sigCanvasRef.current.getContext('2d');
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = color;
    const pos = getPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  };

  const stopDraw = () => setIsDrawing(false);

  const clearCanvas = () => {
    const canvas = sigCanvasRef.current;
    if (canvas) canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ pb: 0 }}>Create Your Signature</DialogTitle>
      <DialogContent>
        <Tabs value={sigTab} onChange={(_, v) => setSigTab(v)} sx={{ mb: 2 }}>
          <Tab label="Draw"   data-testid="tab-draw" />
          <Tab label="Type"   data-testid="tab-type" />
          <Tab label="Upload" data-testid="tab-upload" />
        </Tabs>

        {/* ── Colour picker (Draw + Type tabs) ──────────────────────── */}
        {sigTab !== 2 && (
          <Stack data-testid="sig-color-picker" direction="row" spacing={1} sx={{ mb: 2 }}>
            {SIG_COLORS.map(c => (
              <Box
                key={c.value}
                onClick={() => setSigColor(c.value)}
                sx={{
                  width: 28, height: 28, borderRadius: '50%',
                  bgcolor: c.value, cursor: 'pointer',
                  border: color === c.value ? '3px solid #666' : '2px solid transparent',
                  boxShadow: color === c.value ? '0 0 0 2px white inset' : 'none',
                  transition: 'all 0.15s',
                }}
              />
            ))}
          </Stack>
        )}

        {/* ── DRAW ─────────────────────────────────────────────────── */}
        {sigTab === 0 && (
          <Box>
            <Paper variant="outlined" sx={{ mb: 1, bgcolor: '#fafafa', position: 'relative' }}>
              <canvas
                ref={sigCanvasRef}
                width={460} height={160}
                data-testid="sig-canvas"
                style={{ width: '100%', height: 160, cursor: 'crosshair', touchAction: 'none', display: 'block' }}
                onMouseDown={startDraw}
                onMouseMove={draw}
                onMouseUp={stopDraw}
                onMouseLeave={stopDraw}
              />
              <Typography variant="caption" color="text.disabled"
                sx={{ position: 'absolute', bottom: 8, left: 12, pointerEvents: 'none', fontSize: 10 }}>
                Draw your signature above
              </Typography>
            </Paper>
            <Button size="small" onClick={clearCanvas} startIcon={<DeleteIcon />} sx={{ color: 'text.secondary' }}>
              Clear
            </Button>
          </Box>
        )}

        {/* ── TYPE — 6 font previews ────────────────────────────────── */}
        {sigTab === 1 && (
          <Box>
            <TextField
              fullWidth
              placeholder="Type your name here"
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              inputProps={{ 'data-testid': 'sig-type-input' }}
              sx={{ mb: 2 }}
              autoFocus
            />
            <Box data-testid="sig-font-grid" sx={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: 1,
            }}>
              {SIG_FONTS.map(f => (
                <Paper
                  key={f.label}
                  variant="outlined"
                  onClick={() => setSelectedFont(f.css)}
                  sx={{
                    p: 1.5, textAlign: 'center', cursor: 'pointer',
                    border: font === f.css ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    bgcolor: font === f.css ? '#e3f2fd' : 'white',
                    '&:hover': { bgcolor: '#f5f5f5' },
                    minHeight: 64,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.15s',
                  }}
                >
                  <Typography sx={{
                    fontFamily: f.css,
                    fontSize: typedText ? Math.min(32, 200 / Math.max(typedText.length, 1)) : 28,
                    color,
                    lineHeight: 1.3,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    maxWidth: '100%',
                  }}>
                    {typedText || 'Signature'}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </Box>
        )}

        {/* ── UPLOAD ───────────────────────────────────────────────── */}
        {sigTab === 2 && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Button variant="outlined" component="label" sx={{ mb: 2 }}>
              Upload Signature Image
              <input type="file" hidden accept="image/*" onChange={onSigUpload} data-testid="sig-upload-input" />
            </Button>
            {sigImageUrl ? (
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <img src={sigImageUrl} alt="Signature" style={{ maxWidth: '100%', maxHeight: 120 }} data-testid="sig-upload-preview" />
              </Paper>
            ) : (
              <Typography variant="body2" color="text.disabled">
                Supported: PNG, JPG, GIF (transparent PNG works best)
              </Typography>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={onConfirm} data-testid="sig-confirm-btn"
          disabled={sigTab === 1 && !typedText?.trim()}
          sx={{ fontWeight: 700 }}>
          Use This Signature
        </Button>
      </DialogActions>
    </Dialog>
  );
}
