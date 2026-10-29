/**
 * PdfViewer — Full-viewport editor.
 * PDF is rendered on <canvas>. Placed items are absolutely-positioned
 * <img> overlays so they can be selected, moved and deleted at any time.
 */
import React, { useRef, useState, useCallback } from 'react';
import {
  Box, Stack, Typography, Button, IconButton,
  Tooltip, Divider, TextField, Slider, CircularProgress,
} from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DrawIcon from '@mui/icons-material/Draw';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import CheckBoxOutlinedIcon from '@mui/icons-material/CheckBoxOutlined';
import UndoIcon from '@mui/icons-material/Undo';
import DownloadIcon from '@mui/icons-material/Download';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import AbcIcon from '@mui/icons-material/Abc';

const SIDEBAR_WIDTH = 96;

const SidebarTool = ({ icon, label, onClick, active, testId }) => (
  <Tooltip title={label} placement="right">
    <Box onClick={onClick} data-testid={testId} sx={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', gap: 0.5,
      py: 1.5, px: 1, borderRadius: 2, cursor: 'pointer', width: '100%',
      bgcolor: active ? '#e3f2fd' : 'transparent',
      border: active ? '1.5px solid #1976d2' : '1.5px solid transparent',
      color: active ? 'primary.main' : 'text.secondary',
      '&:hover': { bgcolor: '#f5f5f5', color: 'text.primary' },
      transition: 'all 0.15s',
    }}>
      <Box sx={{ fontSize: 26, display: 'flex', alignItems: 'center' }}>{icon}</Box>
      <Typography variant="caption" fontWeight={500} sx={{ fontSize: 10, lineHeight: 1 }}>{label}</Typography>
    </Box>
  </Tooltip>
);

// Corner resize handle positions
const HANDLES = [
  { id: 'nw', cursor: 'nw-resize', top: -5,  left: -5  },
  { id: 'ne', cursor: 'ne-resize', top: -5,  right: -5 },
  { id: 'sw', cursor: 'sw-resize', bottom: -5, left: -5 },
  { id: 'se', cursor: 'se-resize', bottom: -5, right: -5 },
];

// Single overlay item — draggable, resizable, deletable
function OverlayItem({ item, canvasRef, selected, onSelect, onDelete, onMove, onResize }) {
  const handleBodyMouseDown = useCallback((e) => {
    e.stopPropagation();
    onSelect(item.id);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const startX = e.clientX, startY = e.clientY;
    const origX = item.x, origY = item.y;
    const onMouseMove = (me) => {
      onMove(item.id, origX + (me.clientX - startX) * scaleX, origY + (me.clientY - startY) * scaleY);
    };
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [item, canvasRef, onSelect, onMove]);

  const handleResizeMouseDown = useCallback((e, handleId) => {
    e.stopPropagation();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const startX = e.clientX, startY = e.clientY;
    const origW = item.width, origH = item.height;
    const onMouseMove = (me) => {
      const dx = (me.clientX - startX) * scaleX;
      const dy = (me.clientY - startY) * scaleY;
      let newW = origW, newH = origH;
      if (handleId === 'se') { newW = Math.max(20, origW + dx); newH = Math.max(10, origH + dy); }
      if (handleId === 'sw') { newW = Math.max(20, origW - dx); newH = Math.max(10, origH + dy); }
      if (handleId === 'ne') { newW = Math.max(20, origW + dx); newH = Math.max(10, origH - dy); }
      if (handleId === 'nw') { newW = Math.max(20, origW - dx); newH = Math.max(10, origH - dy); }
      onResize(item.id, newW, newH);
    };
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [item, canvasRef, onResize]);

  const canvas = canvasRef.current;
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  // In jsdom rect dimensions are 0 — use canvas natural size as fallback
  const displayScaleX = (rect.width  || canvas.width  || 1) / (canvas.width  || 1);
  const displayScaleY = (rect.height || canvas.height || 1) / (canvas.height || 1);
  const displayX = (item.x - item.width  / 2) * displayScaleX;
  const displayY = (item.y - item.height / 2) * displayScaleY;
  const displayW = item.width  * displayScaleX;
  const displayH = item.height * displayScaleY;

  return (
    <Box
      onMouseDown={handleBodyMouseDown}
      sx={{
        position: 'absolute',
        left: displayX, top: displayY,
        width: displayW, height: displayH,
        cursor: 'move',
        outline: selected ? '2px solid #1976d2' : '1px dashed transparent',
        '&:hover': { outline: '1px dashed #90caf9' },
        userSelect: 'none',
        zIndex: selected ? 10 : 5,
      }}
    >
      <img
        src={item.dataUrl} alt={item.type}
        style={{ width: '100%', height: '100%', display: 'block', pointerEvents: 'none' }}
        draggable={false}
      />

      {/* Delete button */}
      {selected && (
        <Box
          onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
          sx={{
            position: 'absolute', top: -12, right: -12,
            width: 22, height: 22, borderRadius: '50%',
            bgcolor: '#d32f2f', color: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', '&:hover': { bgcolor: '#b71c1c' }, zIndex: 20,
          }}
        >
          <CloseIcon sx={{ fontSize: 14 }} />
        </Box>
      )}

      {/* Resize handles on corners */}
      {selected && HANDLES.map(h => (
        <Box
          key={h.id}
          onMouseDown={(e) => handleResizeMouseDown(e, h.id)}
          sx={{
            position: 'absolute',
            ...h,
            width: 10, height: 10,
            bgcolor: 'white',
            border: '2px solid #1976d2',
            borderRadius: '50%',
            cursor: h.cursor,
            zIndex: 21,
          }}
        />
      ))}
    </Box>
  );
}

export default function PdfViewer({
  canvasRef,
  currentPage, totalPages,
  onPageChange, onCanvasClick, placingSignature,
  onAddSig, onAddText, onAddDate, onAddInitials, onAddCheckmark,
  onUndo, onDownload, onClear,
  hasItems, downloading,
  signerName, onSignerNameChange,
  sigSize, onSigSizeChange,
  overlayItems, selectedItemId, onSelectItem, onDeleteItem, onMoveItem, onResizeItem,
}) {
  const canvasContainerRef = useRef(null);

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 56px)', overflow: 'hidden', bgcolor: '#f0f0f0' }}>

      {/* ── SIDEBAR ───────────────────────────────────────────────────── */}
      <Box sx={{
        width: SIDEBAR_WIDTH, flexShrink: 0,
        bgcolor: 'white', borderRight: '1px solid #e0e0e0',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        py: 2, gap: 0.5, overflowY: 'auto',
      }}>
        <Typography variant="caption" color="text.disabled"
          sx={{ fontSize: 9, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Tools
        </Typography>

        <SidebarTool icon={<DrawIcon fontSize="inherit" />} label="Sign"
          onClick={onAddSig} active={placingSignature === 'signature'} testId="add-signature-btn" />
        <SidebarTool icon={<AbcIcon fontSize="inherit" />} label="Initials"
          onClick={onAddInitials} active={placingSignature === 'initials'} testId="add-initials-btn" />
        <SidebarTool icon={<TextFieldsIcon fontSize="inherit" />} label="Text"
          onClick={onAddText} active={placingSignature === 'text'} testId="add-text-btn" />
        <SidebarTool icon={<CalendarTodayIcon fontSize="inherit" />} label="Date"
          onClick={onAddDate} active={placingSignature === 'date'} testId="add-date-btn" />
        <SidebarTool icon={<CheckBoxOutlinedIcon fontSize="inherit" />} label="Checkmark"
          onClick={onAddCheckmark} active={placingSignature === 'checkmark'} testId="add-checkmark-btn" />

        <Divider sx={{ width: '80%', my: 1 }} />

        <Typography variant="caption" color="text.disabled"
          sx={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Your name
        </Typography>
        <Box sx={{ px: 1, width: '100%' }}>
          <TextField
            size="small" value={signerName}
            onChange={(e) => onSignerNameChange(e.target.value)}
            placeholder="John Smith"
            inputProps={{ 'data-testid': 'signer-name-input', style: { fontSize: 11, padding: '6px 8px' } }}
            sx={{ width: '100%', '& .MuiOutlinedInput-root': { borderRadius: 1.5 } }}
          />
        </Box>
        <Typography variant="caption" color="text.disabled"
          sx={{ fontSize: 9, textAlign: 'center', px: 1 }}>
          Pre-fills typed sig
        </Typography>

        <Divider sx={{ width: '80%', my: 1 }} />

        <Typography variant="caption" color="text.disabled"
          sx={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Sig size
        </Typography>
        <Box sx={{ px: 1.5, width: '100%' }}>
          <Slider
            value={sigSize} onChange={(_, v) => onSigSizeChange(v)}
            min={40} max={300} step={10} size="small"
            sx={{ color: 'primary.main' }}
          />
        </Box>
        <Typography variant="caption" color="text.disabled" sx={{ fontSize: 9 }}>
          {sigSize}px
        </Typography>

        {/* Hint when item selected */}
        {selectedItemId && (
          <>
            <Divider sx={{ width: '80%', my: 1 }} />
            <Typography variant="caption" color="primary" sx={{ fontSize: 9, textAlign: 'center', px: 1 }}>
              Drag to move
            </Typography>
            <Tooltip title="Delete selected item">
              <IconButton size="small" color="error"
                onClick={() => onDeleteItem(selectedItemId)}
                sx={{ mt: 0.5 }}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </>
        )}
      </Box>

      {/* ── MAIN AREA ─────────────────────────────────────────────────── */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Top bar */}
        <Box sx={{
          height: 52, px: 2, flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          bgcolor: 'white', borderBottom: '1px solid #e0e0e0',
        }}>
          {/* Page nav */}
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <IconButton size="small" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage <= 1} data-testid="prev-page">
              <ChevronLeftIcon />
            </IconButton>
            <Typography variant="body2" fontWeight={600} sx={{ minWidth: 90, textAlign: 'center' }} data-testid="page-info">
              Page {currentPage} of {totalPages}
            </Typography>
            <IconButton size="small" onClick={() => onPageChange(currentPage + 1)} disabled={currentPage >= totalPages} data-testid="next-page">
              <ChevronRightIcon />
            </IconButton>
          </Stack>

          {/* Placing banner */}
          {placingSignature && (
            <Box data-testid="placing-banner" sx={{
              display: 'flex', alignItems: 'center', gap: 1,
              bgcolor: '#fff3e0', px: 2, py: 0.5, borderRadius: 2,
              border: '1px solid #ffcc02',
            }}>
              <Typography variant="body2" fontWeight={600} color="warning.dark">
                Click on the document to place your {placingSignature}
              </Typography>
              <IconButton size="small" onClick={() => onCanvasClick({ _cancel: true })}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          )}

          {/* Right actions */}
          <Stack direction="row" spacing={1} alignItems="center">
            {hasItems && (
              <Tooltip title="Undo last item">
                <IconButton size="small" onClick={onUndo}><UndoIcon fontSize="small" /></IconButton>
              </Tooltip>
            )}
            <Button variant="text" size="small" onClick={onClear}
              sx={{ textTransform: 'none', color: 'text.secondary', fontSize: 13 }}>
              Close
            </Button>
            <Button
              variant="contained"
              startIcon={downloading ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
              onClick={onDownload}
              disabled={!hasItems || downloading}
              size="small"
              data-testid="download-btn"
              sx={{ textTransform: 'none', fontWeight: 700, borderRadius: 2, px: 2 }}
            >
              {downloading ? 'Generating…' : 'Download'}
            </Button>
          </Stack>
        </Box>

        {/* Canvas + overlays */}
        <Box sx={{ flex: 1, overflow: 'auto', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', bgcolor: '#525659', p: 3 }}>
          {/* Wrapper sized to match rendered canvas */}
          <Box
            ref={canvasContainerRef}
            sx={{ position: 'relative', display: 'inline-block', lineHeight: 0 }}
            onClick={(e) => {
              // Deselect if clicking on background (not an overlay item)
              if (e.target === canvasRef.current) {
                onSelectItem(null);
                onCanvasClick(e);
              }
            }}
          >
            <canvas
              ref={canvasRef}
              data-testid="pdf-canvas"
              style={{
                display: 'block',
                maxWidth: '100%',
                cursor: placingSignature ? 'crosshair' : 'default',
                boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
              }}
            />
            {/* Overlay items */}
            {overlayItems.map(item => (
              <OverlayItem
                key={item.id}
                item={item}
                canvasRef={canvasRef}
                selected={selectedItemId === item.id}
                onSelect={onSelectItem}
                onDelete={onDeleteItem}
                onMove={onMoveItem}
                onResize={onResizeItem}
              />
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
