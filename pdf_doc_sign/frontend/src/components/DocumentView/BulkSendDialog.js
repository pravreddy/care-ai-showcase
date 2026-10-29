import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Typography, Alert, CircularProgress, Box,
} from '@mui/material';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import { documentService } from '../../services/api';

/**
 * Dialog for bulk sending a document to multiple recipients.
 * User enters name,email pairs — one per line (CSV-style).
 */
export default function BulkSendDialog({ open, onClose, documentId, documentTitle }) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const parseRecipients = () => {
    return input
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => {
        const parts = line.split(',').map((s) => s.trim());
        if (parts.length >= 2) {
          return { name: parts[0], email: parts[1] };
        }
        // Just an email
        return { name: parts[0].split('@')[0], email: parts[0] };
      })
      .filter((r) => r.email.includes('@'));
  };

  const handleSend = async () => {
    const recipients = parseRecipients();
    if (recipients.length === 0) {
      setError('No valid recipients found. Use format: Name, email@example.com');
      return;
    }

    setSending(true);
    setError('');
    setResult(null);

    try {
      const res = await documentService.bulkSend(documentId, recipients);
      setResult(res);
    } catch (err) {
      setError(err.response?.data?.error || 'Bulk send failed.');
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    setInput('');
    setResult(null);
    setError('');
    onClose();
  };

  const recipientCount = parseRecipients().length;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <GroupAddIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Bulk Send — {documentTitle}
      </DialogTitle>
      <DialogContent>
        {!result ? (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Enter one recipient per line. Format: <strong>Name, email@example.com</strong>
              <br />Or just the email address.
            </Typography>

            <TextField
              multiline
              rows={8}
              fullWidth
              placeholder={"John Smith, john@example.com\nJane Doe, jane@example.com\nbob@company.com"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={sending}
              variant="outlined"
              sx={{ fontFamily: 'monospace' }}
            />

            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {recipientCount} valid recipient{recipientCount !== 1 ? 's' : ''} detected
            </Typography>

            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </>
        ) : (
          <Box sx={{ py: 2 }}>
            <Alert severity={result.emails_failed > 0 ? 'warning' : 'success'} sx={{ mb: 2 }}>
              {result.message}
            </Alert>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Sent: {result.emails_sent} · Failed: {result.emails_failed} · Total: {result.total}
            </Typography>
            {result.results?.filter((r) => !r.sent).length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="error">Failed recipients:</Typography>
                {result.results.filter((r) => !r.sent).map((r, i) => (
                  <Typography key={i} variant="caption" display="block" color="text.secondary">
                    {r.email}: {r.error || 'Email failed'}
                  </Typography>
                ))}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{result ? 'Close' : 'Cancel'}</Button>
        {!result && (
          <Button
            variant="contained"
            onClick={handleSend}
            disabled={sending || recipientCount === 0}
            startIcon={sending ? <CircularProgress size={18} /> : <GroupAddIcon />}
          >
            {sending ? 'Sending...' : `Send to ${recipientCount} Recipient${recipientCount !== 1 ? 's' : ''}`}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
