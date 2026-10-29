/**
 * PrepareDocument.js — Place signature fields on a PDF before sending for signing.
 *
 * Two ways to add fields:
 *   1. Click a tool in the sidebar, then click on the PDF to place
 *   2. Right-click on the PDF to add a field at that position
 *
 * Placed fields are empty placeholder boxes — the signer will fill them in
 * later. They can be freely moved (drag body) and resized (4 corner handles)
 * before the document is sent, matching the free-sign-tool's placement UX.
 *
 * Fields are stored as percentage coordinates so they scale with any render size.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Button, IconButton, Alert, CircularProgress,
  Divider, AppBar, Toolbar, Menu, MenuItem, ListItemIcon,
  ListItemText, Tooltip, Select, FormControl, InputLabel,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';
import SendIcon from '@mui/icons-material/Send';
import DrawIcon from '@mui/icons-material/Draw';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import PersonIcon from '@mui/icons-material/Person';
import AbcIcon from '@mui/icons-material/Abc';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CheckBoxOutlinedIcon from '@mui/icons-material/CheckBoxOutlined';
import DeleteIcon from '@mui/icons-material/Delete';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import CloseIcon from '@mui/icons-material/Close';
import { documentService } from '../../services/api';
import { getDocumentErrorMessage, getApiErrorMessage } from '../../utils/errorHandling';
import PdfViewer from '../Pdf/PdfViewer';

// Signer colours for visual distinction
const SIGNER_COLORS = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a', '#c62828'];

const FIELD_TYPES = [
  { type: 'SIGNATURE', label: 'Signature',  icon: <DrawIcon />,         defaultW: 20, defaultH: 5   },
  { type: 'INITIALS',  label: 'Initials',   icon: <AbcIcon />,          defaultW: 8,  defaultH: 4   },
  { type: 'DATE',      label: 'Date',       icon: <CalendarTodayIcon />, defaultW: 15, defaultH: 3.5 },
  { type: 'NAME',      label: 'Full Name',  icon: <PersonIcon />,       defaultW: 20, defaultH: 3.5 },
  { type: 'TEXT',      label: 'Text',       icon: <TextFieldsIcon />,   defaultW: 20, defaultH: 3.5 },
  { type: 'CHECKBOX',  label: 'Checkbox',   icon: <CheckBoxOutlinedIcon />, defaultW: 3,  defaultH: 1.5 },
];

// Corner resize handle positions (matches FreeSignTool/PdfViewer.js)
const HANDLES = [
  { id: 'nw', cursor: 'nw-resize', top: -5,    left: -5  },
  { id: 'ne', cursor: 'ne-resize', top: -5,    right: -5 },
  { id: 'sw', cursor: 'sw-resize', bottom: -5, left: -5  },
  { id: 'se', cursor: 'se-resize', bottom: -5, right: -5 },
];

// Minimum field size in percentage points — stops degenerate zero-size boxes
const MIN_W_PCT = 3;
const MIN_H_PCT = 1.5;

export default function PrepareDocument() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [fields, setFields] = useState([]);
  const [selectedFieldId, setSelectedFieldId] = useState(null);
  const [activeSigner, setActiveSigner] = useState(1);
  const [contextMenu, setContextMenu] = useState(null);
  const [draggingType, setDraggingType] = useState(null);
  const fieldIdCounter = useRef(0);

  useEffect(() => { loadDocument(); }, [id]); // eslint-disable-line

  const loadDocument = async () => {
    try {
      const doc = await documentService.get(id);
      setDocument(doc);
      if (doc.signature_fields && doc.signature_fields.length > 0) {
        setFields(doc.signature_fields.map((f, i) => ({ ...f, _localId: `existing-${i}` })));
        fieldIdCounter.current = doc.signature_fields.length;
      }
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'load'));
    } finally {
      setLoading(false);
    }
  };

  const addField = useCallback((fieldType, page, xPercent, yPercent) => {
    const typeInfo = FIELD_TYPES.find(f => f.type === fieldType);
    const w = typeInfo?.defaultW || 20;
    const h = typeInfo?.defaultH || 5;
    const newField = {
      _localId: `field-${fieldIdCounter.current++}`,
      field_type: fieldType,
      page,
      // Centre the box on the click point (matches free-tool behaviour)
      x_percent: Math.max(0, Math.min(xPercent - w / 2, 100 - w)),
      y_percent: Math.max(0, Math.min(yPercent - h / 2, 100 - h)),
      width_percent: w,
      height_percent: h,
      signer_index: activeSigner,
      label: '',
      required: true,
    };
    setFields(prev => [...prev, newField]);
    setSelectedFieldId(newField._localId);
  }, [activeSigner]);

  const removeField = (localId) => {
    setFields(prev => prev.filter(f => f._localId !== localId));
    if (selectedFieldId === localId) setSelectedFieldId(null);
  };

  const updateField = (localId, updates) => {
    setFields(prev => prev.map(f => f._localId === localId ? { ...f, ...updates } : f));
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      const payload = fields.map(f => ({
        field_type: f.field_type,
        page: f.page,
        x_percent: f.x_percent,
        y_percent: f.y_percent,
        width_percent: f.width_percent,
        height_percent: f.height_percent,
        signer_index: f.signer_index,
        label: f.label || '',
        required: f.required !== false,
      }));
      await documentService.saveFields(id, payload);
      setSuccess(`${fields.length} field(s) saved successfully!`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to save fields. Please try again.'));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndContinue = async () => {
    await handleSave();
    if (!error) {
      setTimeout(() => navigate(`/documents/${id}/send`), 500);
    }
  };

  const handlePageContextMenu = (pageNum, xPercent, yPercent, event) => {
    setContextMenu({ mouseX: event.clientX, mouseY: event.clientY, pageNum, xPercent, yPercent });
  };

  const handleContextMenuClose = () => setContextMenu(null);

  const handleContextMenuAdd = (fieldType) => {
    if (contextMenu) addField(fieldType, contextMenu.pageNum, contextMenu.xPercent, contextMenu.yPercent);
    setContextMenu(null);
  };

  const handleSidebarDragStart = (fieldType) => setDraggingType(fieldType);

  const handlePageClick = (pageNum, xPercent, yPercent) => {
    if (draggingType) {
      addField(draggingType, pageNum, xPercent, yPercent);
      setDraggingType(null);
    } else {
      setSelectedFieldId(null);
    }
  };

  const renderOverlay = (pageNum, pageWidth, pageHeight) => {
    const pageFields = fields.filter(f => f.page === pageNum);
    if (!pageFields.length) return null;

    return pageFields.map((field) => {
      const typeInfo = FIELD_TYPES.find(t => t.type === field.field_type);
      const color = SIGNER_COLORS[(field.signer_index - 1) % SIGNER_COLORS.length];
      const isSelected = selectedFieldId === field._localId;

      return (
        <FieldOverlay
          key={field._localId}
          field={field}
          typeInfo={typeInfo}
          color={color}
          isSelected={isSelected}
          pageWidth={pageWidth}
          pageHeight={pageHeight}
          onSelect={() => setSelectedFieldId(field._localId)}
          onDelete={() => removeField(field._localId)}
          onMove={(x_percent, y_percent) => updateField(field._localId, { x_percent, y_percent })}
          onResize={(width_percent, height_percent, x_percent, y_percent) =>
            updateField(field._localId, { width_percent, height_percent, x_percent, y_percent })
          }
        />
      );
    });
  };

  const authToken = localStorage.getItem('accessToken');
  const pdfUrl = documentService.getPdfUrl(id);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      <AppBar position="static" color="inherit" elevation={1}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/documents')} sx={{ mr: 2 }}><ArrowBackIcon /></IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Prepare Document — {document?.title}</Typography>
          <Button variant="outlined" startIcon={saving ? <CircularProgress size={18} /> : <SaveIcon />} onClick={handleSave} disabled={saving} sx={{ mr: 1 }}>Save</Button>
          <Button variant="contained" startIcon={<SendIcon />} onClick={handleSaveAndContinue} disabled={saving}>Save & Add Signers</Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
        {/* ─── Left Sidebar ─── */}
        <Paper elevation={2} sx={{ width: 240, flexShrink: 0, p: 2, overflowY: 'auto', borderRadius: 0 }}>
          <Typography variant="subtitle2" gutterBottom>Signer</Typography>
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Assign to</InputLabel>
            <Select value={activeSigner} label="Assign to" onChange={(e) => setActiveSigner(e.target.value)}>
              {[1, 2, 3, 4, 5].map(n => (
                <MenuItem key={n} value={n}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: SIGNER_COLORS[(n - 1) % SIGNER_COLORS.length] }} />
                    Signer {n}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle2" gutterBottom>
            Drag to PDF {draggingType ? '— click on PDF to place' : ''}
          </Typography>

          {FIELD_TYPES.map(({ type, label, icon }) => (
            <Tooltip key={type} title="Click then click on PDF to place" placement="right">
              <Paper
                elevation={draggingType === type ? 4 : 1}
                sx={{
                  p: 1.5, mb: 1, cursor: 'grab', display: 'flex', alignItems: 'center', gap: 1,
                  border: draggingType === type ? '2px solid #1565c0' : '1px solid #e0e0e0',
                  bgcolor: draggingType === type ? '#e3f2fd' : 'white',
                  '&:hover': { bgcolor: '#f5f5f5' }, transition: 'all 0.15s',
                }}
                onClick={() => setDraggingType(draggingType === type ? null : type)}
                onDragStart={() => handleSidebarDragStart(type)}
                draggable
              >
                <DragIndicatorIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                {icon}
                <Typography variant="body2">{label}</Typography>
              </Paper>
            </Tooltip>
          ))}

          {draggingType && (
            <Alert severity="info" sx={{ mt: 2, py: 0.5 }}>
              Click on the PDF to place the {FIELD_TYPES.find(f => f.type === draggingType)?.label} field.
              <Button size="small" onClick={() => setDraggingType(null)} sx={{ ml: 1 }}>Cancel</Button>
            </Alert>
          )}

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>Placed Fields ({fields.length})</Typography>
          {fields.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              No fields yet. Drag fields from above or right-click on the PDF.
            </Typography>
          )}
          {fields.map((field) => {
            const typeInfo = FIELD_TYPES.find(t => t.type === field.field_type);
            const color = SIGNER_COLORS[(field.signer_index - 1) % SIGNER_COLORS.length];
            return (
              <Paper
                key={field._localId}
                elevation={selectedFieldId === field._localId ? 3 : 0}
                sx={{
                  p: 1, mb: 0.5, display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer',
                  border: selectedFieldId === field._localId ? `2px solid ${color}` : '1px solid #eee',
                  bgcolor: selectedFieldId === field._localId ? '#fafafa' : 'transparent',
                }}
                onClick={() => setSelectedFieldId(field._localId)}
              >
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: color, flexShrink: 0 }} />
                <Typography variant="caption" sx={{ flexGrow: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {typeInfo?.label} · P{field.page}
                </Typography>
                <Tooltip title="Delete">
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); removeField(field._localId); }}>
                    <DeleteIcon sx={{ fontSize: 14 }} />
                  </IconButton>
                </Tooltip>
              </Paper>
            );
          })}

          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">
            Tip: Click a placed field to select it — drag to move, corner handles to resize.
            Right-click the PDF to add a field at that position.
          </Typography>
        </Paper>

        {/* ─── Main: PDF Viewer ─── */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}
          <PdfViewer pdfUrl={pdfUrl} authToken={authToken} onPageClick={handlePageClick} onPageContextMenu={handlePageContextMenu} renderOverlay={renderOverlay} />
        </Box>
      </Box>

      {/* ─── Right-click context menu ─── */}
      <Menu open={contextMenu !== null} onClose={handleContextMenuClose} anchorReference="anchorPosition"
        anchorPosition={contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}>
        <MenuItem disabled>
          <Typography variant="caption" color="text.secondary">Add field for Signer {activeSigner} (page {contextMenu?.pageNum})</Typography>
        </MenuItem>
        <Divider />
        {FIELD_TYPES.map(({ type, label, icon }) => (
          <MenuItem key={type} onClick={() => handleContextMenuAdd(type)}>
            <ListItemIcon>{icon}</ListItemIcon>
            <ListItemText>{label}</ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
}


/**
 * FieldOverlay — A single placed-field box on top of a PDF page.
 *
 * Renders an empty placeholder rectangle (no label text) that the sender
 * can drag to move and resize via 4 corner handles. When selected, a red X
 * in the top-right corner deletes the field.
 *
 * A small type icon sits in the upper-left corner so the sender still
 * knows what kind of field it is without making the box look "filled".
 */
function FieldOverlay({ field, typeInfo, color, isSelected, pageWidth, pageHeight, onSelect, onDelete, onMove, onResize }) {
  const [dragging, setDragging] = useState(false);

  // Pixel geometry for the current render size
  const left   = (field.x_percent      / 100) * pageWidth;
  const top    = (field.y_percent      / 100) * pageHeight;
  const width  = (field.width_percent  / 100) * pageWidth;
  const height = (field.height_percent / 100) * pageHeight;

  // ── Body drag: move the whole box ──────────────────────────────────────
  const handleBodyMouseDown = (e) => {
    e.stopPropagation();
    e.preventDefault();
    onSelect();
    setDragging(true);

    const startX = e.clientX;
    const startY = e.clientY;
    const origXPct = field.x_percent;
    const origYPct = field.y_percent;

    const onMouseMove = (ev) => {
      const dxPct = ((ev.clientX - startX) / pageWidth)  * 100;
      const dyPct = ((ev.clientY - startY) / pageHeight) * 100;
      const newX = Math.max(0, Math.min(origXPct + dxPct, 100 - field.width_percent));
      const newY = Math.max(0, Math.min(origYPct + dyPct, 100 - field.height_percent));
      onMove(newX, newY);
    };
    const onMouseUp = () => {
      setDragging(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  // ── Corner resize: adjust width/height and (for nw/ne/sw) x/y too ─────
  const handleResizeMouseDown = (e, handleId) => {
    e.stopPropagation();
    e.preventDefault();
    onSelect();

    const startX = e.clientX;
    const startY = e.clientY;
    const origX = field.x_percent;
    const origY = field.y_percent;
    const origW = field.width_percent;
    const origH = field.height_percent;

    const onMouseMove = (ev) => {
      const dxPct = ((ev.clientX - startX) / pageWidth)  * 100;
      const dyPct = ((ev.clientY - startY) / pageHeight) * 100;

      let newX = origX, newY = origY, newW = origW, newH = origH;

      if (handleId === 'se') {
        newW = Math.max(MIN_W_PCT, Math.min(origW + dxPct, 100 - origX));
        newH = Math.max(MIN_H_PCT, Math.min(origH + dyPct, 100 - origY));
      } else if (handleId === 'sw') {
        newW = Math.max(MIN_W_PCT, Math.min(origW - dxPct, origX + origW));
        newX = origX + (origW - newW);
        newH = Math.max(MIN_H_PCT, Math.min(origH + dyPct, 100 - origY));
      } else if (handleId === 'ne') {
        newW = Math.max(MIN_W_PCT, Math.min(origW + dxPct, 100 - origX));
        newH = Math.max(MIN_H_PCT, Math.min(origH - dyPct, origY + origH));
        newY = origY + (origH - newH);
      } else if (handleId === 'nw') {
        newW = Math.max(MIN_W_PCT, Math.min(origW - dxPct, origX + origW));
        newX = origX + (origW - newW);
        newH = Math.max(MIN_H_PCT, Math.min(origH - dyPct, origY + origH));
        newY = origY + (origH - newH);
      }

      onResize(newW, newH, newX, newY);
    };
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const TypeIcon = typeInfo?.icon
    ? React.cloneElement(typeInfo.icon, { sx: { fontSize: 12, color } })
    : null;

  return (
    <Box
      sx={{
        position: 'absolute', left, top, width, height,
        border: `2px ${isSelected ? 'solid' : 'dashed'} ${color}`,
        borderRadius: '4px',
        cursor: dragging ? 'grabbing' : 'grab',
        pointerEvents: 'auto',
        transition: dragging ? 'none' : 'box-shadow 0.15s',
        boxShadow: isSelected ? `0 0 8px ${color}55` : 'none',
        zIndex: isSelected ? 10 : 5,
        // Transparent interior so the PDF stays visible through the box.
        // A faint tint only appears on hover so placed fields remain discoverable.
        bgcolor: 'transparent',
        '&:hover': { bgcolor: `${color}14` },
      }}
      onMouseDown={handleBodyMouseDown}
    >
      {/* Small type icon in the corner — tells the sender what kind of field
          this is without making the box look filled. */}
      {TypeIcon && (
        <Box sx={{
          position: 'absolute', top: 2, left: 4,
          display: 'flex', alignItems: 'center',
          pointerEvents: 'none', userSelect: 'none',
          opacity: isSelected ? 1 : 0.7,
        }}>
          {TypeIcon}
        </Box>
      )}

      {/* Delete button on selection */}
      {isSelected && (
        <IconButton
          size="small"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          sx={{
            position: 'absolute', top: -12, right: -12,
            width: 22, height: 22,
            bgcolor: '#d32f2f', color: 'white',
            border: '1.5px solid white',
            '&:hover': { bgcolor: '#b71c1c' },
            zIndex: 20,
          }}
        >
          <CloseIcon sx={{ fontSize: 14 }} />
        </IconButton>
      )}

      {/* Corner resize handles on selection */}
      {isSelected && HANDLES.map(h => (
        <Box
          key={h.id}
          onMouseDown={(e) => handleResizeMouseDown(e, h.id)}
          sx={{
            position: 'absolute',
            ...h,
            width: 10, height: 10,
            bgcolor: 'white',
            border: `2px solid ${color}`,
            borderRadius: '50%',
            cursor: h.cursor,
            zIndex: 21,
          }}
        />
      ))}
    </Box>
  );
}
