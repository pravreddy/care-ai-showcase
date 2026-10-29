import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, TextField, Button, IconButton, Grid,
  Alert, CircularProgress, Chip, List, ListItem, Avatar, Stepper, 
  Step, StepLabel, Container, AppBar, Toolbar, Switch, FormControlLabel,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import DescriptionIcon from '@mui/icons-material/Description';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EmailIcon from '@mui/icons-material/Email';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { documentService } from '../../services/api';
import { getDocumentErrorMessage, getApiErrorMessage } from '../../utils/errorHandling';

// Must match the signer colours used in PrepareDocument so position #N here
// visually lines up with the "Signer N" fields placed on the PDF.
const SIGNER_COLORS = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a', '#c62828'];

export default function SendForSigning() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [fieldCount, setFieldCount] = useState(0);
  const [signers, setSigners] = useState([{ name: '', email: '' }]);
  const [sequential, setSequential] = useState(false);

  useEffect(() => { loadDocument(); }, [id]); // eslint-disable-line

  const loadDocument = async () => {
    try {
      const doc = await documentService.get(id);
      setDocument(doc);
      setFieldCount(doc.signature_fields?.length || 0);
      if (doc.signers && doc.signers.length > 0) {
        setSigners(doc.signers.map(s => ({ name: s.signer_name, email: s.signer_email })));
      }
      setSequential(!!doc.sequential_signing);
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'load'));
    } finally {
      setLoading(false);
    }
  };

  const addSigner = () => setSigners([...signers, { name: '', email: '' }]);
  const removeSigner = (index) => { if (signers.length > 1) setSigners(signers.filter((_, i) => i !== index)); };
  const updateSigner = (index, field, value) => { const updated = [...signers]; updated[index][field] = value; setSigners(updated); };
  const moveSigner = (index, dir) => {
    const target = index + dir;
    if (target < 0 || target >= signers.length) return;
    const updated = [...signers];
    [updated[index], updated[target]] = [updated[target], updated[index]];
    setSigners(updated);
  };

  const validateSigners = () => {
    for (const signer of signers) {
      if (!signer.name.trim()) return 'All signers must have a name';
      if (!signer.email.trim()) return 'All signers must have an email';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signer.email)) return `Invalid email: ${signer.email}`;
    }
    return null;
  };

  const handleSend = async () => {
    const validationError = validateSigners();
    if (validationError) { setError(validationError); return; }

    setSending(true);
    setError('');

    try {
      const result = await documentService.sendForSigning(id, signers, sequential);
      if (result.emails_failed > 0) {
        setSuccess(
          `Document sent to ${signers.length} signer(s). ${result.emails_sent} email(s) sent successfully. ` +
          `${result.emails_failed} email(s) failed — signers can still use the direct link from the document details page.`
        );
      } else {
        setSuccess(`Document sent for signing! ${result.emails_sent} signer(s) will receive an email with a link to sign.`);
      }
      setTimeout(() => navigate('/documents'), 3000);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to send document. Please try again.'));
    } finally {
      setSending(false);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}><CircularProgress /></Box>;

  if (!document) return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Alert severity="error">Document not found</Alert>
      <Button sx={{ mt: 2 }} onClick={() => navigate('/documents')}>Back to Documents</Button>
    </Container>
  );

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      <AppBar position="static" color="inherit" elevation={1}>
        <Toolbar>
          <IconButton edge="start" onClick={() => navigate('/documents')} sx={{ mr: 2 }}><ArrowBackIcon /></IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Send for Signing</Typography>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={() => navigate(`/documents/${id}/prepare`)} sx={{ mr: 1 }}>Edit Fields</Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 3 }} icon={<CheckCircleIcon />}>{success}</Alert>}

        <Stepper activeStep={2} sx={{ mb: 4 }}>
          <Step completed><StepLabel>Upload PDF</StepLabel></Step>
          <Step completed><StepLabel>Place Fields</StepLabel></Step>
          <Step><StepLabel>Add Signers</StepLabel></Step>
          <Step><StepLabel>Send</StepLabel></Step>
        </Stepper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}><DescriptionIcon /></Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6">{document.title}</Typography>
              <Typography variant="body2" color="text.secondary">
                {document.file_size_mb} MB · {document.page_count || '?'} page(s) · Uploaded {new Date(document.created_at).toLocaleDateString()}
              </Typography>
              {fieldCount > 0 && <Chip label={`${fieldCount} field(s) placed`} size="small" color="success" variant="outlined" sx={{ mt: 0.5 }} />}
            </Box>
            <Chip label={document.status} color={document.status === 'DRAFT' ? 'default' : document.status === 'PENDING' ? 'warning' : 'success'} />
          </Box>
        </Paper>

        {fieldCount === 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No signature fields have been placed on this document. Signers will sign at the bottom of the last page.
            <Button size="small" sx={{ ml: 1 }} onClick={() => navigate(`/documents/${id}/prepare`)}>Place Fields Now</Button>
          </Alert>
        )}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}><EmailIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Who needs to sign?</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>Add the email addresses of people who need to sign this document.</Typography>
          <Alert severity="info" sx={{ mb: 3, py: 0.5 }}>
            The coloured number is each signer's position. Fields you placed for “Signer 1” go to
            position #1, “Signer 2” to #2, and so on — use the ↑ ↓ arrows to reorder.
          </Alert>

          <List>
            {signers.map((signer, index) => (
              <ListItem key={index} sx={{ px: 0, py: 1 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={1}>
                    <Chip
                      label={`#${index + 1}`}
                      size="small"
                      sx={{ bgcolor: SIGNER_COLORS[index % SIGNER_COLORS.length], color: 'white', fontWeight: 700 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField fullWidth size="small" label={`Signer ${index + 1} Name`} value={signer.name} onChange={(e) => updateSigner(index, 'name', e.target.value)} placeholder="John Smith" />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField fullWidth size="small" type="email" label={`Signer ${index + 1} Email`} value={signer.email} onChange={(e) => updateSigner(index, 'email', e.target.value)} placeholder="john@example.com" />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton size="small" disabled={index === 0} onClick={() => moveSigner(index, -1)} title="Move up"><ArrowUpwardIcon fontSize="small" /></IconButton>
                      <IconButton size="small" disabled={index === signers.length - 1} onClick={() => moveSigner(index, 1)} title="Move down"><ArrowDownwardIcon fontSize="small" /></IconButton>
                      {signers.length > 1 && <IconButton color="error" size="small" onClick={() => removeSigner(index)} title="Remove"><DeleteIcon fontSize="small" /></IconButton>}
                    </Box>
                  </Grid>
                </Grid>
              </ListItem>
            ))}
          </List>
          <Button startIcon={<AddIcon />} onClick={addSigner} sx={{ mt: 2 }}>Add Another Signer</Button>

          <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #eee' }}>
            <FormControlLabel
              control={<Switch checked={sequential} onChange={(e) => setSequential(e.target.checked)} />}
              label={
                <Box>
                  <Typography variant="body2" fontWeight={600}>Sign in order (one at a time)</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Only #1 is emailed first; each next signer is invited automatically once the
                    previous one signs. Leave off to email everyone at once.
                  </Typography>
                </Box>
              }
            />
          </Box>
        </Paper>

        <Box sx={{ textAlign: 'center' }}>
          <Button variant="contained" size="large" startIcon={sending ? <CircularProgress size={20} color="inherit" /> : <SendIcon />} onClick={handleSend} disabled={sending || signers.every(s => !s.email.trim())} sx={{ px: 6, py: 1.5 }}>
            {sending ? 'Sending...' : `Send to ${signers.filter(s => s.email.trim()).length} Signer(s)`}
          </Button>
        </Box>

        <Paper sx={{ p: 3, mt: 4, bgcolor: '#fafafa' }}>
          <Typography variant="subtitle2" gutterBottom>What happens next?</Typography>
          <Typography variant="body2" color="text.secondary">
            1. Each signer receives an email with a secure link · 2. They click the link to view and sign the document · 3. You get notified when each person signs · 4. Once everyone has signed, you can download the completed document
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
}
