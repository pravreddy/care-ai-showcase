/**
 * FreeSignTool — Thin orchestrator. Wires hooks → child components.
 * Route: /free-electronic-signature
 *
 * Hooks: usePdfLoader, useSigningItems, useDownload
 * Helpers: signatureHelpers (pure functions)
 * Children: FileUploadArea, PdfViewer, SignatureDialog, TextDialog
 */
import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Container, Typography, Button, Paper,
  Stack, Chip, Alert,
} from '@mui/material';
import DrawIcon from '@mui/icons-material/Draw';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import ShieldIcon from '@mui/icons-material/Shield';
import SpeedIcon from '@mui/icons-material/Speed';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import FileUploadArea from './FileUploadArea';
import PdfViewer from './PdfViewer';
import SignatureDialog from './SignatureDialog';
import TextDialog from './TextDialog';
import SEO from '../Common/SEO';
import { DEFAULT_FONT, DEFAULT_COLOR, DEFAULT_SIG_SIZE } from './freeSignConfig';
import { CHECKMARK_DATA_URL, generateTypedSignature, generateTextDataUrl, stripWhiteBackground } from './signatureHelpers';
import usePdfLoader from './usePdfLoader';
import useSigningItems from './useSigningItems';
import useDownload from './useDownload';

export default function FreeSignTool() {
  const navigate = useNavigate();
  const sigCanvasRef = useRef(null);

  // ── Hooks ────────────────────────────────────────────────────────────
  const pdf = usePdfLoader();
  const [sigSize, setSigSize] = useState(DEFAULT_SIG_SIZE);
  const signing = useSigningItems(pdf.canvasRef, pdf.currentPage, sigSize);
  const dl = useDownload(pdf.pdfBytes, signing.items, pdf.canvasRef, pdf.fileName, pdf.setError);

  // ── Signature dialog state ───────────────────────────────────────────
  const [signerName, setSignerName] = useState('');
  const [sigColor, setSigColor] = useState(DEFAULT_COLOR);
  const [selectedFont, setSelectedFont] = useState(DEFAULT_FONT);
  const [sigDialogOpen, setSigDialogOpen] = useState(false);
  const [sigTab, setSigTab] = useState(0);
  const [typedText, setTypedText] = useState('');
  const [sigImageUrl, setSigImageUrl] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [initialsDialogOpen, setInitialsDialogOpen] = useState(false);
  const [textDialogOpen, setTextDialogOpen] = useState(false);
  const [textDialogMode, setTextDialogMode] = useState('text');

  // ── Dialog handlers ──────────────────────────────────────────────────
  const handleSigUpload = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        // Chroma-key out the white background so scanned/photographed
        // signatures don't embed as an off-white rectangle over PDF content.
        const transparentUrl = await stripWhiteBackground(reader.result);
        setSigImageUrl(transparentUrl);
      } catch {
        // Fall back to the raw upload if chroma-key fails for any reason
        setSigImageUrl(reader.result);
      }
    };
    reader.readAsDataURL(f);
  };

  const openSignatureDialog = (isInitials = false) => {
    if (isInitials) {
      const initials = signerName.trim()
        ? signerName.trim().split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 3)
        : '';
      if (initials && !typedText) { setTypedText(initials); setSigTab(1); }
      setInitialsDialogOpen(true);
    } else {
      if (signerName.trim() && !typedText) { setTypedText(signerName.trim()); setSigTab(1); }
      setSigDialogOpen(true);
    }
  };

  const confirmSignature = (isInitials = false) => {
    let dataUrl = null;
    if (sigTab === 0 && sigCanvasRef.current) {
      dataUrl = sigCanvasRef.current.toDataURL('image/png');
    } else if (sigTab === 1) {
      dataUrl = generateTypedSignature(typedText, selectedFont, sigColor);
    } else if (sigTab === 2) {
      dataUrl = sigImageUrl;
    }
    if (!dataUrl) { pdf.setError('Please create a signature first.'); return; }
    signing.setPlacing({ type: isInitials ? 'initials' : 'signature', dataUrl });
    setSigDialogOpen(false);
    setInitialsDialogOpen(false);
    setTypedText('');
    setSigImageUrl(null);
  };

  const confirmText = (text, fontSize, color) => {
    const dataUrl = generateTextDataUrl(text, fontSize, color, textDialogMode);
    signing.setPlacing({ type: textDialogMode, dataUrl });
    setTextDialogOpen(false);
  };

  const addCheckmark = () => signing.setPlacing({ type: 'checkmark', dataUrl: CHECKMARK_DATA_URL });

  // ── File select (resets items + download) ────────────────────────────
  const handleFileSelect = async (file) => {
    signing.clearItems();
    dl.resetDownload();
    await pdf.handleFileSelect(file);
  };

  // ── Clear everything ─────────────────────────────────────────────────
  const handleClear = () => {
    pdf.clearPdf();
    signing.clearItems();
    dl.resetDownload();
  };

  // ── SEO (Helmet — renders in <head> regardless of view state) ────────
  const seoTag = (
    <SEO
      title="Free Electronic Signature Tool – Sign PDFs Online"
      description="Sign PDF documents online free. Draw, type or upload your signature. No account needed. Supports PDF, DOC, DOCX, JPG and PNG. UK-based, GDPR compliant."
      path="/free-electronic-signature"
      keywords="free electronic signature, sign PDF online free, e-signature tool free, free document signing UK"
    />
  );

  // ─────────────────────────────────────────────────────────────────────
  // CONVERTING STATE
  // ─────────────────────────────────────────────────────────────────────
  if (pdf.converting) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: '#f8f9fa' }}>
        {seoTag}
        <Typography variant="h5" fontWeight={700} gutterBottom>Converting your file…</Typography>
        <Typography variant="body1" color="text.secondary">Please wait a moment</Typography>
      </Box>
    );
  }

  // ─────────────────────────────────────────────────────────────────────
  // SUCCESS PAGE
  // ─────────────────────────────────────────────────────────────────────
  if (dl.downloadDone) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#f8f9fa' }}>
        {seoTag}
        <Box sx={{ px: 3, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e0e0e0', bgcolor: 'white' }}>
          <Typography variant="h6" fontWeight={800} color="primary" sx={{ cursor: 'pointer' }} onClick={() => navigate('/')}>SignSimple</Typography>
          <Stack direction="row" spacing={1}>
            <Button variant="text" onClick={() => navigate('/login')} sx={{ textTransform: 'none' }}>Sign In</Button>
            <Button variant="contained" onClick={() => navigate('/register')} sx={{ textTransform: 'none', fontWeight: 700 }}>Start Free</Button>
          </Stack>
        </Box>
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
          <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
          <Typography variant="h4" fontWeight={800} gutterBottom>Successfully Completed!</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Your signed PDF has been saved to your device.</Typography>
          {dl.signedBlobUrl && (
            <Button variant="contained" size="large" startIcon={<DownloadIcon />}
              component="a" href={dl.signedBlobUrl} download={`signed_${pdf.fileName || 'document.pdf'}`}
              sx={{ fontWeight: 700, px: 5, py: 1.5, fontSize: 16, mb: 2, textTransform: 'none', borderRadius: 3 }}>
              Download Document
            </Button>
          )}
          <Button variant="outlined" size="large" onClick={handleClear}
            sx={{ fontWeight: 600, px: 4, textTransform: 'none', borderRadius: 3, mb: 5 }}>
            Sign Another Document
          </Button>
          <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#1a237e', borderRadius: 3, maxWidth: 480, width: '100%' }}>
            <Typography variant="h6" fontWeight={700} color="white" gutterBottom>Need to send for others to sign?</Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.75)', mb: 3 }}>
              Create a free account — invite signers by email, track status, get audit trails.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/register')}
              sx={{ textTransform: 'none', fontWeight: 700, px: 4, bgcolor: '#43a047', '&:hover': { bgcolor: '#388e3c' } }}>
              Create Free Account
            </Button>
          </Paper>
        </Box>
      </Box>
    );
  }

  // ─────────────────────────────────────────────────────────────────────
  // EDITOR MODE
  // ─────────────────────────────────────────────────────────────────────
  if (pdf.pdfDoc) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {seoTag}
        <Box sx={{ height: 56, px: 2, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', bgcolor: '#1a237e', color: 'white', boxShadow: 2 }}>
          <Typography variant="h6" fontWeight={800} sx={{ cursor: 'pointer', letterSpacing: -0.5 }} onClick={handleClear}>SignSimple</Typography>
          <Typography variant="caption" sx={{ opacity: 0.7 }}>{pdf.fileName}</Typography>
          <Stack direction="row" spacing={1}>
            <Button variant="text" onClick={() => navigate('/login')} sx={{ textTransform: 'none', color: 'rgba(255,255,255,0.8)', fontSize: 13 }}>Sign In</Button>
            <Button variant="contained" onClick={() => navigate('/register')} sx={{ textTransform: 'none', fontWeight: 700, bgcolor: '#43a047', '&:hover': { bgcolor: '#388e3c' }, fontSize: 13 }}>Start Free</Button>
          </Stack>
        </Box>
        {pdf.error && <Alert severity="error" onClose={() => pdf.setError('')} sx={{ borderRadius: 0 }}>{pdf.error}</Alert>}
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <PdfViewer
            canvasRef={pdf.canvasRef}
            currentPage={pdf.currentPage} totalPages={pdf.totalPages}
            onPageChange={pdf.goToPage}
            onCanvasClick={signing.handleCanvasClick}
            placingSignature={signing.placing?.type ?? null}
            onAddSig={() => openSignatureDialog(false)}
            onAddInitials={() => openSignatureDialog(true)}
            onAddText={() => { setTextDialogMode('text'); setTextDialogOpen(true); }}
            onAddDate={() => { setTextDialogMode('date'); setTextDialogOpen(true); }}
            onAddCheckmark={addCheckmark}
            onUndo={signing.undoItem}
            onDownload={dl.downloadSignedPdf}
            onClear={handleClear}
            hasItems={signing.items.length > 0}
            downloading={dl.downloading}
            signerName={signerName}
            onSignerNameChange={setSignerName}
            sigSize={sigSize}
            onSigSizeChange={setSigSize}
            overlayItems={signing.currentPageItems}
            selectedItemId={signing.selectedItemId}
            onSelectItem={signing.setSelectedItemId}
            onDeleteItem={signing.deleteItem}
            onMoveItem={signing.moveItem}
            onResizeItem={signing.resizeItem}
          />
        </Box>
        <SignatureDialog
          open={sigDialogOpen || initialsDialogOpen}
          onClose={() => { setSigDialogOpen(false); setInitialsDialogOpen(false); }}
          onConfirm={() => confirmSignature(initialsDialogOpen)}
          sigCanvasRef={sigCanvasRef}
          sigTab={sigTab} setSigTab={setSigTab}
          typedText={typedText} setTypedText={setTypedText}
          sigImageUrl={sigImageUrl} onSigUpload={handleSigUpload}
          isDrawing={isDrawing} setIsDrawing={setIsDrawing}
          sigColor={sigColor} setSigColor={setSigColor}
          selectedFont={selectedFont} setSelectedFont={setSelectedFont}
        />
        <TextDialog
          open={textDialogOpen}
          onClose={() => setTextDialogOpen(false)}
          onConfirm={confirmText}
          mode={textDialogMode}
        />
      </Box>
    );
  }

  // ─────────────────────────────────────────────────────────────────────
  // UPLOAD MODE
  // ─────────────────────────────────────────────────────────────────────
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {seoTag}
      <Box sx={{ px: 3, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e0e0e0', bgcolor: 'white' }}>
        <Typography variant="h6" fontWeight={800} color="primary" sx={{ cursor: 'pointer', letterSpacing: -0.5 }} onClick={() => navigate('/')}>SignSimple</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="text" onClick={() => navigate('/login')} sx={{ textTransform: 'none' }}>Sign In</Button>
          <Button variant="contained" onClick={() => navigate('/register')} sx={{ textTransform: 'none', fontWeight: 700 }}>Start Free</Button>
        </Stack>
      </Box>
      <Box sx={{ py: { xs: 5, md: 7 }, textAlign: 'center', bgcolor: '#f8f9fa' }}>
        <Container maxWidth="sm">
          <Typography variant="h3" fontWeight={800} gutterBottom sx={{ letterSpacing: -1 }}>Sign Documents Online</Typography>
          <Typography variant="h6" color="text.secondary" fontWeight={400} sx={{ mb: 4 }}>Free, fast and secure. No account needed.</Typography>
          <Stack direction="row" spacing={2} justifyContent="center" flexWrap="wrap">
            <Chip icon={<ShieldIcon />} label="Legally binding in UK" color="default" variant="outlined" size="small" />
            <Chip icon={<SpeedIcon />} label="Ready in seconds" color="default" variant="outlined" size="small" />
          </Stack>
        </Container>
      </Box>
      <Container maxWidth="md" sx={{ py: 4, flex: 1 }}>
        {pdf.error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => pdf.setError('')}>{pdf.error}</Alert>}
        <FileUploadArea onFileSelect={handleFileSelect} />
        <Box sx={{ mt: 8 }}>
          <Typography variant="h5" fontWeight={700} align="center" gutterBottom>How It Works</Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mt: 3 }}>
            {[
              { icon: <UploadFileIcon sx={{ fontSize: 32 }} />, step: '1', title: 'Upload your file', desc: 'PDF, Word, JPG or PNG — up to 20MB' },
              { icon: <DrawIcon sx={{ fontSize: 32 }} />, step: '2', title: 'Sign & annotate', desc: 'Draw, type or upload your signature' },
              { icon: <DownloadIcon sx={{ fontSize: 32 }} />, step: '3', title: 'Download', desc: 'Get your signed PDF instantly' },
            ].map(s => (
              <Paper key={s.step} elevation={0} sx={{ p: 3, textAlign: 'center', flex: 1, border: '1px solid #e0e0e0', borderRadius: 3 }}>
                <Box sx={{ color: 'primary.main', mb: 1.5 }}>{s.icon}</Box>
                <Chip label={`Step ${s.step}`} size="small" sx={{ mb: 1.5, bgcolor: '#e8eaf6', color: 'primary.dark', fontWeight: 700 }} />
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>{s.title}</Typography>
                <Typography variant="body2" color="text.secondary">{s.desc}</Typography>
              </Paper>
            ))}
          </Stack>
        </Box>
        <Paper sx={{ mt: 6, p: 4, textAlign: 'center', bgcolor: '#1a237e', borderRadius: 3 }}>
          <Typography variant="h6" fontWeight={700} color="white" gutterBottom>Need to send documents for others to sign?</Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
            Create a free account — 10 documents per month, email notifications, audit trails and more.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/register')}
            sx={{ textTransform: 'none', fontWeight: 700, px: 4, bgcolor: '#43a047', '&:hover': { bgcolor: '#388e3c' } }}>
            Create Free Account
          </Button>
        </Paper>
      </Container>
      <Box sx={{ py: 3, textAlign: 'center', bgcolor: '#1a1a2e', color: 'white', mt: 4 }}>
        <Typography variant="body2" sx={{ opacity: 0.6 }}>© {new Date().getFullYear()} Avyangah Technologies Limited · UK Company #08235853</Typography>
        <Typography variant="caption" sx={{ opacity: 0.4 }}>Electronic signatures are legally binding under UK law (Electronic Communications Act 2000)</Typography>
      </Box>
    </Box>
  );
}
