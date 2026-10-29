/**
 * CouponAdminPage.js — Superuser coupon management.
 * 
 * Features:
 *   - Grant free access to any user (superuser only)
 *   - Generate coupon codes for leads
 *   - View all coupons with status
 *   - Deactivate coupons
 * 
 * Only visible if user.is_superuser === true.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Button,
  Alert, CircularProgress, IconButton, Tooltip, Stack,
  TextField, Select, MenuItem, FormControl, InputLabel,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Tabs, Tab, Slider, Divider,
} from '@mui/material';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import BlockIcon from '@mui/icons-material/Block';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { couponService } from '../../services/api';

const STATUS_COLORS = {
  ACTIVE: 'success', REDEEMED: 'info', EXPIRED: 'warning', DEACTIVATED: 'error',
};
const SOURCE_COLORS = {
  CHATBOT: 'secondary', ADMIN: 'primary', SALES: 'info', REFERRAL: 'warning',
};

const DURATION_OPTIONS = [
  { value: 90, label: '3 months' },
  { value: 180, label: '6 months' },
  { value: 365, label: '1 year' },
];

export default function CouponAdminPage({ user }) {
  const [tab, setTab] = useState(0);
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Grant Free form
  const [grantEmail, setGrantEmail] = useState('');
  const [grantDocs, setGrantDocs] = useState(100);
  const [grantScans, setGrantScans] = useState(100);
  const [grantDuration, setGrantDuration] = useState(90);
  const [grantPlan, setGrantPlan] = useState('STARTER');
  const [grantNote, setGrantNote] = useState('');
  const [granting, setGranting] = useState(false);

  // Generate Coupon form
  const [genFirstName, setGenFirstName] = useState('');
  const [genLastName, setGenLastName] = useState('');
  const [genEmail, setGenEmail] = useState('');
  const [genCompany, setGenCompany] = useState('');
  const [genPlan, setGenPlan] = useState('STARTER');
  const [genDuration, setGenDuration] = useState(180);
  const [genDocs, setGenDocs] = useState(100);
  const [genScans, setGenScans] = useState(100);
  const [generating, setGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await couponService.list();
      setCoupons(data.results || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load coupons');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!user?.is_superuser && !user?.is_platform_admin) {
    return <Alert severity="error">Access denied. Platform administrators only.</Alert>;
  }

  // --- Grant Free Access ---
  const handleGrantFree = async () => {
    if (!grantEmail) { setError('Email is required'); return; }
    setGranting(true);
    setError('');
    try {
      const res = await couponService.grantFree({
        email: grantEmail,
        documents: grantDocs,
        ai_scans: grantScans,
        duration_days: grantDuration,
        plan: grantPlan,
        description: grantNote,
      });
      setSuccess(`Granted ${grantPlan} to ${grantEmail} — ${res.coupon_code} valid until ${res.valid_until}`);
      setGrantEmail(''); setGrantNote('');
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to grant access');
    } finally {
      setGranting(false);
    }
  };

  // --- Generate Coupon ---
  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setGeneratedCode('');
    try {
      const res = await couponService.generate({
        first_name: genFirstName,
        last_name: genLastName,
        email: genEmail,
        company: genCompany,
        plan: genPlan,  // already 'STARTER' or 'PROFESSIONAL'
        duration_days: Number(genDuration),
        documents_included: Number(genDocs),
        ai_scans_included: Number(genScans),
        price_gbp: 1.00,
        source: 'ADMIN',
      });
      setGeneratedCode(res.code);
      setSuccess(`Coupon generated: ${res.code}`);
      setGenFirstName(''); setGenLastName(''); setGenEmail(''); setGenCompany('');
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate coupon');
    } finally {
      setGenerating(false);
    }
  };

  // --- Deactivate ---
  const handleDeactivate = async (coupon) => {
    if (!window.confirm(`Deactivate coupon ${coupon.code}?`)) return;
    try {
      await couponService.deactivate(coupon.id);
      setSuccess(`Deactivated: ${coupon.code}`);
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to deactivate');
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setSuccess(`Copied: ${code}`);
  };

  const activeCoupons = coupons.filter(c => c.status === 'ACTIVE');
  const redeemedCoupons = coupons.filter(c => c.status === 'REDEEMED');

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <CardGiftcardIcon sx={{ fontSize: 36, color: 'primary.main' }} />
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={800}>Coupons & Access</Typography>
          <Typography variant="body2" color="text.secondary">
            Generate coupons, grant free access to users
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={load}><RefreshIcon /></IconButton>
        </Tooltip>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Stats */}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Total Coupons', value: coupons.length, color: 'primary.main' },
          { label: 'Active', value: activeCoupons.length, color: 'success.main' },
          { label: 'Redeemed', value: redeemedCoupons.length, color: 'info.main' },
        ].map(s => (
          <Paper key={s.label} sx={{ p: 2, flex: 1, textAlign: 'center', borderRadius: 3 }}>
            <Typography variant="h4" fontWeight={800} sx={{ color: s.color }}>{s.value}</Typography>
            <Typography variant="caption" color="text.secondary">{s.label}</Typography>
          </Paper>
        ))}
      </Stack>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab icon={<PersonAddIcon />} label="Grant Free Access" iconPosition="start" />
        <Tab icon={<CardGiftcardIcon />} label="Generate Coupon" iconPosition="start" />
        <Tab label={`All Coupons (${coupons.length})`} />
      </Tabs>

      {/* ─── Tab 0: Grant Free Access (superuser only) ─── */}
      {tab === 0 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight={700} gutterBottom>
            Grant Free Access to a User
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Instantly upgrades a user's plan. No coupon code needed — they get access immediately.
          </Typography>

          <Stack spacing={2}>
            <TextField
              label="User Email" fullWidth required
              value={grantEmail} onChange={(e) => setGrantEmail(e.target.value)}
              placeholder="sarah@sparkclean.co.uk"
            />

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Plan</InputLabel>
                <Select value={grantPlan} onChange={(e) => setGrantPlan(e.target.value)} label="Plan">
                  <MenuItem value="STARTER">Starter</MenuItem>
                  <MenuItem value="PROFESSIONAL">Professional</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Duration</InputLabel>
                <Select value={grantDuration} onChange={(e) => setGrantDuration(e.target.value)} label="Duration">
                  {DURATION_OPTIONS.map(d => (
                    <MenuItem key={d.value} value={d.value}>{d.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Documents: {grantDocs}
                </Typography>
                <Slider
                  value={grantDocs} onChange={(_, v) => setGrantDocs(v)}
                  min={10} max={1000} step={10}
                  marks={[{ value: 10, label: '10' }, { value: 100, label: '100' }, { value: 500, label: '500' }, { value: 1000, label: '1000' }]}
                />
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  AI Scans: {grantScans}
                </Typography>
                <Slider
                  value={grantScans} onChange={(_, v) => setGrantScans(v)}
                  min={0} max={500} step={10}
                  marks={[{ value: 0, label: '0' }, { value: 100, label: '100' }, { value: 500, label: '500' }]}
                />
              </Box>
            </Stack>

            <TextField
              label="Internal Note (optional)" fullWidth multiline rows={2}
              value={grantNote} onChange={(e) => setGrantNote(e.target.value)}
              placeholder="e.g. Demo for NHS trust, free trial for event"
            />

            <Button
              variant="contained" size="large" onClick={handleGrantFree}
              disabled={granting || !grantEmail}
              startIcon={granting ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            >
              {granting ? 'Granting...' : `Grant ${grantPlan} Access`}
            </Button>
          </Stack>
        </Paper>
      )}

      {/* ─── Tab 1: Generate Coupon Code ─── */}
      {tab === 1 && (
        <Paper sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" fontWeight={700} gutterBottom>
            Generate Coupon Code
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Creates a unique code the user enters at signup. Code expires in 7 days. £1 to activate.
          </Typography>

          <Stack spacing={2}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField label="First Name" fullWidth value={genFirstName} onChange={(e) => setGenFirstName(e.target.value)} />
              <TextField label="Last Name" fullWidth value={genLastName} onChange={(e) => setGenLastName(e.target.value)} />
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField label="Email" fullWidth value={genEmail} onChange={(e) => setGenEmail(e.target.value)} />
              <TextField label="Company (optional)" fullWidth value={genCompany} onChange={(e) => setGenCompany(e.target.value)} />
            </Stack>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Plan</InputLabel>
                <Select value={genPlan} onChange={(e) => setGenPlan(e.target.value)} label="Plan">
                  <MenuItem value="STARTER">Starter (100 docs + 100 scans)</MenuItem>
                  <MenuItem value="PROFESSIONAL">Professional (1000 docs + 500 scans)</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Duration</InputLabel>
                <Select value={genDuration} onChange={(e) => setGenDuration(e.target.value)} label="Duration">
                  {DURATION_OPTIONS.map(d => (
                    <MenuItem key={d.value} value={d.value}>{d.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            <Button
              variant="contained" size="large" onClick={handleGenerate}
              disabled={generating}
              startIcon={generating ? <CircularProgress size={20} /> : <CardGiftcardIcon />}
            >
              {generating ? 'Generating...' : 'Generate Coupon Code'}
            </Button>

            {generatedCode && (
              <Alert
                severity="success"
                action={
                  <IconButton size="small" onClick={() => copyCode(generatedCode)}>
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                }
              >
                <Typography variant="body2">
                  Coupon code: <strong>{generatedCode}</strong>
                </Typography>
                <Typography variant="caption">
                  Share this with the user. Valid for 7 days. £1 to activate.
                </Typography>
              </Alert>
            )}
          </Stack>
        </Paper>
      )}

      {/* ─── Tab 2: All Coupons Table ─── */}
      {tab === 2 && (
        <Paper sx={{ borderRadius: 3 }}>
          <Box sx={{ p: 2 }}>
            {loading ? (
              <Box sx={{ textAlign: 'center', py: 6 }}><CircularProgress /></Box>
            ) : coupons.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <Typography color="text.secondary">No coupons generated yet.</Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Code</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>For</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Plan</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Duration</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Docs</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Scans</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Source</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {coupons.map((c) => (
                      <TableRow key={c.id} hover>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={0.5}>
                            <Typography variant="body2" fontWeight={700} sx={{ fontFamily: 'monospace' }}>
                              {c.code}
                            </Typography>
                            <IconButton size="small" onClick={() => copyCode(c.code)}>
                              <ContentCopyIcon sx={{ fontSize: 14 }} />
                            </IconButton>
                          </Stack>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {c.lead_first_name} {c.lead_last_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {c.lead_email}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={c.plan_granted} size="small" color="info" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {c.duration_days <= 90 ? '3 months' : c.duration_days <= 180 ? '6 months' : '1 year'}
                          </Typography>
                        </TableCell>
                        <TableCell>{c.documents_included}</TableCell>
                        <TableCell>{c.ai_scans_included}</TableCell>
                        <TableCell>
                          <Chip label={c.source} size="small" variant="outlined"
                            color={SOURCE_COLORS[c.source] || 'default'} />
                        </TableCell>
                        <TableCell>
                          <Chip label={c.status} size="small"
                            color={STATUS_COLORS[c.status] || 'default'} />
                        </TableCell>
                        <TableCell>
                          {c.status === 'ACTIVE' && (
                            <Tooltip title="Deactivate">
                              <IconButton size="small" color="error" onClick={() => handleDeactivate(c)}>
                                <BlockIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  );
}
