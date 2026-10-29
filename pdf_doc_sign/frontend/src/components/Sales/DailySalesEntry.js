import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper, Typography, TextField, Button, Grid, Box,
  Select, MenuItem, FormControl, InputLabel, Switch,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  IconButton, Alert, CircularProgress, Chip, Stack, Tooltip,
  Dialog, DialogTitle, DialogContent, DialogActions, Divider,
  Checkbox, FormControlLabel,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { salesService } from '../../services/api';
import api from '../../services/api';

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function getDayName(dateStr) {
  if (!dateStr) return '';
  return DAYS[new Date(dateStr).getDay()];
}

// Helper to parse existing items_description to line items
function parseItemsToLineItems(itemsDescription) {
  if (!itemsDescription) return [];
  // Try to parse as JSON first (new format)
  try {
    const parsed = JSON.parse(itemsDescription);
    if (Array.isArray(parsed)) return parsed;
  } catch {
    // Fall back to parsing old text format like "5 Chapathi @ ₹10, 10 Phulka @ ₹8"
    // Or just return as single item
    if (itemsDescription.includes('@')) {
      const parts = itemsDescription.split(',').map(s => s.trim()).filter(Boolean);
      return parts.map((part, idx) => {
        const match = part.match(/^(\d+)\s+(.+?)\s*@\s*₹?(\d+(?:\.\d+)?)/i);
        if (match) {
          return {
            id: `legacy-${idx}`,
            item_name: match[2].trim(),
            quantity: parseInt(match[1]) || 1,
            unit_price: parseFloat(match[3]) || 0,
          };
        }
        return { id: `legacy-${idx}`, item_name: part, quantity: 1, unit_price: 0 };
      });
    }
    return [{ id: 'legacy-0', item_name: itemsDescription, quantity: 1, unit_price: 0 }];
  }
  return [];
}

// Helper to serialize line items to items_description (JSON string)
function serializeLineItems(lineItems) {
  return JSON.stringify(lineItems.map(({ item_name, quantity, unit_price }) => ({
    item_name,
    quantity,
    unit_price,
  })));
}

// Helper to format line items for display
function formatLineItemsDisplay(lineItems) {
  if (!lineItems || lineItems.length === 0) return '';
  return lineItems.map(item => `${item.quantity}x ${item.item_name}`).join(', ');
}

// Calculate total from line items
function calculateLineItemsTotal(lineItems) {
  return lineItems.reduce((sum, item) => sum + (item.quantity || 0) * (item.unit_price || 0), 0);
}

export default function DailySalesEntry() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [clientData, setClientData] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Items Dialog State
  const [itemsDialogOpen, setItemsDialogOpen] = useState(false);
  const [editingEntryIndex, setEditingEntryIndex] = useState(null);
  const [editingLineItems, setEditingLineItems] = useState([]);

  // Month navigation
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(new Date().getMonth()); // 0-indexed

  // Load clients
  useEffect(() => {
    salesService.getClients().then((data) => {
      setClients(data.results || data || []);
    }).catch(() => setError('Failed to load clients'));
  }, []);

  const goToPrevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11); }
    else { setViewMonth(viewMonth - 1); }
  };

  const goToNextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0); }
    else { setViewMonth(viewMonth + 1); }
  };

  const goToCurrentMonth = () => {
    const now = new Date();
    setViewYear(now.getFullYear());
    setViewMonth(now.getMonth());
  };

  const isCurrentMonth = viewYear === new Date().getFullYear() && viewMonth === new Date().getMonth();

  // Load client details and existing entries
  useEffect(() => {
    if (!selectedClient) return;
    const client = clients.find((c) => c.id === selectedClient);
    setClientData(client);

    // Load entries for selected month
    const fromDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`;
    const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate();
    const toDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${lastDay}`;

    setLoading(true);
    salesService.getDailySales({ client: selectedClient, from_date: fromDate, to_date: toDate })
      .then((data) => {
        const existing = data.results || data;
        // Fill in all days of the month
        const allDays = [];
        for (let d = 1; d <= lastDay; d++) {
          const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
          const existing_entry = existing.find((e) => e.date === dateStr);
          if (existing_entry) {
            // Parse line items from items_description
            const lineItems = parseItemsToLineItems(existing_entry.items_description);
            allDays.push({ 
              ...existing_entry, 
              line_items: lineItems,
              _saved: true 
            });
          } else {
            allDays.push({
              date: dateStr,
              day_name: getDayName(dateStr),
              is_holiday: false,
              holiday_reason: '',
              num_people: client?.default_num_people || 0,
              items_description: '',
              line_items: [],
              item_price: 0,
              food_price_per_day: 0,
              packing_charges: parseFloat(client?.default_packing_charge) || 0,
              courier_charges: parseFloat(client?.default_courier_charge) || 0,
              total_charge: 0,
              _saved: false,
              _new: true,
            });
          }
        }
        setEntries(allDays);
      })
      .catch(() => setError('Failed to load entries'))
      .finally(() => setLoading(false));
  }, [selectedClient, clients, viewYear, viewMonth]);

  const recalculateEntry = useCallback((entry) => {
    if (entry.is_holiday) {
      return {
        ...entry,
        item_price: 0,
        food_price_per_day: 0,
        packing_charges: 0,
        courier_charges: 0,
        total_charge: 0,
      };
    }

    // Calculate food total from line items
    const foodTotal = calculateLineItemsTotal(entry.line_items || []);
    const packingCharges = parseFloat(entry.packing_charges) || 0;
    const courierCharges = parseFloat(entry.courier_charges) || 0;
    
    return {
      ...entry,
      food_price_per_day: foodTotal,
      total_charge: foodTotal + packingCharges + courierCharges,
    };
  }, []);

  const updateEntry = (index, field, value) => {
    const updated = [...entries];
    updated[index] = { ...updated[index], [field]: value, _saved: false };
    updated[index] = recalculateEntry(updated[index]);
    setEntries(updated);
  };

  const openItemsDialog = (index) => {
    const entry = entries[index];
    setEditingEntryIndex(index);
    // Clone line items for editing
    setEditingLineItems(
      (entry.line_items || []).map((item, idx) => ({
        ...item,
        id: item.id || `item-${idx}-${Date.now()}`,
      }))
    );
    setItemsDialogOpen(true);
  };

  const closeItemsDialog = () => {
    setItemsDialogOpen(false);
    setEditingEntryIndex(null);
    setEditingLineItems([]);
  };

  const addLineItem = () => {
    setEditingLineItems([
      ...editingLineItems,
      { id: `new-${Date.now()}`, item_name: '', quantity: 1, unit_price: 0 },
    ]);
  };

  const updateLineItem = (itemIndex, field, value) => {
    const updated = [...editingLineItems];
    updated[itemIndex] = { ...updated[itemIndex], [field]: value };
    setEditingLineItems(updated);
  };

  const deleteLineItem = (itemIndex) => {
    setEditingLineItems(editingLineItems.filter((_, i) => i !== itemIndex));
  };

  const saveLineItems = () => {
    if (editingEntryIndex === null) return;
    
    const updated = [...entries];
    updated[editingEntryIndex] = {
      ...updated[editingEntryIndex],
      line_items: editingLineItems.filter(item => item.item_name.trim()),
      items_description: serializeLineItems(editingLineItems.filter(item => item.item_name.trim())),
      _saved: false,
    };
    updated[editingEntryIndex] = recalculateEntry(updated[editingEntryIndex]);
    setEntries(updated);
    closeItemsDialog();
  };

  const copyFromPrevious = (index) => {
    if (index === 0) return;
    
    // Find the most recent non-holiday entry before this one
    let prevIndex = index - 1;
    while (prevIndex >= 0 && entries[prevIndex].is_holiday) {
      prevIndex--;
    }
    if (prevIndex < 0) return;
    
    const prev = entries[prevIndex];
    const updated = [...entries];
    updated[index] = {
      ...updated[index],
      line_items: prev.line_items.map((item, idx) => ({
        ...item,
        id: `copy-${idx}-${Date.now()}`,
      })),
      items_description: prev.items_description,
      num_people: prev.num_people,
      packing_charges: prev.packing_charges,
      courier_charges: prev.courier_charges,
      _saved: false,
    };
    updated[index] = recalculateEntry(updated[index]);
    setEntries(updated);
  };

  const saveAll = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    const toSave = entries.filter((e) => !e._saved && (e.line_items?.length > 0 || e.is_holiday || e.items_description));
    if (toSave.length === 0) {
      setError('Nothing to save. Add items to at least one day.');
      setSaving(false);
      return;
    }

    try {
      const payload = {
        sales: toSave.map((e) => ({
          client: selectedClient,
          date: e.date,
          is_holiday: e.is_holiday,
          holiday_reason: e.holiday_reason || '',
          num_people: parseInt(e.num_people) || 0,
          items_description: e.items_description || serializeLineItems(e.line_items || []),
          item_price: 0, // Not used anymore
          food_price_per_day: parseFloat(e.food_price_per_day) || 0,
          packing_charges: parseFloat(e.packing_charges) || 0,
          courier_charges: parseFloat(e.courier_charges) || 0,
        })),
      };
      const result = await salesService.bulkCreateSales(payload);
      setSuccess(`Saved ${result.created} entries successfully!`);
      setEntries((prev) => prev.map((e) => ({ ...e, _saved: true })));
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const monthTotal = entries.reduce((sum, e) => sum + (parseFloat(e.total_charge) || 0), 0);
  const editingTotal = calculateLineItemsTotal(editingLineItems);

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Daily Sales Entry
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Enter daily deliveries for each client. Click on the Items cell to add/edit menu items.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Client Selector + Month Navigation */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Select Client</InputLabel>
              <Select
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                label="Select Client"
              >
                {clients.length === 0 ? (
                  <MenuItem value="" disabled>No clients found - add clients first</MenuItem>
                ) : (
                  clients.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      {c.name} — {c.organisation_name}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            {/* Month Navigation */}
            <Stack direction="row" alignItems="center" spacing={0.5} justifyContent="center">
              <IconButton onClick={goToPrevMonth} size="small"><ChevronLeftIcon /></IconButton>
              <Typography variant="subtitle1" fontWeight={700} sx={{ minWidth: 120, textAlign: 'center' }}>
                {MONTH_NAMES[viewMonth]} {viewYear}
              </Typography>
              <IconButton onClick={goToNextMonth} size="small" disabled={isCurrentMonth}><ChevronRightIcon /></IconButton>
              {!isCurrentMonth && (
                <Button size="small" variant="text" onClick={goToCurrentMonth}>Today</Button>
              )}
            </Stack>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
            <Button
              variant="contained" startIcon={<SaveIcon />}
              onClick={saveAll} disabled={saving || !selectedClient}
              sx={{ fontWeight: 600, mr: 1 }}
            >
              {saving ? <CircularProgress size={20} /> : 'Save All'}
            </Button>
            {selectedClient && clientData?.contact_email && clientData?.show_confirmation !== false && (
              <Button
                variant="outlined" color="info" startIcon={<MarkEmailReadIcon />}
                onClick={async () => {
                  const fromDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`;
                  const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate();
                  const toDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${lastDay}`;
                  try {
                    const r = await salesService.sendBulkConfirmation(selectedClient, fromDate, toDate);
                    setSuccess(r.message || 'Bulk confirmation sent');
                  } catch (e) {
                    setError(e.response?.data?.error || 'Failed to send');
                  }
                }}
                size="small"
              >
                Send All for Confirmation
              </Button>
            )}
            {selectedClient && (
              <Button
                variant="outlined" size="small" startIcon={<FileDownloadIcon />}
                onClick={async () => {
                  try {
                    const fromDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`;
                    const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate();
                    const toDate = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${lastDay}`;
                    const resp = await api.get('/sales/daily/export_excel/', {
                      params: { client: selectedClient, from_date: fromDate, to_date: toDate },
                      responseType: 'blob',
                    });
                    const url = window.URL.createObjectURL(new Blob([resp.data]));
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `sales_${MONTH_NAMES[viewMonth]}_${viewYear}.xlsx`;
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    window.URL.revokeObjectURL(url);
                  } catch { setError('Failed to export Excel'); }
                }}
                sx={{ ml: 1 }}
              >
                Export Excel
              </Button>
            )}
          </Grid>
        </Grid>
        {clientData && (
          <Stack direction="row" spacing={1} sx={{ mt: 1.5 }} alignItems="center">
            <Chip label={clientData.pricing_model} size="small" color="primary" variant="outlined" />
            {clientData.default_num_people > 0 && (
              <Chip label={`${clientData.default_num_people} people`} size="small" />
            )}
            <Chip label={`₹${clientData.total_sales_this_month?.toLocaleString() || 0} this month`} size="small" color="success" variant="outlined" />
            <Tooltip title="When off, hides the confirmation email button and Confirmed column — for clients who just need simple sales entry">
              <FormControlLabel
                control={
                  <Checkbox
                    size="small"
                    checked={clientData?.show_confirmation !== false}
                    onChange={async (e) => {
                      try {
                        const updated = await salesService.updateClient(selectedClient, { show_confirmation: e.target.checked });
                        setClientData(updated);
                      } catch {
                        setError('Failed to update confirmation setting');
                      }
                    }}
                  />
                }
                label={
                  <Typography variant="caption" color="text.secondary">
                    Confirmation workflow
                  </Typography>
                }
                sx={{ ml: 0.5 }}
              />
            </Tooltip>
          </Stack>
        )}
      </Paper>

      {/* Daily Entries Table */}
      {loading ? (
        <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>
      ) : selectedClient && entries.length > 0 ? (
        <Paper>
          <TableContainer sx={{ maxHeight: '70vh' }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, minWidth: 90 }}>Date</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 70 }}>Day</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 70 }}>
                    <Tooltip title="Toggle to mark any day as a holiday (Diwali, company day, etc.)">
                      <span>Holiday</span>
                    </Tooltip>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, minWidth: 300 }}>Items (click to edit)</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 100 }} align="right">Food ₹</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 80 }} align="right">Pack ₹</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 80 }} align="right">Courier ₹</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 100 }} align="right">Total ₹</TableCell>
                  {clientData?.show_confirmation !== false && (
                    <TableCell sx={{ fontWeight: 700, width: 90 }} align="center">Confirmed</TableCell>
                  )}
                  <TableCell width={40}></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries.map((entry, i) => (
                  <TableRow
                    key={entry.date}
                    sx={{
                      bgcolor: entry.is_holiday
                        ? '#f5f5f5'
                        : entry.has_dispute
                          ? '#fff3e0'  /* Amber — has open dispute */
                          : !entry._saved && !entry._new
                            ? '#fce4ec'  /* Pink — edited but not saved */
                            : entry._saved
                              ? '#f1f8e9'  /* Green — saved */
                              : 'inherit',
                      opacity: entry.is_holiday ? 0.6 : 1,
                      '&:hover': { bgcolor: entry.is_holiday ? '#eeeeee' : !entry._saved && !entry._new ? '#f8bbd0' : '#e3f2fd' },
                    }}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {new Date(entry.date + 'T00:00').toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ color: entry.is_holiday ? 'warning.main' : 'inherit' }}>
                        {getDayName(entry.date)?.slice(0, 3)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title={entry.is_holiday ? 'Mark as working day' : 'Mark as holiday'}>
                        <Switch
                          size="small" checked={entry.is_holiday}
                          onChange={(e) => {
                            const updated = [...entries];
                            updated[i] = {
                              ...updated[i],
                              is_holiday: e.target.checked,
                              holiday_reason: e.target.checked ? 'Holiday' : '',
                              _saved: false,
                            };
                            updated[i] = recalculateEntry(updated[i]);
                            setEntries(updated);
                          }}
                          color="warning"
                        />
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      {!entry.is_holiday ? (
                        <Box 
                          onClick={() => openItemsDialog(i)}
                          sx={{ 
                            p: 1, 
                            border: '1px dashed #ccc', 
                            borderRadius: 1,
                            cursor: 'pointer',
                            minHeight: 40,
                            display: 'flex',
                            alignItems: 'center',
                            '&:hover': { borderColor: 'primary.main', bgcolor: '#f5f5f5' },
                          }}
                        >
                          {entry.line_items?.length > 0 ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                              <RestaurantMenuIcon fontSize="small" color="primary" />
                              <Typography variant="body2" sx={{ flex: 1 }}>
                                {formatLineItemsDisplay(entry.line_items)}
                              </Typography>
                              <Chip 
                                label={`${entry.line_items.length} items`} 
                                size="small" 
                                color="primary" 
                                variant="outlined"
                              />
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <AddCircleOutlineIcon fontSize="small" />
                              Click to add items...
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Chip
                          label={entry.holiday_reason || 'Holiday'}
                          size="small"
                          color="warning"
                          variant="outlined"
                          sx={{ fontWeight: 600 }}
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600} color={entry.is_holiday ? 'text.secondary' : 'inherit'}>
                        {entry.is_holiday ? '—' : `₹${(parseFloat(entry.food_price_per_day) || 0).toLocaleString()}`}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {entry.is_holiday ? (
                        <Typography variant="body2" color="text.disabled">—</Typography>
                      ) : (
                        <TextField
                          size="small" type="number" value={entry.packing_charges || ''}
                          onChange={(e) => updateEntry(i, 'packing_charges', e.target.value)}
                          sx={{ width: 70 }}
                          inputProps={{ min: 0, style: { textAlign: 'right' } }}
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {entry.is_holiday ? (
                        <Typography variant="body2" color="text.disabled">—</Typography>
                      ) : (
                        <TextField
                          size="small" type="number" value={entry.courier_charges || ''}
                          onChange={(e) => updateEntry(i, 'courier_charges', e.target.value)}
                          sx={{ width: 70 }}
                          inputProps={{ min: 0, style: { textAlign: 'right' } }}
                        />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={700}
                        sx={{ color: entry.total_charge > 0 ? 'success.dark' : 'text.secondary' }}
                      >
                        ₹{(parseFloat(entry.total_charge) || 0).toLocaleString()}
                      </Typography>
                    </TableCell>
                    {clientData?.show_confirmation !== false && (
                    <TableCell align="center">
                      {!entry.is_holiday && entry._saved && (
                        <Stack direction="row" spacing={0.5} justifyContent="center" alignItems="center">
                          {entry.has_dispute && (
                            <Tooltip title="Open dispute — go to Disputes page to resolve">
                              <Chip
                                icon={<ReportProblemIcon />}
                                label="Dispute"
                                size="small"
                                color="warning"
                                variant="outlined"
                              />
                            </Tooltip>
                          )}
                          {!entry.has_dispute && (
                            entry.client_confirmed ? (
                              <Tooltip title={`Client confirmed${entry.client_confirmed_at ? ' at ' + new Date(entry.client_confirmed_at).toLocaleString() : ''}`}>
                                <Chip icon={<CheckCircleOutlineIcon />} label="Confirmed" size="small" color="success" variant="outlined" />
                              </Tooltip>
                            ) : (
                                    <Tooltip title="Send confirmation email — client can confirm or report an issue">
                                <IconButton size="small" color="info" onClick={async () => {
                                  try {
                                    const r = await salesService.sendConfirmation(entry.id, {
                                      show_prices: true,
                                      show_breakdown: false,
                                    });
                                    setSuccess(r.message || 'Confirmation email sent to client');
                                  } catch (e) {
                                    setError(e.response?.data?.error || 'Failed — does client have an email?');
                                  }
                                }}>
                                  <MarkEmailReadIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )
                          )}
                        </Stack>
                      )}
                      {!entry.is_holiday && !entry._saved && (
                        <Typography variant="caption" color="text.disabled">Save first</Typography>
                      )}
                    </TableCell>
                    )}
                    <TableCell>
                      <Stack direction="row" spacing={0}>
                        {!entry._saved && (entry.line_items?.length > 0 || entry.is_holiday || !entry._new) && (
                          <Tooltip title="Save this row">
                            <IconButton
                              size="small"
                              sx={{
                                color: 'white',
                                bgcolor: 'primary.main',
                                '&:hover': { bgcolor: 'primary.dark' },
                                width: 28, height: 28,
                              }}
                              onClick={async () => {
                              try {
                                const payload = {
                                  sales: [{
                                    client: selectedClient,
                                    date: entry.date,
                                    is_holiday: entry.is_holiday,
                                    holiday_reason: entry.holiday_reason || '',
                                    num_people: parseInt(entry.num_people) || 0,
                                    items_description: entry.items_description || serializeLineItems(entry.line_items || []),
                                    item_price: 0,
                                    food_price_per_day: parseFloat(entry.food_price_per_day) || 0,
                                    packing_charges: parseFloat(entry.packing_charges) || 0,
                                    courier_charges: parseFloat(entry.courier_charges) || 0,
                                  }],
                                };
                                const result = await salesService.bulkCreateSales(payload);
                                const updated = [...entries];
                                // Write back id from server so second save does update not insert
                                const savedSale = result?.sales?.[0];
                                updated[i] = { ...updated[i], _saved: true, _new: false, ...(savedSale?.id ? { id: savedSale.id } : {}) };
                                setEntries(updated);
                                setSuccess(`Saved ${entry.date}`);
                              } catch { setError('Failed to save'); }
                            }}>
                              <SaveIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {!entry.is_holiday && i > 0 && (
                          <Tooltip title="Copy from previous day">
                            <IconButton size="small" onClick={() => copyFromPrevious(i)}>
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
                {/* TOTAL ROW */}
                <TableRow sx={{ bgcolor: '#e8f5e9' }}>
                  <TableCell colSpan={8} align="right">
                    <Typography variant="subtitle1" fontWeight={700}>Month Total:</Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="h6" fontWeight={700} color="success.dark">
                      ₹{monthTotal.toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      ) : selectedClient ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">No entries yet. Select a client to start.</Typography>
        </Paper>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            {clients.length === 0 
              ? 'No clients found. Go to Clients page to add clients first.' 
              : 'Select a client to enter daily sales.'
            }
          </Typography>
        </Paper>
      )}

      {/* ==================== ITEMS DIALOG ==================== */}
      <Dialog 
        open={itemsDialogOpen} 
        onClose={closeItemsDialog} 
        maxWidth="md" 
        fullWidth
        PaperProps={{ sx: { minHeight: '50vh' } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <RestaurantMenuIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Edit Menu Items
              </Typography>
            </Box>
            {editingEntryIndex !== null && (
              <Chip 
                label={new Date(entries[editingEntryIndex]?.date + 'T00:00').toLocaleDateString('en-IN', { 
                  day: '2-digit', month: 'short', year: 'numeric' 
                })}
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Add menu items with quantity and unit price. Total is calculated automatically.
          </Typography>
        </DialogTitle>
        
        <Divider />
        
        <DialogContent sx={{ pt: 2 }}>
          {/* Line Items Table */}
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, width: '40%' }}>Item Name</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: '15%' }} align="center">Qty</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: '20%' }} align="right">Unit Price ₹</TableCell>
                  <TableCell sx={{ fontWeight: 700, width: '20%' }} align="right">Total ₹</TableCell>
                  <TableCell width={50}></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {editingLineItems.map((item, idx) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <TextField
                        size="small"
                        fullWidth
                        value={item.item_name}
                        onChange={(e) => updateLineItem(idx, 'item_name', e.target.value)}
                        placeholder="e.g. Chapathi, Phulka, Dal Fry..."
                        autoFocus={idx === editingLineItems.length - 1 && !item.item_name}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <TextField
                        size="small"
                        type="number"
                        value={item.quantity || ''}
                        onChange={(e) => updateLineItem(idx, 'quantity', parseInt(e.target.value) || 0)}
                        sx={{ width: 70 }}
                        inputProps={{ min: 1, style: { textAlign: 'center' } }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <TextField
                        size="small"
                        type="number"
                        value={item.unit_price || ''}
                        onChange={(e) => updateLineItem(idx, 'unit_price', parseFloat(e.target.value) || 0)}
                        sx={{ width: 100 }}
                        inputProps={{ min: 0, step: 0.5, style: { textAlign: 'right' } }}
                        InputProps={{ startAdornment: <Typography color="text.secondary" sx={{ mr: 0.5 }}>₹</Typography> }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography fontWeight={600}>
                        ₹{((item.quantity || 0) * (item.unit_price || 0)).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="error" onClick={() => deleteLineItem(idx)}>
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                
                {/* Empty state */}
                {editingLineItems.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary" gutterBottom>
                        No items yet. Click "Add Item" to start.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                
                {/* Total Row */}
                {editingLineItems.length > 0 && (
                  <TableRow sx={{ bgcolor: '#e3f2fd' }}>
                    <TableCell colSpan={3} align="right">
                      <Typography fontWeight={700}>Food Total:</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="h6" fontWeight={700} color="primary.main">
                        ₹{editingTotal.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell />
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Add Item Button */}
          <Box sx={{ mt: 2 }}>
            <Button 
              startIcon={<AddCircleOutlineIcon />} 
              onClick={addLineItem}
              variant="outlined"
            >
              Add Item
            </Button>
          </Box>
        </DialogContent>
        
        <Divider />
        
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button onClick={closeItemsDialog} color="inherit">
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={saveLineItems}
            disabled={editingLineItems.filter(i => i.item_name.trim()).length === 0}
          >
            Save Items
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
