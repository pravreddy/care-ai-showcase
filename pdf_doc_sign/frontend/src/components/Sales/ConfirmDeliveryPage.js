/**
 * ConfirmDeliveryPage — Public page for clients to confirm/dispute a delivery.
 * No login required. Accessed via token link in email.
 *
 * Two actions:
 *   Confirm  — client confirms delivery received (optionally with a note)
 *   Issue    — client raises a dispute without needing to log in
 *
 * Price visibility is controlled by the admin at send time via show_prices flag.
 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box, Container, Paper, Typography, Button, TextField, Alert,
  CircularProgress, Divider, Chip, Stack,
  FormControl, InputLabel, Select, MenuItem,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import { confirmationService } from '../../services/api';

const DISPUTE_TYPES = [
  { value: 'MISSING_ITEM', label: 'Item Missing' },
  { value: 'WRONG_ITEM', label: 'Wrong Item Delivered' },
  { value: 'QUALITY', label: 'Quality Issue' },
  { value: 'QUANTITY', label: 'Quantity Mismatch' },
  { value: 'OVERCHARGE', label: 'Overcharged' },
  { value: 'OTHER', label: 'Other' },
];

export default function ConfirmDeliveryPage() {
  const { token } = useParams();
  const [delivery, setDelivery] = useState(null);
  const [alreadyConfirmed, setAlreadyConfirmed] = useState(false);
  const [confirmedAt, setConfirmedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Confirm flow
  const [confirming, setConfirming] = useState(false);
  const [confirmNote, setConfirmNote] = useState('');
  const [confirmSuccess, setConfirmSuccess] = useState('');

  // Dispute flow
  const [showDisputeForm, setShowDisputeForm] = useState(false);
  const [disputeType, setDisputeType] = useState('MISSING_ITEM');
  const [disputeDescription, setDisputeDescription] = useState('');
  const [submittingDispute, setSubmittingDispute] = useState(false);
  const [disputeSuccess, setDisputeSuccess] = useState('');
  const [disputeError, setDisputeError] = useState('');

  // Auto-open dispute form if link has #dispute hash (from "Report Issue" email button)
  useEffect(() => {
    if (window.location.hash === '#dispute') setShowDisputeForm(true);
  }, []);

  useEffect(() => { loadDelivery(); }, [token]); // eslint-disable-line

  const loadDelivery = async () => {
    try {
      const data = await confirmationService.getDelivery(token);
      setDelivery(data.delivery);
      setAlreadyConfirmed(data.already_confirmed);
      if (data.confirmed_at) setConfirmedAt(data.confirmed_at);
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid or expired confirmation link.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError('');
    try {
      const result = await confirmationService.confirm(token, confirmNote);
      setConfirmSuccess(result.message);
      setAlreadyConfirmed(true);
      setConfirmedAt(result.confirmed_at);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to confirm delivery.');
    } finally {
      setConfirming(false);
    }
  };

  const handleDispute = async () => {
    if (!disputeDescription.trim()) {
      setDisputeError('Please describe the issue.');
      return;
    }
    setSubmittingDispute(true);
    setDisputeError('');
    try {
      await confirmationService.raiseDispute(token, disputeType, disputeDescription);
      setDisputeSuccess('Your concern has been raised. The provider will be notified and will get back to you.');
      setShowDisputeForm(false);
    } catch (err) {
      setDisputeError(err.response?.data?.error || 'Failed to raise concern. Please try again.');
    } finally {
      setSubmittingDispute(false);
    }
  };

  // ── Loading ──────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // ── Invalid link ─────────────────────────────────────────────────────────
  if (error && !delivery) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5', display: 'flex', alignItems: 'center' }}>
        <Container maxWidth="sm">
          <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
            <Typography variant="h5" color="error" gutterBottom fontWeight={700}>Link Invalid</Typography>
            <Typography color="text.secondary">{error}</Typography>
          </Paper>
        </Container>
      </Box>
    );
  }

  // ── Already confirmed ────────────────────────────────────────────────────
  if (alreadyConfirmed && !disputeSuccess) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#e8f5e9', display: 'flex', alignItems: 'center' }}>
        <Container maxWidth="sm">
          <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 3 }}>
            <CheckCircleIcon sx={{ fontSize: 72, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" fontWeight={800} gutterBottom>
              {confirmSuccess || 'Delivery Confirmed'}
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 1 }}>
              {delivery?.org_name} — {delivery?.date} ({delivery?.day_name})
            </Typography>
            {confirmedAt && (
              <Typography variant="body2" color="text.secondary">
                Confirmed at: {new Date(confirmedAt).toLocaleString()}
              </Typography>
            )}
            <Divider sx={{ my: 3 }} />
            <Typography variant="body2" color="text.secondary">
              Thank you for confirming. You can close this page.
            </Typography>
            <Typography variant="caption" color="text.disabled" sx={{ mt: 2, display: 'block' }}>
              Powered by SignSimple — signsimple.co.uk
            </Typography>
          </Paper>
        </Container>
      </Box>
    );
  }

  // ── Dispute submitted ────────────────────────────────────────────────────
  if (disputeSuccess) {
    return (
      <Box sx={{ minHeight: '100vh', bgcolor: '#fff8e1', display: 'flex', alignItems: 'center' }}>
        <Container maxWidth="sm">
          <Paper sx={{ p: 5, textAlign: 'center', borderRadius: 3 }}>
            <ReportProblemIcon sx={{ fontSize: 72, color: 'warning.main', mb: 2 }} />
            <Typography variant="h4" fontWeight={800} gutterBottom>
              Concern Raised
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              {disputeSuccess}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You can close this page.
            </Typography>
            <Typography variant="caption" color="text.disabled" sx={{ mt: 2, display: 'block' }}>
              Powered by SignSimple — signsimple.co.uk
            </Typography>
          </Paper>
        </Container>
      </Box>
    );
  }

  // ── Main page ────────────────────────────────────────────────────────────
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ py: 2, px: 3, borderRadius: 0 }}>
        <Container maxWidth="sm">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" fontWeight={800} color="primary">SignSimple</Typography>
            <Chip label="Delivery Confirmation" size="small" color="info" />
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="sm" sx={{ py: 4 }}>
        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        {/* Delivery details card */}
        <Paper sx={{ p: 3, mb: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <LocalShippingIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6" fontWeight={700}>{delivery?.org_name}</Typography>
              <Typography variant="body2" color="text.secondary">
                Delivery to {delivery?.client_name}
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">Date</Typography>
            <Typography variant="body2" fontWeight={600}>
              {delivery?.date} ({delivery?.day_name})
            </Typography>
          </Box>

          {/* Items — always shown */}
          {delivery?.items && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>Items</Typography>
              <Typography variant="body2">{delivery.items}</Typography>
            </Box>
          )}

          {delivery?.num_people > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">People</Typography>
              <Typography variant="body2">{delivery.num_people}</Typography>
            </Box>
          )}

          {/* Price info — only shown if admin chose to include it */}
          {delivery?.show_prices && (
            <>
              <Divider sx={{ my: 2 }} />
              {delivery.show_breakdown ? (
                <>
                  {delivery.food_total > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">Food</Typography>
                      <Typography variant="body2">Rs.{delivery.food_total?.toLocaleString()}</Typography>
                    </Box>
                  )}
                  {delivery.packing > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">Packing</Typography>
                      <Typography variant="body2">Rs.{delivery.packing?.toLocaleString()}</Typography>
                    </Box>
                  )}
                  {delivery.courier > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">Courier</Typography>
                      <Typography variant="body2">Rs.{delivery.courier?.toLocaleString()}</Typography>
                    </Box>
                  )}
                  <Divider sx={{ my: 1 }} />
                </>
              ) : null}
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="subtitle1" fontWeight={700}>Total</Typography>
                <Typography variant="subtitle1" fontWeight={700}>
                  Rs.{delivery.total?.toLocaleString()}
                </Typography>
              </Box>
            </>
          )}
        </Paper>

        {/* Action area */}
        {!showDisputeForm ? (
          <Paper sx={{ p: 3, borderRadius: 3 }}>
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              Did you receive this delivery?
            </Typography>

            {/* Confirm note */}
            <TextField
              fullWidth multiline rows={2}
              placeholder="Optional note e.g. All received, missing 1 item..."
              value={confirmNote}
              onChange={(e) => setConfirmNote(e.target.value)}
              variant="outlined" size="small"
              sx={{ mb: 2 }}
            />

            <Stack spacing={1.5}>
              <Button
                fullWidth variant="contained" size="large" color="success"
                startIcon={confirming ? <CircularProgress size={20} color="inherit" /> : <CheckCircleIcon />}
                onClick={handleConfirm}
                disabled={confirming}
                sx={{ py: 1.5, fontSize: '1rem', fontWeight: 700, borderRadius: 2 }}
              >
                {confirming ? 'Confirming…' : '✓  Yes, I received this delivery'}
              </Button>

              <Button
                fullWidth variant="outlined" size="large" color="warning"
                startIcon={<ReportProblemIcon />}
                onClick={() => setShowDisputeForm(true)}
                sx={{ py: 1.2, fontSize: '0.95rem', borderRadius: 2 }}
              >
                There's an issue with this delivery
              </Button>
            </Stack>
          </Paper>
        ) : (
          /* Dispute form */
          <Paper sx={{ p: 3, borderRadius: 3, border: '1.5px solid #ff9800' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ReportProblemIcon color="warning" />
              <Typography variant="subtitle1" fontWeight={700}>Raise a Concern</Typography>
            </Box>

            {disputeError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setDisputeError('')}>
                {disputeError}
              </Alert>
            )}

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>What went wrong?</InputLabel>
              <Select
                value={disputeType}
                onChange={(e) => setDisputeType(e.target.value)}
                label="What went wrong?"
              >
                {DISPUTE_TYPES.map((t) => (
                  <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth multiline rows={3}
              label="Describe the issue"
              placeholder="e.g. Missing 2 Chapathi, received cold food, wrong items delivered..."
              value={disputeDescription}
              onChange={(e) => setDisputeDescription(e.target.value)}
              sx={{ mb: 2 }}
            />

            <Stack direction="row" spacing={1.5}>
              <Button
                variant="text" color="inherit" onClick={() => setShowDisputeForm(false)}
                sx={{ flex: 1 }}
              >
                Back
              </Button>
              <Button
                variant="contained" color="warning" size="large"
                onClick={handleDispute}
                disabled={submittingDispute || !disputeDescription.trim()}
                startIcon={submittingDispute ? <CircularProgress size={18} color="inherit" /> : <ReportProblemIcon />}
                sx={{ flex: 2, fontWeight: 700, borderRadius: 2 }}
              >
                {submittingDispute ? 'Submitting…' : 'Submit Concern'}
              </Button>
            </Stack>
          </Paper>
        )}

        <Typography variant="caption" color="text.disabled" sx={{ mt: 3, display: 'block', textAlign: 'center' }}>
          Powered by SignSimple — Avyangah Technologies Limited
        </Typography>
      </Container>
    </Box>
  );
}
