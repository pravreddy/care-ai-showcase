import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, Grid, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  IconButton, Alert, CircularProgress, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem,
  Switch, FormControlLabel, Tooltip, InputAdornment, Divider, Card, CardContent,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonIcon from '@mui/icons-material/Person';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import BusinessIcon from '@mui/icons-material/Business';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import GroupIcon from '@mui/icons-material/Group';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import { salesService, organisationService } from '../../services/api';

const PRICING_MODELS = [
  { value: 'ITEMISED', label: 'Itemised Pricing', description: 'List items + prices each day' },
  { value: 'PER_HEAD', label: 'Per Head', description: 'Fixed rate × number of people' },
  { value: 'FIXED', label: 'Fixed Daily', description: 'Same amount every day' },
];

const initialFormState = {
  organisation: '',
  branch: '',
  name: '',
  legal_name: '',
  contact_person: '',
  contact_email: '',
  contact_phone: '',
  address: '',
  city: '',
  country: '',
  gst_number: '',
  pan_number: '',
  default_num_people: 0,
  default_packing_charge: 0,
  default_courier_charge: 0,
  pricing_model: 'ITEMISED',
  fixed_daily_rate: 0,
  per_head_rate: 0,
  skip_weekends: true,
  is_active: true,
  notes: '',
};

export default function ClientsManager() {
  const [clients, setClients] = useState([]);
  const [organisations, setOrganisations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState('add'); // 'add' or 'edit'
  const [formData, setFormData] = useState(initialFormState);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);

  // Load clients and organisations
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [clientsRes, orgsRes] = await Promise.all([
        salesService.getClients(),
        organisationService.getMyOrganisations(),
      ]);
      setClients(clientsRes.results || clientsRes || []);
      setOrganisations(orgsRes.data || []);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setDialogMode('add');
    setFormData({
      ...initialFormState,
      organisation: organisations.length > 0 ? organisations[0].organisation_id : '',
    });
    setEditingId(null);
    setDialogOpen(true);
  };

  const handleOpenEdit = (client) => {
    setDialogMode('edit');
    setFormData({
      organisation: client.organisation,
      branch: client.branch || '',
      name: client.name,
      legal_name: client.legal_name || '',
      contact_person: client.contact_person || '',
      contact_email: client.contact_email || '',
      contact_phone: client.contact_phone || '',
      address: client.address || '',
      city: client.city || '',
      country: client.country || '',
      gst_number: client.gst_number || '',
      pan_number: client.pan_number || '',
      default_num_people: client.default_num_people || 0,
      default_packing_charge: parseFloat(client.default_packing_charge) || 0,
      default_courier_charge: parseFloat(client.default_courier_charge) || 0,
      pricing_model: client.pricing_model || 'ITEMISED',
      fixed_daily_rate: parseFloat(client.fixed_daily_rate) || 0,
      per_head_rate: parseFloat(client.per_head_rate) || 0,
      skip_weekends: client.skip_weekends !== false,
      is_active: client.is_active !== false,
      notes: client.notes || '',
    });
    setEditingId(client.id);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData(initialFormState);
    setEditingId(null);
  };

  const handleInputChange = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({ ...formData, [field]: value });
  };

  const handleSave = async () => {
    // Validation
    if (!formData.name.trim()) {
      setError('Client name is required');
      return;
    }
    if (!formData.organisation) {
      setError('Please select an organisation');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const payload = {
        ...formData,
        branch: formData.branch || null,
        default_num_people: parseInt(formData.default_num_people) || 0,
        default_packing_charge: parseFloat(formData.default_packing_charge) || 0,
        default_courier_charge: parseFloat(formData.default_courier_charge) || 0,
        fixed_daily_rate: parseFloat(formData.fixed_daily_rate) || 0,
        per_head_rate: parseFloat(formData.per_head_rate) || 0,
      };

      if (dialogMode === 'edit') {
        await salesService.updateClient(editingId, payload);
        setSuccess('Client updated successfully!');
      } else {
        await salesService.createClient(payload);
        setSuccess('Client created successfully!');
      }

      handleCloseDialog();
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to save client');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (client) => {
    if (!window.confirm(`Are you sure you want to delete "${client.name}"? This cannot be undone.`)) {
      return;
    }

    try {
      await salesService.deleteClient(client.id);
      setSuccess('Client deleted');
      loadData();
    } catch (err) {
      setError('Failed to delete client. It may have associated sales records.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Clients
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage your clients who receive daily deliveries. Add clients here before entering daily sales.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Header with Add Button */}
      <Paper sx={{ p: 2, mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6">{clients.length} Client{clients.length !== 1 ? 's' : ''}</Typography>
          <Typography variant="body2" color="text.secondary">
            {clients.filter(c => c.is_active).length} active
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenAdd}
          disabled={organisations.length === 0}
        >
          Add Client
        </Button>
      </Paper>

      {/* No organisations warning */}
      {organisations.length === 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You need to be a member of an organisation with sales access to add clients.
          Go to <strong>Organisation</strong> to create or join one first.
        </Alert>
      )}

      {/* Clients Table */}
      {clients.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Client Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Organisation</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Contact</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Location</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Pricing</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="right">This Month</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clients.map((client) => (
                <TableRow key={client.id} hover>
                  <TableCell>
                    <Typography fontWeight={600}>{client.name}</Typography>
                    {client.default_num_people > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        <GroupIcon sx={{ fontSize: 12, mr: 0.5 }} />
                        {client.default_num_people} people default
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{client.organisation_name}</Typography>
                    {client.branch_name && (
                      <Typography variant="caption" color="text.secondary">{client.branch_name}</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {client.contact_person && (
                      <Typography variant="body2">{client.contact_person}</Typography>
                    )}
                    {client.contact_email && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {client.contact_email}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {client.city || '—'}
                    {client.country && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {client.country}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={client.pricing_model}
                      size="small"
                      color={client.pricing_model === 'FIXED' ? 'primary' : client.pricing_model === 'PER_HEAD' ? 'secondary' : 'default'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography fontWeight={600} color="success.dark">
                      ₹{(client.total_sales_this_month || 0).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={client.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={client.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleOpenEdit(client)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" color="error" onClick={() => handleDelete(client)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <BusinessIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Clients Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add your first client to start tracking daily sales and generating invoices.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenAdd}
            disabled={organisations.length === 0}
          >
            Add Your First Client
          </Button>
        </Paper>
      )}

      {/* Add/Edit Client Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogMode === 'edit' ? 'Edit Client' : 'Add New Client'}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Basic Information */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary" sx={{ mb: 2 }}>
                Basic Information
              </Typography>
            </Grid>

            {organisations.length > 1 && (
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Organisation</InputLabel>
                  <Select
                    value={formData.organisation}
                    onChange={handleInputChange('organisation')}
                    label="Organisation"
                  >
                    {organisations.map((org) => (
                      <MenuItem key={org.organisation_id} value={org.organisation_id}>
                        {org.organisation_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Client Name"
                value={formData.name}
                onChange={handleInputChange('name')}
                required
                placeholder="e.g., TechCorp Bangalore"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><BusinessIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Legal / Trading Name"
                value={formData.legal_name}
                onChange={handleInputChange('legal_name')}
                placeholder="e.g., TechCorp Private Limited"
                helperText="Appears on invoices if set (otherwise Client Name is used)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Contact Person"
                value={formData.contact_person}
                onChange={handleInputChange('contact_person')}
                placeholder="e.g., Priya Sharma"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><PersonIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Contact Email"
                type="email"
                value={formData.contact_email}
                onChange={handleInputChange('contact_email')}
                placeholder="e.g., priya@techcorp.in"
                helperText="Used for sending invoices"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><EmailIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Contact Phone"
                value={formData.contact_phone}
                onChange={handleInputChange('contact_phone')}
                placeholder="e.g., +91 98765 43210"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><PhoneIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="City"
                value={formData.city}
                onChange={handleInputChange('city')}
                placeholder="e.g., Bangalore"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><LocationOnIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Country"
                value={formData.country}
                onChange={handleInputChange('country')}
                placeholder="e.g., India"
                helperText="Used for tax label (GST/VAT/Sales Tax) and currency defaults"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Delivery Address"
                value={formData.address}
                onChange={handleInputChange('address')}
                placeholder="e.g., 123 Tech Park, Whitefield"
                multiline
                rows={2}
              />
            </Grid>

            {/* Tax & Registration (shown when country suggests India) */}
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 2 }}>
                Tax & Registration
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="GST / GSTIN Number"
                value={formData.gst_number}
                onChange={handleInputChange('gst_number')}
                placeholder="e.g., 29ABCDE1234F1Z5"
                helperText="Goods & Services Tax number (India). Shown on invoices."
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="PAN Number"
                value={formData.pan_number}
                onChange={handleInputChange('pan_number')}
                placeholder="e.g., ABCDE1234F"
                helperText="Permanent Account Number (India). Shown on invoices."
                inputProps={{ maxLength: 10, style: { textTransform: 'uppercase' } }}
              />
            </Grid>

            {/* Pricing Section */}
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 2 }}>
                Pricing Model
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Pricing Model</InputLabel>
                <Select
                  value={formData.pricing_model}
                  onChange={handleInputChange('pricing_model')}
                  label="Pricing Model"
                >
                  {PRICING_MODELS.map((model) => (
                    <MenuItem key={model.value} value={model.value}>
                      {model.label} — {model.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {formData.pricing_model === 'PER_HEAD' && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Per Head Rate"
                  type="number"
                  value={formData.per_head_rate}
                  onChange={handleInputChange('per_head_rate')}
                  placeholder="e.g., 120"
                  InputProps={{
                    startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                  }}
                />
              </Grid>
            )}

            {formData.pricing_model === 'FIXED' && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Fixed Daily Rate"
                  type="number"
                  value={formData.fixed_daily_rate}
                  onChange={handleInputChange('fixed_daily_rate')}
                  placeholder="e.g., 5000"
                  InputProps={{
                    startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                  }}
                />
              </Grid>
            )}

            {/* Default Values */}
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 2 }}>
                Default Values (pre-fill for daily entry)
              </Typography>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Default Headcount"
                type="number"
                value={formData.default_num_people}
                onChange={handleInputChange('default_num_people')}
                placeholder="e.g., 50"
                helperText="Typical number of people served"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><GroupIcon /></InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Default Packing Charge"
                type="number"
                value={formData.default_packing_charge}
                onChange={handleInputChange('default_packing_charge')}
                placeholder="e.g., 100"
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Default Courier Charge"
                type="number"
                value={formData.default_courier_charge}
                onChange={handleInputChange('default_courier_charge')}
                placeholder="e.g., 200"
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
              />
            </Grid>

            {/* Settings */}
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" color="primary" sx={{ mt: 2, mb: 2 }}>
                Settings
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.skip_weekends}
                    onChange={handleInputChange('skip_weekends')}
                  />
                }
                label="Skip Weekends (auto-mark Sat/Sun as holidays)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={handleInputChange('is_active')}
                  />
                }
                label="Active Client"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                value={formData.notes}
                onChange={handleInputChange('notes')}
                multiline
                rows={2}
                placeholder="Any additional notes about this client..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseDialog} startIcon={<CloseIcon />}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {saving ? 'Saving...' : (dialogMode === 'edit' ? 'Update Client' : 'Add Client')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
