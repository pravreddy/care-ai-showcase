/**
 * PlatformAdminPage.js — Superuser-only panel.
 * Replaces Django admin for the most common tasks:
 *   - Enable / disable sales access per org
 *   - Change org plan / status
 *   - See all orgs with their industry + request notes
 *
 * Only renders if user.is_superuser === true (also checked server-side).
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Button,
  Alert, CircularProgress, IconButton, Tooltip, Stack,
  TextField, Select, MenuItem, FormControl, InputLabel,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Tabs, Tab, Badge,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BlockIcon from '@mui/icons-material/Block';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditIcon from '@mui/icons-material/Edit';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import { platformAdminService } from '../../services/api';

const PLAN_COLORS   = { FREE: 'default', STARTER: 'info', PROFESSIONAL: 'success', ENTERPRISE: 'warning' };
const STATUS_COLORS = { ACTIVE: 'success', TRIAL: 'info', SUSPENDED: 'error', CANCELLED: 'default' };

export default function PlatformAdminPage({ user }) {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState(0);

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editOrg, setEditOrg] = useState(null);
  const [editPlan, setEditPlan] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await platformAdminService.getOrgs();
      setOrgs(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load organisations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!user?.is_superuser && !user?.is_platform_admin) {
    return <Alert severity="error">Access denied. Platform administrators only.</Alert>;
  }

  const handleEnableSales = async (org) => {
    try {
      const res = await platformAdminService.enableSales(org.id);
      setSuccess(res.message);
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed');
    }
  };

  const handleDisableSales = async (org) => {
    if (!window.confirm(`Disable sales access for "${org.name}"?`)) return;
    try {
      const res = await platformAdminService.disableSales(org.id);
      setSuccess(res.message);
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed');
    }
  };

  const openEdit = (org) => {
    setEditOrg(org);
    setEditPlan(org.plan);
    setEditStatus(org.status);
    setEditOpen(true);
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      if (editPlan !== editOrg.plan) {
        await platformAdminService.setPlan(editOrg.id, editPlan);
      }
      if (editStatus !== editOrg.status) {
        await platformAdminService.setStatus(editOrg.id, editStatus);
      }
      setSuccess(`${editOrg.name} updated.`);
      setEditOpen(false);
      load();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  // Filter by search
  const filtered = orgs.filter(o =>
    !search ||
    o.name.toLowerCase().includes(search.toLowerCase()) ||
    o.email?.toLowerCase().includes(search.toLowerCase()) ||
    o.domain?.toLowerCase().includes(search.toLowerCase()) ||
    o.owner_email?.toLowerCase().includes(search.toLowerCase())
  );

  const salesRequests = filtered.filter(o => !o.sales_access_enabled && o.industry);
  const salesEnabled  = filtered.filter(o => o.sales_access_enabled);

  const tabOrgs = tab === 0 ? filtered : tab === 1 ? salesRequests : salesEnabled;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <AdminPanelSettingsIcon sx={{ fontSize: 36, color: 'primary.main' }} />
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={800}>Platform Admin</Typography>
          <Typography variant="body2" color="text.secondary">
            Enable sales access, change plans and org status without using Django admin
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <TextField
            size="small" placeholder="Search…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            sx={{ width: 220 }}
          />
          <Tooltip title="Refresh">
            <IconButton onClick={load}><RefreshIcon /></IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Stats */}
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Total Orgs',     value: orgs.length,                                       color: 'primary.main' },
          { label: 'Sales Requests', value: orgs.filter(o => !o.sales_access_enabled && o.industry).length, color: 'warning.main' },
          { label: 'Sales Enabled',  value: orgs.filter(o => o.sales_access_enabled).length,   color: 'success.main' },
          { label: 'Active',         value: orgs.filter(o => o.status === 'ACTIVE').length,    color: 'info.main' },
        ].map(s => (
          <Paper key={s.label} sx={{ p: 2, flex: 1, textAlign: 'center', borderRadius: 3 }}>
            <Typography variant="h4" fontWeight={800} sx={{ color: s.color }}>{s.value}</Typography>
            <Typography variant="caption" color="text.secondary">{s.label}</Typography>
          </Paper>
        ))}
      </Stack>

      <Paper sx={{ borderRadius: 3 }}>
        <Box sx={{ borderBottom: '1px solid #e0e0e0' }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 2 }}>
            <Tab label={`All (${filtered.length})`} />
            <Tab
              label={
                <Badge badgeContent={salesRequests.length} color="warning" max={99}>
                  <Box sx={{ pr: salesRequests.length ? 2 : 0 }}>Sales Requests</Box>
                </Badge>
              }
            />
            <Tab label={`Sales Enabled (${salesEnabled.length})`} />
          </Tabs>
        </Box>

        <Box sx={{ p: 2 }}>
          {loading ? (
            <Box sx={{ textAlign: 'center', py: 6 }}><CircularProgress /></Box>
          ) : tabOrgs.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography color="text.secondary">
                {tab === 1 ? 'No pending sales access requests — all clear!' : 'No organisations found.'}
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>Organisation</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Owner</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Industry / Use case</TableCell>
                    <TableCell sx={{ fontWeight: 700 }} align="center">Members</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Plan</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Sales</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tabOrgs.map((org) => (
                    <TableRow
                      key={org.id}
                      hover
                      sx={{
                        bgcolor: !org.sales_access_enabled && org.industry
                          ? '#fff8e1'
                          : 'inherit',
                      }}
                    >
                      {/* Org name */}
                      <TableCell>
                        <Typography variant="body2" fontWeight={700}>{org.name}</Typography>
                        <Typography variant="caption" color="text.secondary">{org.domain}</Typography>
                      </TableCell>

                      {/* Owner */}
                      <TableCell>
                        <Typography variant="body2">{org.owner_email || '—'}</Typography>
                      </TableCell>

                      {/* Industry */}
                      <TableCell sx={{ maxWidth: 200 }}>
                        {org.industry_display ? (
                          <Box>
                            <Chip label={org.industry_display} size="small" color="primary" variant="outlined" />
                            {org.sales_access_notes && (
                              <Tooltip title={org.sales_access_notes} arrow>
                                <Typography
                                  variant="caption" color="text.secondary"
                                  sx={{ display: 'block', mt: 0.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                >
                                  {org.sales_access_notes}
                                </Typography>
                              </Tooltip>
                            )}
                          </Box>
                        ) : (
                          <Typography variant="caption" color="text.disabled">—</Typography>
                        )}
                      </TableCell>

                      {/* Members */}
                      <TableCell align="center">
                        <Typography variant="body2">{org.member_count}</Typography>
                      </TableCell>

                      {/* Plan */}
                      <TableCell>
                        <Chip label={org.plan} size="small" color={PLAN_COLORS[org.plan] || 'default'} />
                      </TableCell>

                      {/* Status */}
                      <TableCell>
                        <Chip label={org.status} size="small" color={STATUS_COLORS[org.status] || 'default'} />
                      </TableCell>

                      {/* Sales */}
                      <TableCell>
                        {org.sales_access_enabled ? (
                          <Chip icon={<CheckCircleIcon />} label="Enabled" size="small" color="success" />
                        ) : org.industry ? (
                          <Chip label="Requested" size="small" color="warning" variant="outlined" />
                        ) : (
                          <Typography variant="caption" color="text.disabled">—</Typography>
                        )}
                      </TableCell>

                      {/* Actions */}
                      <TableCell>
                        <Stack direction="row" spacing={0.5} alignItems="center">
                          {!org.sales_access_enabled ? (
                            <Tooltip title={
                              org.industry
                                ? `Enable sales for ${org.name} (${org.industry_display}) — will send them an email`
                                : `Enable sales for ${org.name} — will send them an email`
                            }>
                              <Button
                                size="small"
                                variant="contained"
                                color="success"
                                startIcon={<PointOfSaleIcon />}
                                onClick={() => handleEnableSales(org)}
                                sx={{ textTransform: 'none', fontSize: 12, whiteSpace: 'nowrap' }}
                              >
                                Enable Sales
                              </Button>
                            </Tooltip>
                          ) : (
                            <Tooltip title="Disable sales access">
                              <IconButton size="small" color="error" onClick={() => handleDisableSales(org)}>
                                <BlockIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          {/* Plan/status edit — superuser only */}
                          {user?.is_superuser && (
                            <Tooltip title="Edit plan / status (superuser only)">
                              <IconButton size="small" onClick={() => openEdit(org)}>
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </Paper>

      {/* Edit plan/status dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit — {editOrg?.name}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Plan</InputLabel>
            <Select value={editPlan} onChange={(e) => setEditPlan(e.target.value)} label="Plan">
              <MenuItem value="FREE">Free</MenuItem>
              <MenuItem value="STARTER">Starter</MenuItem>
              <MenuItem value="PROFESSIONAL">Professional</MenuItem>
              <MenuItem value="ENTERPRISE">Enterprise</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Status</InputLabel>
            <Select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} label="Status">
              <MenuItem value="ACTIVE">Active</MenuItem>
              <MenuItem value="TRIAL">Trial</MenuItem>
              <MenuItem value="SUSPENDED">Suspended</MenuItem>
              <MenuItem value="CANCELLED">Cancelled</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setEditOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit} disabled={saving}>
            {saving ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
