import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, IconButton, Tooltip, Alert,
  CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  FormControlLabel, Checkbox,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PendingIcon from '@mui/icons-material/Pending';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import { salesService } from '../../services/api';

const DISPUTE_TYPES = [
  { value: 'MISSING_ITEM', label: 'Item Missing' },
  { value: 'WRONG_ITEM', label: 'Wrong Item Delivered' },
  { value: 'QUALITY', label: 'Quality Issue' },
  { value: 'QUANTITY', label: 'Quantity Mismatch' },
  { value: 'OVERCHARGE', label: 'Overcharged' },
  { value: 'OTHER', label: 'Other' },
];

export default function MyDeliveriesPage({ user }) {
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Dispute dialog
  const [disputeOpen, setDisputeOpen] = useState(false);
  const [disputeSaleId, setDisputeSaleId] = useState(null);
  const [disputeType, setDisputeType] = useState('MISSING_ITEM');
  const [disputeDescription, setDisputeDescription] = useState('');
  const [sendDisputeEmail, setSendDisputeEmail] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { loadDeliveries(); }, []);

  const loadDeliveries = async () => {
    setLoading(true);
    try {
      // Client user sees their own deliveries via the sales API
      const now = new Date();
      const fromDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
      const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
      const toDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${lastDay}`;
      const data = await salesService.getDailySales({ from_date: fromDate, to_date: toDate });
      setDeliveries(data.results || data || []);
    } catch {
      setError('Failed to load deliveries.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmInApp = async (saleId) => {
    try {
      // Use the send_confirmation endpoint but we'll add in-app confirm later
      // For now, mark as confirmed via the API
      await salesService.confirmDeliveryInApp(saleId);
      setSuccess('Delivery confirmed!');
      loadDeliveries();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to confirm.');
    }
  };

  const openDisputeDialog = (saleId) => {
    setDisputeSaleId(saleId);
    setDisputeType('MISSING_ITEM');
    setDisputeDescription('');
    setSendDisputeEmail(false);
    setDisputeOpen(true);
  };

  const handleSubmitDispute = async () => {
    if (!disputeDescription.trim()) {
      setError('Please describe the issue.');
      return;
    }
    setSubmitting(true);
    try {
      await salesService.createDispute({
        daily_sale: disputeSaleId,
        dispute_type: disputeType,
        description: disputeDescription,
        send_email: sendDisputeEmail,
      });
      setSuccess('Concern raised successfully. The provider will be notified.');
      setDisputeOpen(false);
      loadDeliveries();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to raise concern.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatItems = (itemsDesc) => {
    if (!itemsDesc) return '—';
    try {
      const items = JSON.parse(itemsDesc);
      if (Array.isArray(items)) {
        return items.map(i => `${i.quantity}x ${i.item_name}`).join(', ');
      }
    } catch { /* fall through */ }
    return itemsDesc.slice(0, 60);
  };

  if (loading) {
    return <Box sx={{ textAlign: 'center', py: 6 }}><CircularProgress /></Box>;
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        My Deliveries
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        View your deliveries this month. Confirm receipt or raise a concern if something isn't right.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {deliveries.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <LocalShippingIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          <Typography color="text.secondary">No deliveries recorded this month.</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Day</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Items</TableCell>
                {!user?.is_client_user && (
                  <TableCell sx={{ fontWeight: 700 }} align="right">Total</TableCell>
                )}
                <TableCell sx={{ fontWeight: 700 }} align="center">Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {deliveries.map((d) => (
                <TableRow
                  key={d.id}
                  sx={{ bgcolor: d.is_holiday ? '#fff3e0' : d.client_confirmed ? '#f1f8e9' : 'inherit' }}
                >
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {new Date(d.date + 'T00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                    </Typography>
                  </TableCell>
                  <TableCell>{d.day_name?.slice(0, 3)}</TableCell>
                  <TableCell>
                    {d.is_holiday ? (
                      <Typography variant="body2" color="text.secondary"><em>{d.holiday_reason || 'Holiday'}</em></Typography>
                    ) : (
                      <Typography variant="body2">{formatItems(d.items_description)}</Typography>
                    )}
                  </TableCell>
                  {!user?.is_client_user && (
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>
                        {d.is_holiday ? '—' : `Rs.${parseFloat(d.total_charge || 0).toLocaleString()}`}
                      </Typography>
                    </TableCell>
                  )}
                  <TableCell align="center">
                    {d.is_holiday ? (
                      <Chip label="Holiday" size="small" color="warning" variant="outlined" />
                    ) : d.client_confirmed ? (
                      <Tooltip title={`Confirmed ${d.client_confirmed_at ? new Date(d.client_confirmed_at).toLocaleString() : ''}`}>
                        <Chip icon={<CheckCircleIcon />} label="Confirmed" size="small" color="success" />
                      </Tooltip>
                    ) : d.has_dispute ? (
                      <Chip icon={<ReportProblemIcon />} label="Disputed" size="small" color="error" />
                    ) : (
                      <Chip icon={<PendingIcon />} label="Pending" size="small" color="default" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {!d.is_holiday && !d.client_confirmed && (
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                        <Button size="small" color="success" variant="outlined"
                          onClick={() => handleConfirmInApp(d.id)}>
                          Confirm
                        </Button>
                        <Button size="small" color="error" variant="outlined"
                          onClick={() => openDisputeDialog(d.id)}>
                          Issue
                        </Button>
                      </Box>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dispute Dialog */}
      <Dialog open={disputeOpen} onClose={() => setDisputeOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <ReportProblemIcon sx={{ mr: 1, verticalAlign: 'middle', color: 'error.main' }} />
          Raise a Concern
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Issue Type</InputLabel>
            <Select value={disputeType} onChange={(e) => setDisputeType(e.target.value)} label="Issue Type">
              {DISPUTE_TYPES.map((t) => (
                <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="Describe the issue"
            placeholder="e.g. Missing 2 Chapathi, received cold food, quantity was less than ordered..."
            value={disputeDescription}
            onChange={(e) => setDisputeDescription(e.target.value)}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={<Checkbox checked={sendDisputeEmail} onChange={(e) => setSendDisputeEmail(e.target.checked)} />}
            label={
              <Typography variant="body2" color="text.secondary">
                Also send email notification to the provider
              </Typography>
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDisputeOpen(false)}>Cancel</Button>
          <Button
            variant="contained" color="error"
            onClick={handleSubmitDispute}
            disabled={submitting || !disputeDescription.trim()}
          >
            {submitting ? <CircularProgress size={20} /> : 'Submit Concern'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
