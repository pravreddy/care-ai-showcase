import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Typography, TextField, Button, Grid, Box,
  Select, MenuItem, FormControl, InputLabel, Alert, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Stack, Divider, FormControlLabel, Checkbox,
} from '@mui/material';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import EmailIcon from '@mui/icons-material/Email';
import DownloadIcon from '@mui/icons-material/Download';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { salesService } from '../../services/api';

export default function InvoiceGenerator() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [taxPercentage, setTaxPercentage] = useState(0);
  const [currency, setCurrency] = useState('INR');
  const [notes, setNotes] = useState('');

  // Invoice content options
  const [includeDailyBreakdown, setIncludeDailyBreakdown] = useState(true);
  const [includePackingCharges, setIncludePackingCharges] = useState(true);
  const [includeCourierCharges, setIncludeCourierCharges] = useState(true);
  const [includeItemDetail, setIncludeItemDetail] = useState(true);
  const [attachExcel, setAttachExcel] = useState(false);

  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [invoice, setInvoice] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [invoices, setInvoices] = useState([]);

  useEffect(() => {
    salesService.getClients().then((data) => setClients(data.results || data)).catch(() => {});
    salesService.getInvoices().then((data) => setInvoices(data.results || data)).catch(() => {});
  }, []);

  // Auto-set currency when client changes
  useEffect(() => {
    if (!selectedClient) return;
    const client = clients.find(c => c.id === selectedClient);
    if (client?.suggested_currency) {
      setCurrency(client.suggested_currency);
    }
  }, [selectedClient, clients]);

  // Auto-set date range to current month
  useEffect(() => {
    const now = new Date();
    const firstDay = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    const lastDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${lastDay}`;
    setFromDate(firstDay);
    setToDate(lastDate);
  }, []);

  const loadSummary = async () => {
    if (!selectedClient || !fromDate || !toDate) return;
    setLoading(true);
    setError('');
    try {
      const data = await salesService.getSummary(selectedClient, fromDate, toDate);
      setSummary(data);
    } catch {
      setError('Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedClient && fromDate && toDate) loadSummary();
  }, [selectedClient, fromDate, toDate]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setSuccess('');
    try {
      const result = await salesService.generateInvoice({
        client_id: selectedClient,
        from_date: fromDate,
        to_date: toDate,
        tax_percentage: parseFloat(taxPercentage) || 0,
        currency,
        notes,
        include_daily_breakdown: includeDailyBreakdown,
        include_packing_charges: includePackingCharges,
        include_courier_charges: includeCourierCharges,
        include_item_detail: includeItemDetail,
        attach_excel: attachExcel,
      });
      setInvoice(result);
      setSuccess(`Invoice ${result.invoice_number} generated! Grand Total: ₹${parseFloat(result.grand_total).toLocaleString()}`);
      // Refresh invoice list
      salesService.getInvoices().then((data) => setInvoices(data.results || data)).catch(() => {});
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate invoice');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (invId) => {
    try {
      const blob = await salesService.downloadInvoice(invId);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${invId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      setError('Failed to download');
    }
  };

  const handleSendEmail = async (invId) => {
    try {
      const result = await salesService.sendInvoiceEmail(invId);
      setSuccess(result.message);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send email');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Invoice Generator
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Select a client and date range to generate a PDF invoice from daily sales records.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Controls */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Client</InputLabel>
              <Select value={selectedClient} onChange={(e) => setSelectedClient(e.target.value)} label="Client">
                {clients.map((c) => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} md={2}>
            <TextField fullWidth type="date" label="From Date" value={fromDate}
              onChange={(e) => setFromDate(e.target.value)} InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={6} md={2}>
            <TextField fullWidth type="date" label="To Date" value={toDate}
              onChange={(e) => setToDate(e.target.value)} InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={4} md={1.5}>
            <FormControl fullWidth>
              <InputLabel>Currency</InputLabel>
              <Select value={currency} onChange={(e) => setCurrency(e.target.value)} label="Currency">
                <MenuItem value="INR">Rs. (INR)</MenuItem>
                <MenuItem value="GBP">£ (GBP)</MenuItem>
                <MenuItem value="USD">$ (USD)</MenuItem>
                <MenuItem value="EUR">€ (EUR)</MenuItem>
                <MenuItem value="CAD">CAD</MenuItem>
                <MenuItem value="AUD">AUD</MenuItem>
              </Select>
            </FormControl>
            {selectedClient && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                Auto-set from client country
              </Typography>
            )}
          </Grid>
          <Grid item xs={4} md={1.5}>
            <TextField fullWidth type="number" label="GST %" value={taxPercentage}
              onChange={(e) => setTaxPercentage(e.target.value)} inputProps={{ min: 0, max: 28, step: 0.5 }} />
          </Grid>
          <Grid item xs={6} md={3}>
            <Button fullWidth variant="contained" size="large" startIcon={<PictureAsPdfIcon />}
              onClick={handleGenerate} disabled={generating || !selectedClient}
              sx={{ py: 1.5, fontWeight: 700 }}
            >
              {generating ? <CircularProgress size={20} /> : 'Generate Invoice'}
            </Button>
          </Grid>
        </Grid>
        <TextField fullWidth label="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)}
          multiline rows={2} sx={{ mt: 2 }} placeholder="Any additional notes for the invoice..." />

        {/* Invoice Content Options */}
        <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 2 }}>
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>What to include in the invoice:</Typography>
          <Grid container spacing={0}>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={<Checkbox checked={includeDailyBreakdown} onChange={(e) => setIncludeDailyBreakdown(e.target.checked)} />}
                label="Include daily breakdown (show each day's items and totals)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={<Checkbox checked={includeItemDetail} onChange={(e) => setIncludeItemDetail(e.target.checked)} disabled={!includeDailyBreakdown} />}
                label='Include item detail ("5x Chapathi @10" vs just food total)'
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={<Checkbox checked={includePackingCharges} onChange={(e) => setIncludePackingCharges(e.target.checked)} />}
                label="Include packing charges"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={<Checkbox checked={includeCourierCharges} onChange={(e) => setIncludeCourierCharges(e.target.checked)} />}
                label="Include courier/delivery charges"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={<Checkbox checked={attachExcel} onChange={(e) => setAttachExcel(e.target.checked)} />}
                label="Attach Excel breakdown (spreadsheet with daily data sent alongside PDF when emailing)"
              />
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* Summary Preview */}
      {loading && <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress /></Box>}
      {summary && !loading && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>Preview Summary</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={2}><Typography variant="body2" color="text.secondary">Working Days</Typography><Typography variant="h5" fontWeight={700}>{summary.working_days}</Typography></Grid>
            <Grid item xs={6} md={2}><Typography variant="body2" color="text.secondary">Holidays</Typography><Typography variant="h5">{summary.holidays}</Typography></Grid>
            <Grid item xs={6} md={2}><Typography variant="body2" color="text.secondary">Food Total</Typography><Typography variant="h5">₹{summary.total_food?.toLocaleString()}</Typography></Grid>
            <Grid item xs={6} md={2}><Typography variant="body2" color="text.secondary">Packing</Typography><Typography variant="h5">₹{summary.total_packing?.toLocaleString()}</Typography></Grid>
            <Grid item xs={6} md={2}><Typography variant="body2" color="text.secondary">Courier</Typography><Typography variant="h5">₹{summary.total_courier?.toLocaleString()}</Typography></Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="body2" color="text.secondary">Grand Total</Typography>
              <Typography variant="h4" fontWeight={800} color="success.dark">₹{summary.grand_total?.toLocaleString()}</Typography>
            </Grid>
          </Grid>
          {summary.open_disputes > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {summary.open_disputes} open dispute(s) in this period. Consider resolving before invoicing.
            </Alert>
          )}
        </Paper>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Recent Invoices */}
      <Typography variant="h6" fontWeight={600} gutterBottom>Recent Invoices</Typography>
      {invoices.length > 0 ? (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Invoice #</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Client</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Period</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Days</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="right">Total</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell><Typography fontWeight={600}>{inv.invoice_number}</Typography></TableCell>
                  <TableCell>{inv.client_name}</TableCell>
                  <TableCell>{inv.from_date} → {inv.to_date}</TableCell>
                  <TableCell>{inv.working_days}</TableCell>
                  <TableCell align="right"><Typography fontWeight={700}>₹{parseFloat(inv.grand_total).toLocaleString()}</Typography></TableCell>
                  <TableCell>
                    <Chip
                      label={inv.status} size="small"
                      color={inv.status === 'PAID' ? 'success' : inv.status === 'SENT' ? 'info' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5}>
                      <Button size="small" startIcon={<DownloadIcon />} onClick={() => handleDownload(inv.id)}>PDF</Button>
                      <Button size="small" startIcon={<EmailIcon />} onClick={() => handleSendEmail(inv.id)}>Email</Button>
                      {inv.status !== 'PAID' && (
                        <Button size="small" startIcon={<CheckCircleIcon />} color="success"
                          onClick={async () => {
                            await salesService.markInvoicePaid(inv.id);
                            salesService.getInvoices().then((data) => setInvoices(data.results || data));
                          }}
                        >Paid</Button>
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No invoices generated yet.</Typography>
        </Paper>
      )}
    </Container>
  );
}
