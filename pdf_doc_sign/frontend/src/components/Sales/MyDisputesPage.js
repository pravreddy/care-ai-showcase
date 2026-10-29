import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, Alert, CircularProgress,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  FormControlLabel, Checkbox,
} from '@mui/material';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { salesService } from '../../services/api';

const STATUS_COLORS = {
  OPEN: 'error',
  ACKNOWLEDGED: 'warning',
  RESOLVED: 'success',
  REJECTED: 'default',
};

export default function MyDisputesPage({ user }) {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Resolve dialog
  const [resolveOpen, setResolveOpen] = useState(false);
  const [resolveId, setResolvId] = useState(null);
  const [resolveNotes, setResolveNotes] = useState('');
  const [sendResolveEmail, setSendResolveEmail] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isClientUser = user?.is_client_user;

  useEffect(() => { loadDisputes(); }, []);

  const loadDisputes = async () => {
    setLoading(true);
    try {
      const data = await salesService.getDisputes();
      setDisputes(data.results || data || []);
    } catch {
      setError('Failed to load disputes.');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await salesService.acknowledgeDispute(id);
      setSuccess('Dispute acknowledged.');
      loadDisputes();
    } catch {
      setError('Failed to acknowledge.');
    }
  };

  const openResolveDialog = (id) => {
    setResolvId(id);
    setResolveNotes('');
    setSendResolveEmail(false);
    setResolveOpen(true);
  };

  const handleResolve = async () => {
    setSubmitting(true);
    try {
      await salesService.resolveDispute(resolveId, resolveNotes, sendResolveEmail);
      setSuccess('Dispute resolved.');
      setResolveOpen(false);
      loadDisputes();
    } catch {
      setError('Failed to resolve.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <Box sx={{ textAlign: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  const openDisputes = disputes.filter(d => d.status === 'OPEN' || d.status === 'ACKNOWLEDGED');
  const closedDisputes = disputes.filter(d => d.status === 'RESOLVED' || d.status === 'REJECTED');

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        {isClientUser ? 'My Concerns' : 'Disputes & Concerns'}
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {isClientUser
          ? 'View your raised concerns and their resolution status.'
          : 'View and resolve client concerns about deliveries.'
        }
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {disputes.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
          <Typography color="text.secondary">No concerns raised. Everything looks good!</Typography>
        </Paper>
      ) : (
        <>
          {/* Open Disputes */}
          {openDisputes.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                <ReportProblemIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'error.main' }} />
                Open ({openDisputes.length})
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Raised By</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      {!isClientUser && <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {openDisputes.map((d) => (
                      <TableRow key={d.id} sx={{ bgcolor: '#fff3e0' }}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {new Date(d.created_at).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={d.dispute_type?.replace('_', ' ')} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{d.description}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {d.raised_by_email || '—'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={d.status} size="small" color={STATUS_COLORS[d.status] || 'default'} />
                        </TableCell>
                        {!isClientUser && (
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {d.status === 'OPEN' && (
                                <Button size="small" color="warning" variant="outlined"
                                  onClick={() => handleAcknowledge(d.id)}>
                                  Acknowledge
                                </Button>
                              )}
                              <Button size="small" color="success" variant="outlined"
                                onClick={() => openResolveDialog(d.id)}>
                                Resolve
                              </Button>
                            </Box>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Closed Disputes */}
          {closedDisputes.length > 0 && (
            <Box>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                <CheckCircleIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'success.main' }} />
                Resolved ({closedDisputes.length})
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Resolution</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Resolved At</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {closedDisputes.map((d) => (
                      <TableRow key={d.id}>
                        <TableCell>{new Date(d.created_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Chip label={d.dispute_type?.replace('_', ' ')} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{d.description}</TableCell>
                        <TableCell>
                          <Typography variant="body2" color="success.main">
                            {d.resolution_notes || 'Resolved'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {d.resolved_at ? new Date(d.resolved_at).toLocaleDateString() : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </>
      )}

      {/* Resolve Dialog */}
      <Dialog open={resolveOpen} onClose={() => setResolveOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Resolve Concern</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth multiline rows={3}
            label="Resolution notes"
            placeholder="e.g. Credit applied for next delivery, item will be replaced..."
            value={resolveNotes}
            onChange={(e) => setResolveNotes(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <FormControlLabel
            control={<Checkbox checked={sendResolveEmail} onChange={(e) => setSendResolveEmail(e.target.checked)} />}
            label={
              <Typography variant="body2" color="text.secondary">
                Also send email notification to the client
              </Typography>
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleResolve} disabled={submitting}>
            {submitting ? <CircularProgress size={20} /> : 'Mark Resolved'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
