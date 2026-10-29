/**
 * SigningPage.js — Professional full-viewport signing editor.
 *
 * Layout (mirrors DigiSigner UX):
 *   Top nav  — document title + signer info + Done button
 *   Left sidebar — tool icons (Signature, Initials, Date, Name, Text)
 *   Centre — PDF canvas with clickable field overlays
 *
 * Two modes:
 *   hasFields  — fields are pre-placed by sender, signer clicks them
 *   noFields   — free-form, signer picks a tool and clicks the PDF
 *     (handled via SignatureDialog popup)
 */
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box, Typography, Alert, CircularProgress,
  Button, Tooltip, Divider, Container, Paper, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DescriptionIcon from '@mui/icons-material/Description';
import DrawIcon from '@mui/icons-material/Draw';
import AbcIcon from '@mui/icons-material/Abc';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import PersonIcon from '@mui/icons-material/Person';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { signingService } from '../../services/api';
import useSigningLogic from '../../hooks/useSigningLogic';
import SIGNATURE_TABS from '../../utils/signatureTabs';
import PdfViewer from '../Pdf/PdfViewer';
import SigningOverlay from './SigningOverlay';
import SignatureDialog from './SignatureDialog';

const SIDEBAR_W = 88;

// Sidebar tool button
const SidebarTool = ({ icon, label, onClick, active, badge }) => (
  <Tooltip title={label} placement="right">
    <Box
      onClick={onClick}
      sx={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', gap: 0.5,
        py: 1.5, px: 1, borderRadius: 2, cursor: 'pointer', position: 'relative',
        bgcolor: active ? '#e3f2fd' : 'transparent',
        border: active ? '1.5px solid #1976d2' : '1.5px solid transparent',
        color: active ? 'primary.main' : 'text.secondary',
        '&:hover': { bgcolor: '#f5f5f5', color: 'text.primary' },
        transition: 'all 0.15s',
        minWidth: 64,
      }}
    >
      <Box sx={{ fontSize: 26, display: 'flex' }}>{icon}</Box>
      <Typography variant="caption" fontWeight={500} sx={{ fontSize: 10, lineHeight: 1 }}>
        {label}
      </Typography>
      {badge && (
        <Box sx={{
          position: 'absolute', top: 4, right: 4,
          width: 8, height: 8, borderRadius: '50%', bgcolor: 'success.main',
        }} />
      )}
    </Box>
  </Tooltip>
);

export default function SigningPage() {
  const { token } = useParams();
  const signing = useSigningLogic(token);

  const [sigDialogOpen, setSigDialogOpen] = useState(false);
  const [sigDialogFieldType, setSigDialogFieldType] = useState('SIGNATURE');

  // Text field input dialog — opens when signer clicks a TEXT field
  const [textDialogField, setTextDialogField] = useState(null);
  const [textDialogValue, setTextDialogValue] = useState('');

  const openTextDialog = (field) => {
    setTextDialogField(field);
    setTextDialogValue(signing.filledFields[field.id] || '');
  };
  const closeTextDialog = () => {
    setTextDialogField(null);
    setTextDialogValue('');
  };
  const saveTextDialog = () => {
    if (textDialogField) signing.fillField(textDialogField.id, textDialogValue.trim());
    closeTextDialog();
  };

  const handleFieldClick = (field) => {
    if (field.field_type === 'SIGNATURE' || field.field_type === 'INITIALS') {
      setSigDialogFieldType(field.field_type);
      setSigDialogOpen(true);
    } else if (field.field_type === 'CHECKBOX') {
      // Toggle directly — no dialog. 'true' ↔ 'false'; first click sets 'true'.
      const current = String(signing.filledFields[field.id] || '').toLowerCase();
      signing.fillField(field.id, current === 'true' ? 'false' : 'true');
    } else if (field.field_type === 'TEXT') {
      openTextDialog(field);
    } else if (field.field_type === 'DATE') {
      // Let signer override the auto-filled date via the same text dialog
      openTextDialog(field);
    } else if (field.field_type === 'NAME') {
      openTextDialog(field);
    }
  };

  const handleFieldClear = (field) => {
    if (field.field_type === 'SIGNATURE' || field.field_type === 'INITIALS') {
      signing.clearSignature();
    } else {
      signing.clearField(field.id);
    }
  };

  // ── Loading ──────────────────────────────────────────────────────────────
  if (signing.loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', bgcolor: '#f5f5f5' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }} color="text.secondary">Loading document…</Typography>
      </Box>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (signing.error && !signing.document) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5', display: 'flex', alignItems: 'center' }}>
        <Container maxWidth="sm">
          <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 3 }}>
            <DescriptionIcon sx={{ fontSize: 64, color: 'error.light', mb: 2 }} />
            <Typography variant="h5" gutterBottom fontWeight={700}>Unable to open document</Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>{signing.error}</Typography>
            <Typography variant="caption" color="text.disabled">
              The link may have expired or already been used.
            </Typography>
          </Paper>
        </Container>
      </Box>
    );
  }

  // ── Already signed ───────────────────────────────────────────────────────
  if (signing.signed) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5', display: 'flex', alignItems: 'center' }}>
        <Container maxWidth="sm">
          <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 3 }}>
            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" fontWeight={800} gutterBottom>You're done!</Typography>
            <Typography color="text.secondary" sx={{ mb: 1 }}>
              You have successfully signed
            </Typography>
            <Typography fontWeight={700} sx={{ mb: 3 }}>
              "{signing.document?.title}"
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              All parties will be notified. A signed copy will be sent once everyone has signed.
            </Typography>
            <Chip
              icon={<CheckCircleIcon />}
              label="Legally binding under UK law"
              color="success"
              variant="outlined"
            />
          </Paper>
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', textAlign: 'center', mt: 2 }}>
            Powered by SignSimple — Avyangah Technologies Limited
          </Typography>
        </Container>
      </Box>
    );
  }

  const pdfUrl = signingService.getPdfUrl(token);
  const hasSignature = !!signing.signatureBlob;
  const signerName = signing.signer?.signer_name || '';
  const signerEmail = signing.signer?.signer_email || '';
  const docTitle = signing.document?.title || 'Document';
  const progress = signing.sigFieldCount > 0
    ? `${signing.filledSigCount} of ${signing.sigFieldCount} fields signed`
    : hasSignature ? 'Signature ready' : 'No signature yet';

  // ── Full viewport signing editor ─────────────────────────────────────────
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* ── TOP NAV ──────────────────────────────────────────────────── */}
      <Box sx={{
        height: 56, px: 2, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        bgcolor: '#1a237e', color: 'white', boxShadow: 2,
      }}>
        {/* Left: branding + doc title */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" fontWeight={800} sx={{ letterSpacing: -0.5, cursor: 'default' }}>
            SignSimple
          </Typography>
          <Divider orientation="vertical" flexItem sx={{ bgcolor: 'rgba(255,255,255,0.2)', my: 1 }} />
          <Typography variant="body2" sx={{ opacity: 0.85, maxWidth: 300 }} noWrap>
            {docTitle}
          </Typography>
        </Box>

        {/* Centre: signer info */}
        <Typography variant="caption" sx={{ opacity: 0.7, display: { xs: 'none', sm: 'block' } }}>
          Signing as {signerName} · {signerEmail}
        </Typography>

        {/* Right: progress + Done */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" sx={{ opacity: 0.8, display: { xs: 'none', md: 'block' } }}>
            {progress}
          </Typography>
          <Button
            variant="contained"
            startIcon={signing.submitting ? <CircularProgress size={16} color="inherit" /> : <CheckCircleIcon />}
            disabled={!signing.allFieldsFilled || signing.submitting}
            onClick={signing.submitSignature}
            sx={{
              textTransform: 'none', fontWeight: 700, px: 3,
              bgcolor: signing.allFieldsFilled ? '#43a047' : 'rgba(255,255,255,0.2)',
              '&:hover': { bgcolor: '#388e3c' },
              '&.Mui-disabled': { bgcolor: 'rgba(255,255,255,0.15)', color: 'rgba(255,255,255,0.4)' },
              borderRadius: 2,
            }}
          >
            {signing.submitting ? 'Signing…' : 'Done'}
          </Button>
        </Box>
      </Box>

      {/* Error bar */}
      {signing.error && (
        <Alert severity="error" onClose={() => signing.setError('')} sx={{ borderRadius: 0, flexShrink: 0 }}>
          {signing.error}
        </Alert>
      )}

      {/* ── BODY ─────────────────────────────────────────────────────── */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── LEFT SIDEBAR ───────────────────────────────────────────── */}
        <Box sx={{
          width: SIDEBAR_W, flexShrink: 0,
          bgcolor: 'white', borderRight: '1px solid #e0e0e0',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          py: 2, gap: 0.5, overflowY: 'auto',
        }}>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: 9, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Add
          </Typography>

          <SidebarTool
            icon={<DrawIcon fontSize="inherit" />}
            label="Sign"
            badge={hasSignature}
            onClick={() => { setSigDialogFieldType('SIGNATURE'); setSigDialogOpen(true); }}
          />
          <SidebarTool
            icon={<AbcIcon fontSize="inherit" />}
            label="Initials"
            onClick={() => { setSigDialogFieldType('INITIALS'); setSigDialogOpen(true); }}
          />
          <SidebarTool
            icon={<CalendarTodayIcon fontSize="inherit" />}
            label="Date"
            onClick={() => {
              // Auto-fill all DATE fields
              signing.fields.filter(f => f.field_type === 'DATE').forEach(f => {
                signing.fillField(f.id, new Date().toLocaleDateString('en-GB'));
              });
            }}
          />
          <SidebarTool
            icon={<PersonIcon fontSize="inherit" />}
            label="Name"
            onClick={() => {
              signing.fields.filter(f => f.field_type === 'NAME').forEach(f => {
                signing.fillField(f.id, signerName);
              });
            }}
          />
          <SidebarTool
            icon={<TextFieldsIcon fontSize="inherit" />}
            label="Text"
            onClick={() => { setSigDialogFieldType('SIGNATURE'); setSigDialogOpen(true); }}
          />

          {hasSignature && (
            <SidebarTool
              icon={<DeleteOutlineIcon fontSize="inherit" />}
              label="Clear"
              onClick={() => signing.clearSignature()}
            />
          )}

          <Divider sx={{ width: '80%', my: 1 }} />

          {/* Progress indicator */}
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: 9, textAlign: 'center', px: 1 }}>
            {signing.sigFieldCount > 0 ? `${signing.filledSigCount}/${signing.sigFieldCount}` : hasSignature ? '✓' : '–'}
          </Typography>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: 9, textAlign: 'center', px: 1 }}>
            {signing.sigFieldCount > 0 ? 'fields' : 'signed'}
          </Typography>
        </Box>

        {/* ── PDF AREA ───────────────────────────────────────────────── */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Instruction bar */}
          <Box sx={{
            px: 3, py: 1, bgcolor: '#fff8e1',
            borderBottom: '1px solid #ffe082', flexShrink: 0,
            display: 'flex', alignItems: 'center', gap: 1,
          }}>
            {signing.hasFields ? (
              <Typography variant="body2" color="warning.dark" fontWeight={500}>
                📋 Click the green highlighted fields in the document to sign
              </Typography>
            ) : (
              <Typography variant="body2" color="warning.dark" fontWeight={500}>
                ✍️ Use the sidebar tools to add your signature, then click Done
              </Typography>
            )}
            {signing.allFieldsFilled && (
              <Chip label="Ready to submit" color="success" size="small" icon={<CheckCircleIcon />} sx={{ ml: 'auto' }} />
            )}
          </Box>

          {/* PDF canvas */}
          <Box sx={{ flex: 1, overflow: 'auto', bgcolor: '#525659', p: 3 }}>
            <PdfViewer
              pdfUrl={pdfUrl}
              renderOverlay={(pageNum, pageWidth, pageHeight) => (
                <SigningOverlay
                  pageNum={pageNum}
                  pageWidth={pageWidth}
                  pageHeight={pageHeight}
                  fields={signing.fields}
                  filledFields={signing.filledFields}
                  signaturePreviewUrl={signing.signaturePreviewUrl}
                  onFieldClick={handleFieldClick}
                  onFieldClear={handleFieldClear}
                />
              )}
            />
          </Box>

          {/* Bottom legal bar */}
          <Box sx={{
            px: 3, py: 1.5, bgcolor: 'white',
            borderTop: '1px solid #e0e0e0', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <Typography variant="caption" color="text.disabled">
              By clicking Done you confirm this signature is legally binding under the Electronic Communications Act 2000.
            </Typography>
            <Typography variant="caption" color="text.disabled">
              Powered by SignSimple
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Signature dialog */}
      <SignatureDialog
        open={sigDialogOpen}
        onClose={() => setSigDialogOpen(false)}
        onSave={signing.fillSignatureFields}
        signerName={signerName}
        fieldType={sigDialogFieldType}
      />

      {/* Text / Name / Date input dialog — opens when signer clicks a
          non-signature field. Uses the sender's `label` as the prompt so
          the signer knows what to type (e.g. "Company name", "Job title"). */}
      <Dialog
        open={!!textDialogField}
        onClose={closeTextDialog}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" fontWeight={700}>
            {textDialogField?.field_type === 'DATE' ? 'Enter date'
              : textDialogField?.field_type === 'NAME' ? 'Enter name'
              : 'Enter text'}
          </Typography>
          {textDialogField?.label && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {textDialogField.label}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            fullWidth
            autoFocus
            size="small"
            value={textDialogValue}
            onChange={(e) => setTextDialogValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && textDialogValue.trim()) {
                e.preventDefault();
                saveTextDialog();
              }
            }}
            placeholder={textDialogField?.label || 'Type here…'}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={closeTextDialog} color="inherit" sx={{ textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            onClick={saveTextDialog}
            variant="contained"
            disabled={!textDialogValue.trim()}
            sx={{ textTransform: 'none', fontWeight: 700 }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
