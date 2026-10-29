/**
 * OrganisationPage.js — Full org admin panel.
 * Tabs: Overview | Members | Branches | Settings | Sales Access
 *
 * Permissions:
 *   All members   — can view Overview + Members list
 *   MANAGER+      — can add members / invite
 *   ADMIN/OWNER   — full edit, remove members, branches, settings
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Paper, Typography, Button, Grid, Card, CardContent,
  Alert, CircularProgress, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Chip, IconButton, Tooltip, Avatar,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  MenuItem, Select, FormControl, InputLabel, Stack, Tab, Tabs,
  Divider, LinearProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import GroupIcon from '@mui/icons-material/Group';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import BusinessIcon from '@mui/icons-material/Business';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import EmailIcon from '@mui/icons-material/Email';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import SettingsIcon from '@mui/icons-material/Settings';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import CloseIcon from '@mui/icons-material/Close';
import { organisationService } from '../../services/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const ROLE_COLORS = { OWNER: 'error', ADMIN: 'primary', MANAGER: 'warning', MEMBER: 'default', VIEWER: 'info' };
const ROLES = ['ADMIN', 'MANAGER', 'MEMBER', 'VIEWER'];

function TabPanel({ value, index, children }) {
  return value === index ? <Box sx={{ pt: 3 }}>{children}</Box> : null;
}

// ─── Main Component ────────────────────────────────────────────────────────────
export default function OrganisationPage({ user }) {
  const [loading, setLoading] = useState(true);
  const [orgs, setOrgs] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(null);
  const [orgDetail, setOrgDetail] = useState(null);
  const [members, setMembers] = useState([]);
  const [branches, setBranches] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [tab, setTab] = useState(0);

  // Requests state
  const [requests, setRequests] = useState([]);

  // Alerts
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Add member dialog
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [addMemberForm, setAddMemberForm] = useState({ email: '', full_name: '', role: 'MEMBER', method: 'send_email' });
  const [addMemberResult, setAddMemberResult] = useState(null);
  const [addingMember, setAddingMember] = useState(false);

  // Edit member dialog
  const [editMemberOpen, setEditMemberOpen] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [editMemberRole, setEditMemberRole] = useState('MEMBER');
  const [editMemberBranch, setEditMemberBranch] = useState('');

  // Remove member confirm
  const [removeConfirmOpen, setRemoveConfirmOpen] = useState(false);
  const [removingMember, setRemovingMember] = useState(null);

  // Invite dialog
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');
  const [inviting, setInviting] = useState(false);

  // Branch dialog
  const [branchDialogOpen, setBranchDialogOpen] = useState(false);
  const [branchForm, setBranchForm] = useState({ name: '', code: '', city: '', address: '', postcode: '', phone: '' });
  const [editingBranchId, setEditingBranchId] = useState(null);
  const [savingBranch, setSavingBranch] = useState(false);

  // Settings edit
  const [editingSettings, setEditingSettings] = useState(false);
  const [settingsForm, setSettingsForm] = useState({});
  const [savingSettings, setSavingSettings] = useState(false);

  // Sales access request
  const [requestingSales, setRequestingSales] = useState(false);
  const [salesIndustry, setSalesIndustry] = useState('');
  const [salesNotes, setSalesNotes] = useState('');
  const [salesRequested, setSalesRequested] = useState(false);

  const INDUSTRIES = [
    { value: 'CATERING',    label: 'Catering & Food Delivery' },
    { value: 'HEALTHCARE',  label: 'Home Healthcare & Nursing' },
    { value: 'WASTE',       label: 'Waste Management & Skip Hire' },
    { value: 'PLANT_HIRE',  label: 'Equipment & Plant Hire' },
    { value: 'LOGISTICS',   label: 'Logistics & Courier' },
    { value: 'CLEANING',    label: 'Cleaning Services' },
    { value: 'CONSTRUCTION',label: 'Construction & Trades' },
    { value: 'RETAIL',      label: 'Retail & Wholesale' },
    { value: 'OTHER',       label: 'Other' },
  ];

  // Create org dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ organisation_name: '', organisation_domain: '', work_email: '', company_number: '' });
  const [creating, setCreating] = useState(false);

  // ── Data loading ────────────────────────────────────────────────────────────
  const loadOrgs = useCallback(async () => {
    setLoading(true);
    try {
      const [orgsRes, reqsRes] = await Promise.all([
        organisationService.getMyOrganisations(),
        organisationService.getMyRequests(),
      ]);
      const orgList = orgsRes.data || [];
      setOrgs(orgList);
      setRequests(reqsRes.data || []);
      if (orgList.length > 0 && !selectedOrgId) {
        setSelectedOrgId(orgList[0].organisation_id);
      }
    } catch {
      setError('Failed to load organisations');
    } finally {
      setLoading(false);
    }
  }, [selectedOrgId]);

  const loadOrgData = useCallback(async (orgId) => {
    if (!orgId) return;
    try {
      const [detail, memberList, branchList, inviteList] = await Promise.all([
        organisationService.getDetail(orgId),
        organisationService.getMembers(orgId),
        organisationService.getBranches(orgId),
        organisationService.getInvitations(orgId).then(r => r.data || []).catch(() => []),
      ]);
      setOrgDetail(detail);
      setMembers(memberList);
      setBranches(branchList);
      setInvitations(inviteList);
      setSettingsForm({
        name: detail.name || '',
        email: detail.email || '',
        phone: detail.phone || '',
        website: detail.website || '',
        address: detail.address || '',
        city: detail.city || '',
        postcode: detail.postcode || '',
        country: detail.country || '',
        company_number: detail.company_number || '',
        vat_number: detail.vat_number || '',
        primary_colour: detail.primary_colour || '#1565c0',
      });
    } catch {
      setError('Failed to load organisation data');
    }
  }, []);

  useEffect(() => { loadOrgs(); }, []);
  useEffect(() => { if (selectedOrgId) loadOrgData(selectedOrgId); }, [selectedOrgId]);

  const refresh = () => loadOrgData(selectedOrgId);

  const myOrg = orgs.find(o => o.organisation_id === selectedOrgId);
  const canAdmin = orgDetail?.can_admin || false;
  const canManage = orgDetail?.can_manage || false;

  // ── Add member ──────────────────────────────────────────────────────────────
  const handleAddMember = async () => {
    setAddingMember(true); setError('');
    try {
      const res = await organisationService.createMember(selectedOrgId, addMemberForm);
      const result = res.data || res;
      setAddMemberResult(result);
      setSuccess(result.message || `${addMemberForm.email} added!`);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add member');
    } finally { setAddingMember(false); }
  };

  // ── Invite by email ─────────────────────────────────────────────────────────
  const handleInvite = async () => {
    setInviting(true); setError('');
    try {
      await organisationService.inviteMember(selectedOrgId, { email: inviteEmail, role: inviteRole });
      setSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteOpen(false);
      setInviteEmail(''); setInviteRole('MEMBER');
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send invitation');
    } finally { setInviting(false); }
  };

  // ── Edit member ─────────────────────────────────────────────────────────────
  const openEditMember = (m) => {
    setEditingMember(m);
    setEditMemberRole(m.role);
    setEditMemberBranch(m.branch_id || '');
    setEditMemberOpen(true);
  };

  const handleEditMember = async () => {
    try {
      await organisationService.updateMember(selectedOrgId, editingMember.id, {
        role: editMemberRole,
        branch_id: editMemberBranch || null,
      });
      setSuccess('Member updated.');
      setEditMemberOpen(false);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update member');
    }
  };

  // ── Remove member ────────────────────────────────────────────────────────────
  const handleRemoveMember = async () => {
    try {
      await organisationService.removeMember(selectedOrgId, removingMember.id);
      setSuccess(`${removingMember.email} removed.`);
      setRemoveConfirmOpen(false);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to remove member');
    }
  };

  // ── Branch ──────────────────────────────────────────────────────────────────
  const openAddBranch = () => {
    setBranchForm({ name: '', code: '', city: '', address: '', postcode: '', phone: '' });
    setEditingBranchId(null);
    setBranchDialogOpen(true);
  };

  const openEditBranch = (b) => {
    setBranchForm({ name: b.name, code: b.code || '', city: b.city || '', address: b.address || '', postcode: b.postcode || '', phone: b.phone || '' });
    setEditingBranchId(b.id);
    setBranchDialogOpen(true);
  };

  const handleSaveBranch = async () => {
    setSavingBranch(true); setError('');
    try {
      if (editingBranchId) {
        await organisationService.updateBranch(selectedOrgId, editingBranchId, branchForm);
        setSuccess('Branch updated.');
      } else {
        await organisationService.createBranch(selectedOrgId, branchForm);
        setSuccess(`Branch "${branchForm.name}" created.`);
      }
      setBranchDialogOpen(false);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save branch');
    } finally { setSavingBranch(false); }
  };

  const handleDeleteBranch = async (branchId, name) => {
    if (!window.confirm(`Remove branch "${name}"? Members will be unassigned.`)) return;
    try {
      await organisationService.deleteBranch(selectedOrgId, branchId);
      setSuccess(`Branch "${name}" removed.`);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to remove branch');
    }
  };

  // ── Settings ────────────────────────────────────────────────────────────────
  const handleSaveSettings = async () => {
    setSavingSettings(true); setError('');
    try {
      await organisationService.update(selectedOrgId, settingsForm);
      setSuccess('Organisation details saved.');
      setEditingSettings(false);
      refresh();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save');
    } finally { setSavingSettings(false); }
  };

  // ── Sales access request ────────────────────────────────────────────────────
  const handleRequestSalesAccess = async () => {
    if (!salesIndustry) { setError('Please select your industry first.'); return; }
    setRequestingSales(true); setError('');
    try {
      const res = await organisationService.requestSalesAccess(selectedOrgId, {
        industry: salesIndustry,
        notes: salesNotes,
      });
      setSuccess(res.message);
      setSalesRequested(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit request');
    } finally { setRequestingSales(false); }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => setSuccess('Copied!'));
  };

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;

  // ── No orgs ──────────────────────────────────────────────────────────────────
  if (orgs.length === 0 && requests.length === 0) {
    return (
      <Box>
        {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}
        <Paper sx={{ p: 5, textAlign: 'center' }}>
          <BusinessIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h5" fontWeight={700} gutterBottom>You're not part of any organisation</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>Create one to start using SignSimple with your team.</Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            Create Organisation
          </Button>
        </Paper>
        <CreateOrgDialog open={createOpen} onClose={() => setCreateOpen(false)}
          form={createForm} setForm={setCreateForm}
          creating={creating} setCreating={setCreating}
          setSuccess={setSuccess} setError={setError} reload={loadOrgs} />
      </Box>
    );
  }

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Org selector (if multiple orgs) */}
      {orgs.length > 1 && (
        <Paper sx={{ p: 2, mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" fontWeight={600}>Organisation:</Typography>
          <FormControl size="small" sx={{ minWidth: 250 }}>
            <Select value={selectedOrgId || ''} onChange={(e) => setSelectedOrgId(e.target.value)}>
              {orgs.map((o) => (
                <MenuItem key={o.organisation_id} value={o.organisation_id}>
                  {o.organisation_name} — <em>{o.role_display}</em>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button size="small" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>New Org</Button>
        </Paper>
      )}

      {orgDetail && (
        <Paper sx={{ borderRadius: 3 }}>
          {/* Header */}
          <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2, borderBottom: '1px solid #e0e0e0' }}>
            <Avatar sx={{ bgcolor: orgDetail.primary_colour || 'primary.main', width: 52, height: 52, fontSize: 22, fontWeight: 700 }}>
              {orgDetail.name.charAt(0)}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h5" fontWeight={700}>{orgDetail.name}</Typography>
              <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                <Chip label={myOrg?.role_display || 'Member'} size="small" color={ROLE_COLORS[myOrg?.role] || 'default'} />
                <Chip label={orgDetail.plan} size="small" variant="outlined" />
                {orgDetail.sales_access_enabled && <Chip label="Sales Enabled" size="small" color="success" />}
              </Stack>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">Documents this month</Typography>
              <Typography variant="h6" fontWeight={700}>{orgDetail.documents_used} / {orgDetail.documents_limit}</Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, (orgDetail.documents_used / orgDetail.documents_limit) * 100)}
                sx={{ height: 4, borderRadius: 2, mt: 0.5, width: 120 }}
              />
            </Box>
          </Box>

          {/* Tabs */}
          <Box sx={{ borderBottom: '1px solid #e0e0e0' }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 3 }}>
              <Tab label={`Members (${members.length})`} icon={<GroupIcon />} iconPosition="start" />
              <Tab label={`Branches (${branches.length})`} icon={<AccountTreeIcon />} iconPosition="start" />
              <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
              <Tab label="Sales Access" icon={<PointOfSaleIcon />} iconPosition="start" />
            </Tabs>
          </Box>

          <Box sx={{ p: 3 }}>

            {/* ── MEMBERS TAB ─────────────────────────────────────────── */}
            <TabPanel value={tab} index={0}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Team Members</Typography>
                {canManage && (
                  <Stack direction="row" spacing={1}>
                    <Button variant="outlined" startIcon={<EmailIcon />} onClick={() => setInviteOpen(true)}>
                      Invite by Email
                    </Button>
                    <Button variant="contained" startIcon={<PersonAddIcon />} onClick={() => { setAddMemberResult(null); setAddMemberOpen(true); }}>
                      Add Member
                    </Button>
                  </Stack>
                )}
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Email</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Role</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Branch</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Joined</TableCell>
                      {canAdmin && <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {members.map((m) => (
                      <TableRow key={m.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Avatar sx={{ width: 28, height: 28, fontSize: 12, bgcolor: 'primary.light' }}>
                              {(m.full_name || m.email).charAt(0).toUpperCase()}
                            </Avatar>
                            <Typography variant="body2">{m.full_name || '—'}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell><Typography variant="body2">{m.email}</Typography></TableCell>
                        <TableCell><Chip label={m.role_display} size="small" color={ROLE_COLORS[m.role] || 'default'} /></TableCell>
                        <TableCell><Typography variant="body2">{m.branch_name || '—'}</Typography></TableCell>
                        <TableCell><Typography variant="body2">{m.joined_at ? new Date(m.joined_at).toLocaleDateString() : '—'}</Typography></TableCell>
                        {canAdmin && (
                          <TableCell>
                            <Stack direction="row" spacing={0.5}>
                              {m.role !== 'OWNER' && (
                                <>
                                  <Tooltip title="Edit role / branch">
                                    <IconButton size="small" onClick={() => openEditMember(m)}><EditIcon fontSize="small" /></IconButton>
                                  </Tooltip>
                                  <Tooltip title="Resend setup email">
                                    <IconButton size="small" onClick={async () => {
                                      try {
                                        const r = await organisationService.resendMemberSetup(selectedOrgId, m.id);
                                        setSuccess(r.message);
                                      } catch (err) { setError(err.response?.data?.error || 'Failed'); }
                                    }}>
                                      <SendIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Remove member">
                                    <IconButton size="small" color="error" onClick={() => { setRemovingMember(m); setRemoveConfirmOpen(true); }}>
                                      <DeleteIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </>
                              )}
                            </Stack>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pending invitations */}
              {invitations.filter(i => i.status === 'PENDING').length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>Pending Invitations</Typography>
                  {invitations.filter(i => i.status === 'PENDING').map((inv) => (
                    <Box key={inv.id} sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1, borderBottom: '1px solid #f0f0f0' }}>
                      <EmailIcon fontSize="small" color="action" />
                      <Typography variant="body2" sx={{ flex: 1 }}>{inv.email}</Typography>
                      <Chip label={inv.role_display} size="small" />
                      <Typography variant="caption" color="text.secondary">
                        Expires {new Date(inv.expires_at).toLocaleDateString()}
                      </Typography>
                      {canManage && (
                        <Tooltip title="Revoke invitation">
                          <IconButton size="small" onClick={async () => {
                            try {
                              await organisationService.revokeInvitation(inv.id);
                              setSuccess('Invitation revoked.');
                              refresh();
                            } catch { setError('Failed to revoke'); }
                          }}>
                            <CloseIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  ))}
                </Box>
              )}
            </TabPanel>

            {/* ── BRANCHES TAB ────────────────────────────────────────── */}
            <TabPanel value={tab} index={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>Branches / Locations</Typography>
                {canAdmin && (
                  <Button variant="contained" startIcon={<AddIcon />} onClick={openAddBranch}>
                    Add Branch
                  </Button>
                )}
              </Box>
              {branches.length === 0 ? (
                <Alert severity="info">No branches yet. Branches let you organise members by location or team.</Alert>
              ) : (
                <Grid container spacing={2}>
                  {branches.map((b) => (
                    <Grid item xs={12} md={6} key={b.id}>
                      <Card variant="outlined">
                        <CardContent sx={{ pb: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <Box>
                              <Typography variant="subtitle1" fontWeight={700}>{b.name}</Typography>
                              {b.code && <Typography variant="caption" color="text.secondary">Code: {b.code}</Typography>}
                              {b.city && <Typography variant="body2" color="text.secondary">{b.city}</Typography>}
                              <Chip label={`${b.member_count} member${b.member_count !== 1 ? 's' : ''}`} size="small" sx={{ mt: 0.5 }} />
                            </Box>
                            {canAdmin && (
                              <Stack direction="row">
                                <Tooltip title="Edit branch"><IconButton size="small" onClick={() => openEditBranch(b)}><EditIcon fontSize="small" /></IconButton></Tooltip>
                                <Tooltip title="Remove branch"><IconButton size="small" color="error" onClick={() => handleDeleteBranch(b.id, b.name)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
                              </Stack>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </TabPanel>

            {/* ── SETTINGS TAB ────────────────────────────────────────── */}
            <TabPanel value={tab} index={2}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>Organisation Details</Typography>
                {canAdmin && !editingSettings && (
                  <Button startIcon={<EditIcon />} onClick={() => setEditingSettings(true)}>Edit</Button>
                )}
              </Box>

              {!editingSettings ? (
                <Grid container spacing={2}>
                  {[
                    { label: 'Name', value: orgDetail.name },
                    { label: 'Domain', value: orgDetail.domain },
                    { label: 'Email', value: orgDetail.email },
                    { label: 'Phone', value: orgDetail.phone },
                    { label: 'Website', value: orgDetail.website },
                    { label: 'Address', value: orgDetail.address },
                    { label: 'City', value: orgDetail.city },
                    { label: 'Postcode', value: orgDetail.postcode },
                    { label: 'Country', value: orgDetail.country },
                    { label: 'Company Number', value: orgDetail.company_number },
                    { label: 'VAT Number', value: orgDetail.vat_number },
                  ].map(({ label, value }) => (
                    <Grid item xs={12} md={6} key={label}>
                      <Typography variant="caption" color="text.secondary">{label}</Typography>
                      <Typography variant="body1">{value || <em style={{ color: '#aaa' }}>Not set</em>}</Typography>
                      <Divider sx={{ mt: 0.5 }} />
                    </Grid>
                  ))}
                  <Grid item xs={12} md={6}>
                    <Typography variant="caption" color="text.secondary">Brand Colour</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Box sx={{ width: 24, height: 24, borderRadius: 1, bgcolor: orgDetail.primary_colour, border: '1px solid #ddd' }} />
                      <Typography variant="body2">{orgDetail.primary_colour}</Typography>
                    </Box>
                  </Grid>
                </Grid>
              ) : (
                <Grid container spacing={2}>
                  {[
                    { key: 'name', label: 'Organisation Name', required: true },
                    { key: 'email', label: 'Contact Email', type: 'email' },
                    { key: 'phone', label: 'Phone' },
                    { key: 'website', label: 'Website' },
                    { key: 'address', label: 'Address' },
                    { key: 'city', label: 'City' },
                    { key: 'postcode', label: 'Postcode' },
                    { key: 'country', label: 'Country' },
                    { key: 'company_number', label: 'Company Number' },
                    { key: 'vat_number', label: 'VAT Number' },
                  ].map(({ key, label, type, required }) => (
                    <Grid item xs={12} md={6} key={key}>
                      <TextField
                        fullWidth size="small" label={label} type={type || 'text'}
                        value={settingsForm[key] || ''}
                        onChange={(e) => setSettingsForm({ ...settingsForm, [key]: e.target.value })}
                        required={required}
                      />
                    </Grid>
                  ))}
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth size="small" label="Brand Colour (hex)" type="color"
                      value={settingsForm.primary_colour || '#1565c0'}
                      onChange={(e) => setSettingsForm({ ...settingsForm, primary_colour: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <Stack direction="row" spacing={1}>
                      <Button variant="contained" onClick={handleSaveSettings} disabled={savingSettings}>
                        {savingSettings ? <CircularProgress size={20} /> : 'Save Changes'}
                      </Button>
                      <Button onClick={() => setEditingSettings(false)}>Cancel</Button>
                    </Stack>
                  </Grid>
                </Grid>
              )}
            </TabPanel>

            {/* ── SALES ACCESS TAB ─────────────────────────────────────── */}
            <TabPanel value={tab} index={3}>
              <Typography variant="h6" fontWeight={600} gutterBottom>Sales & Invoicing Access</Typography>
              {orgDetail.sales_access_enabled ? (
                <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 3 }}>
                  Sales & Invoicing is enabled for this organisation. Your team can access Daily Sales, Clients, and Invoices.
                </Alert>
              ) : (
                <Alert severity="info" sx={{ mb: 3 }}>
                  Sales & Invoicing is not yet enabled. Request access below — our team will review and enable it for you.
                </Alert>
              )}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <PointOfSaleIcon color="primary" sx={{ fontSize: 36, mb: 1 }} />
                      <Typography variant="subtitle1" fontWeight={700}>What you get</Typography>
                      {[
                        'Daily sales entry per client',
                        'Invoice generation with PDF',
                        'Client confirmation emails',
                        'Dispute management',
                        'Excel exports',
                        'Client portal access',
                      ].map((f) => (
                        <Box key={f} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <CheckCircleIcon fontSize="small" color="success" />
                          <Typography variant="body2">{f}</Typography>
                        </Box>
                      ))}
                    </CardContent>
                  </Card>
                </Grid>
                {!orgDetail.sales_access_enabled && canAdmin && (
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      {salesRequested ? (
                        <Box sx={{ textAlign: 'center', py: 2 }}>
                          <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                            Request Submitted!
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Our team will review your request and enable Sales &amp; Invoicing
                            within 24 hours. We'll email you when it's ready.
                          </Typography>
                          {orgDetail.industry_display && (
                            <Chip label={orgDetail.industry_display} color="primary" size="small" sx={{ mt: 2 }} />
                          )}
                        </Box>
                      ) : (
                        <>
                          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                            Request Sales Access
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Tell us about your use case so we can set up the right configuration for you.
                          </Typography>
                          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                            <InputLabel>Your industry *</InputLabel>
                            <Select
                              value={salesIndustry}
                              onChange={(e) => setSalesIndustry(e.target.value)}
                              label="Your industry *"
                            >
                              {INDUSTRIES.map(i => (
                                <MenuItem key={i.value} value={i.value}>{i.label}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                          <TextField
                            fullWidth size="small" multiline rows={2}
                            label="How will you use it? (optional)"
                            placeholder="e.g. Track daily meal deliveries to office clients, generate monthly invoices"
                            value={salesNotes}
                            onChange={(e) => setSalesNotes(e.target.value)}
                            sx={{ mb: 2 }}
                          />
                          <Button
                            variant="contained" size="large" fullWidth
                            startIcon={requestingSales ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                            onClick={handleRequestSalesAccess}
                            disabled={requestingSales || !salesIndustry}
                            sx={{ fontWeight: 700 }}
                          >
                            {requestingSales ? 'Submitting…' : 'Request Access'}
                          </Button>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
                            Usually enabled within 24 hours
                          </Typography>
                        </>
                      )}
                    </Card>
                  </Grid>
                )}
              </Grid>
            </TabPanel>
          </Box>
        </Paper>
      )}

      {/* Pending requests (for users with no active org yet) */}
      {requests.filter(r => r.status !== 'APPROVED').length > 0 && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>Pending Organisation Requests</Typography>
          {requests.filter(r => r.status !== 'APPROVED').map((req) => (
            <Box key={req.id} sx={{ display: 'flex', alignItems: 'center', py: 1, borderBottom: '1px solid #f0f0f0' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" fontWeight={600}>{req.organisation_name}</Typography>
                <Chip label={req.status_display || req.status} size="small" sx={{ mt: 0.5 }} />
                {req.status === 'PENDING_WORK_EMAIL' && (
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>Check your work email</Typography>
                )}
              </Box>
              {req.status === 'PENDING_WORK_EMAIL' && (
                <Tooltip title="Resend verification email">
                  <IconButton onClick={async () => {
                    try {
                      await organisationService.resendVerification(req.id);
                      setSuccess('Verification email resent!');
                    } catch { setError('Failed to resend'); }
                  }}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          ))}
        </Paper>
      )}

      <Box sx={{ mt: 2 }}>
        <Button startIcon={<AddIcon />} onClick={() => setCreateOpen(true)} variant="outlined" size="small">
          Create Another Organisation
        </Button>
      </Box>

      {/* ── DIALOGS ─────────────────────────────────────────────────────────── */}

      {/* Add Member */}
      <Dialog open={addMemberOpen} onClose={() => setAddMemberOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle><PersonAddIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Add Member</DialogTitle>
        <DialogContent>
          {addMemberResult ? (
            <Box sx={{ py: 1 }}>
              <Alert severity="success" sx={{ mb: 2 }}>{addMemberResult.message}</Alert>
              {addMemberResult.temporary_password && (
                <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 2, mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Temporary password (share securely):</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography fontFamily="monospace" fontWeight={700}>{addMemberResult.temporary_password}</Typography>
                    <IconButton size="small" onClick={() => copyToClipboard(addMemberResult.temporary_password)}><ContentCopyIcon fontSize="small" /></IconButton>
                  </Box>
                </Box>
              )}
              {addMemberResult.password_setup_url && (
                <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    {addMemberResult.email_sent ? 'Setup email sent. Backup link:' : 'Email failed. Share this link:'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography variant="body2" sx={{ wordBreak: 'break-all', flex: 1 }}>{addMemberResult.password_setup_url}</Typography>
                    <IconButton size="small" onClick={() => copyToClipboard(addMemberResult.password_setup_url)}><ContentCopyIcon fontSize="small" /></IconButton>
                  </Box>
                </Box>
              )}
              <Button fullWidth variant="outlined" sx={{ mt: 2 }} onClick={() => { setAddMemberResult(null); setAddMemberForm({ email: '', full_name: '', role: 'MEMBER', method: 'send_email' }); }}>
                Add Another
              </Button>
            </Box>
          ) : (
            <Box sx={{ pt: 1 }}>
              <TextField fullWidth label="Email" type="email" value={addMemberForm.email}
                onChange={(e) => setAddMemberForm({ ...addMemberForm, email: e.target.value })}
                margin="normal" required autoFocus />
              <TextField fullWidth label="Full Name (optional)" value={addMemberForm.full_name}
                onChange={(e) => setAddMemberForm({ ...addMemberForm, full_name: e.target.value })}
                margin="normal" />
              <FormControl fullWidth margin="normal">
                <InputLabel>Role</InputLabel>
                <Select value={addMemberForm.role} onChange={(e) => setAddMemberForm({ ...addMemberForm, role: e.target.value })} label="Role">
                  <MenuItem value="ADMIN">Admin</MenuItem>
                  <MenuItem value="MANAGER">Manager</MenuItem>
                  <MenuItem value="MEMBER">Member</MenuItem>
                  <MenuItem value="VIEWER">Viewer</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth margin="normal">
                <InputLabel>Onboarding method</InputLabel>
                <Select value={addMemberForm.method} onChange={(e) => setAddMemberForm({ ...addMemberForm, method: e.target.value })} label="Onboarding method">
                  <MenuItem value="send_email">Send setup email (they set their own password)</MenuItem>
                  <MenuItem value="temp_password">Generate temp password (you share it)</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        {!addMemberResult && (
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button onClick={() => setAddMemberOpen(false)}>Cancel</Button>
            <Button variant="contained" onClick={handleAddMember} disabled={addingMember || !addMemberForm.email}>
              {addingMember ? <CircularProgress size={20} /> : 'Add Member'}
            </Button>
          </DialogActions>
        )}
      </Dialog>

      {/* Invite by email */}
      <Dialog open={inviteOpen} onClose={() => setInviteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle><EmailIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Invite by Email</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Send an invitation email. They'll get a link to accept and join the organisation.
          </Typography>
          <TextField fullWidth label="Email address" type="email" value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)} margin="normal" autoFocus />
          <FormControl fullWidth margin="normal">
            <InputLabel>Role</InputLabel>
            <Select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)} label="Role">
              <MenuItem value="ADMIN">Admin</MenuItem>
              <MenuItem value="MANAGER">Manager</MenuItem>
              <MenuItem value="MEMBER">Member</MenuItem>
              <MenuItem value="VIEWER">Viewer</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setInviteOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleInvite} disabled={inviting || !inviteEmail}>
            {inviting ? <CircularProgress size={20} /> : 'Send Invitation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit member */}
      <Dialog open={editMemberOpen} onClose={() => setEditMemberOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit Member — {editingMember?.full_name || editingMember?.email}</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Role</InputLabel>
            <Select value={editMemberRole} onChange={(e) => setEditMemberRole(e.target.value)} label="Role">
              {ROLES.map(r => <MenuItem key={r} value={r}>{r}</MenuItem>)}
            </Select>
          </FormControl>
          {branches.length > 0 && (
            <FormControl fullWidth margin="normal">
              <InputLabel>Branch</InputLabel>
              <Select value={editMemberBranch} onChange={(e) => setEditMemberBranch(e.target.value)} label="Branch">
                <MenuItem value="">No branch</MenuItem>
                {branches.map(b => <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>)}
              </Select>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditMemberOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleEditMember}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Remove confirm */}
      <Dialog open={removeConfirmOpen} onClose={() => setRemoveConfirmOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Remove Member?</DialogTitle>
        <DialogContent>
          <Typography>Remove <strong>{removingMember?.full_name || removingMember?.email}</strong> from this organisation? They will lose access immediately.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRemoveConfirmOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleRemoveMember}>Remove</Button>
        </DialogActions>
      </Dialog>

      {/* Branch dialog */}
      <Dialog open={branchDialogOpen} onClose={() => setBranchDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingBranchId ? 'Edit Branch' : 'Add Branch'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={8}><TextField fullWidth size="small" label="Branch Name *" value={branchForm.name} onChange={(e) => setBranchForm({ ...branchForm, name: e.target.value })} /></Grid>
            <Grid item xs={4}><TextField fullWidth size="small" label="Code" value={branchForm.code} onChange={(e) => setBranchForm({ ...branchForm, code: e.target.value })} /></Grid>
            <Grid item xs={12}><TextField fullWidth size="small" label="Address" value={branchForm.address} onChange={(e) => setBranchForm({ ...branchForm, address: e.target.value })} /></Grid>
            <Grid item xs={6}><TextField fullWidth size="small" label="City" value={branchForm.city} onChange={(e) => setBranchForm({ ...branchForm, city: e.target.value })} /></Grid>
            <Grid item xs={6}><TextField fullWidth size="small" label="Postcode" value={branchForm.postcode} onChange={(e) => setBranchForm({ ...branchForm, postcode: e.target.value })} /></Grid>
            <Grid item xs={12}><TextField fullWidth size="small" label="Phone" value={branchForm.phone} onChange={(e) => setBranchForm({ ...branchForm, phone: e.target.value })} /></Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBranchDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveBranch} disabled={savingBranch || !branchForm.name}>
            {savingBranch ? <CircularProgress size={20} /> : 'Save Branch'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create org dialog */}
      <CreateOrgDialog open={createOpen} onClose={() => setCreateOpen(false)}
        form={createForm} setForm={setCreateForm}
        creating={creating} setCreating={setCreating}
        setSuccess={setSuccess} setError={setError} reload={loadOrgs} />
    </Box>
  );
}


// ─── Create Org Dialog (extracted for reuse) ───────────────────────────────────
function CreateOrgDialog({ open, onClose, form, setForm, creating, setCreating, setSuccess, setError, reload }) {
  const handleCreate = async () => {
    setCreating(true); setError('');
    try {
      const res = await organisationService.createRequest(form);
      setSuccess(res.data?.message || 'Verification email sent!');
      onClose();
      reload();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create request');
    } finally { setCreating(false); }
  };
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Organisation</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Submit a request to create an organisation. You'll verify your work email first.
        </Typography>
        <TextField fullWidth label="Organisation Name *" value={form.organisation_name}
          onChange={(e) => setForm({ ...form, organisation_name: e.target.value })} margin="normal" />
        <TextField fullWidth label="Domain *" value={form.organisation_domain}
          onChange={(e) => setForm({ ...form, organisation_domain: e.target.value })}
          margin="normal" placeholder="e.g. acme.co.uk" helperText="Your organisation's email domain" />
        <TextField fullWidth label="Your Work Email *" type="email" value={form.work_email}
          onChange={(e) => setForm({ ...form, work_email: e.target.value })}
          margin="normal" placeholder="e.g. admin@acme.co.uk" />
        <TextField fullWidth label="Companies House Number (optional)" value={form.company_number}
          onChange={(e) => setForm({ ...form, company_number: e.target.value })} margin="normal" />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleCreate}
          disabled={creating || !form.organisation_name || !form.organisation_domain || !form.work_email}>
          {creating ? <CircularProgress size={24} /> : 'Submit Request'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
