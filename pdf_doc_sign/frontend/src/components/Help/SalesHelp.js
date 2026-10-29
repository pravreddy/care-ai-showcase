import React from 'react';
import {
  Typography, Paper, Box, Stepper, Step, StepLabel, StepContent,
  Grid, Card, CardContent, Chip, Divider,
} from '@mui/material';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import PeopleIcon from '@mui/icons-material/People';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import EmailIcon from '@mui/icons-material/Email';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const CLIENT_STEPS = [
  { label: 'Go to Clients', description: 'From the sidebar, click "Clients" under Sales & Invoicing. This is where you manage all your delivery clients (restaurants, offices, hostels, etc.).' },
  { label: 'Add a new client', description: 'Click "Add Client" and fill in the details: client name, contact person, email, phone, and delivery address. Choose the pricing model that suits your arrangement — Itemised (list items + prices each day), Per Head (fixed rate × number of people), or Fixed Daily (same amount every day).' },
  { label: 'Set default charges', description: 'Configure default packing and courier charges for this client. These will auto-fill each day when you log sales, saving you time. You can also set the default number of people (meals) per day.' },
];

const SALES_STEPS = [
  { label: 'Go to Daily Sales', description: 'From the sidebar, click "Daily Sales". This is your daily log — record what you delivered, to whom, and for how much.' },
  { label: 'Select client and date', description: 'Choose the client from the dropdown and pick the date. If it\'s a weekend or holiday, you can mark it accordingly — no charges are logged.' },
  { label: 'Add line items', description: 'Click to add food items with name, quantity, and unit price. For example: "4x Chapathi @10, 2x Dal Fry @20". The food total is calculated automatically as the sum of all line items.' },
  { label: 'Packing and courier charges', description: 'Packing and courier charges auto-fill from the client defaults. You can override them for any specific day if needed.' },
  { label: 'Copy from previous day', description: 'Serving the same menu as yesterday? Click "Copy from previous day" to duplicate the last working day\'s entry — items, quantities, prices, and charges. Just adjust what changed.' },
  { label: 'Save', description: 'Click Save to store the entry. You can edit any day\'s entry later if there\'s a correction.' },
];

const INVOICE_STEPS = [
  { label: 'Go to Invoices', description: 'From the sidebar, click "Invoices" under Sales & Invoicing.' },
  { label: 'Select client and date range', description: 'Choose the client and set the period — typically a calendar month (e.g., 1 Mar 2026 to 31 Mar 2026). Click "Get Summary" to see the totals before generating.' },
  { label: 'Review the summary', description: 'The summary shows working days, total food charges, packing, courier, and the grand total. You can add GST percentage if applicable, and add any notes (payment terms, bank details, etc.).' },
  { label: 'Generate invoice', description: 'Click "Generate Invoice" to create a professional PDF invoice. The invoice includes your organisation details, client details, a daily breakdown table with all line items formatted clearly, and totals with GST.' },
  { label: 'Send or download', description: 'Download the PDF directly, or click the email icon to send it to the client\'s email automatically. The invoice is numbered sequentially (INV-2026-03-00001) and stored for your records.' },
];

export default function SalesHelp() {
  return (
    <HelpLayout>
      <SEO
        title="Sales Tracking & Invoicing Guide"
        description="Track daily food deliveries, manage clients, and generate monthly invoices with GST support. Built for restaurants, caterers, and delivery businesses."
        path="/help/sales-invoicing"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        Sales Tracking & Invoicing
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        SignSimple includes a built-in sales tracking and invoicing module — designed for restaurants,
        caterers, food delivery services, and small businesses that need to track daily deliveries
        and generate monthly invoices.
      </Typography>

      <Paper sx={{ p: 3, mb: 4, bgcolor: '#fff3e0', borderLeft: '4px solid #f57c00' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Who is this for?</Typography>
        <Typography variant="body2" color="text.secondary">
          This module is ideal for anyone who delivers meals, catering, or products on a daily basis
          and needs to track what was delivered, calculate charges, and generate monthly invoices.
          It replaces spreadsheets and manual record-keeping with a simple, mobile-friendly tool.
        </Typography>
      </Paper>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[
          { icon: <PeopleIcon />, title: 'Client Management', desc: 'Add clients with delivery addresses, pricing models, and default charges. Supports itemised, per-head, and fixed daily pricing.', color: '#1565c0' },
          { icon: <PointOfSaleIcon />, title: 'Daily Sales Log', desc: 'Record food items, quantities, prices, packing, and courier charges each day. Copy from previous day to save time.', color: '#2e7d32' },
          { icon: <ReceiptLongIcon />, title: 'Invoice Generation', desc: 'Generate professional PDF invoices with daily breakdown, GST support, and automatic numbering (INV-YYYY-MM-XXXXX).', color: '#7b1fa2' },
          { icon: <EmailIcon />, title: 'Email Invoices', desc: 'Send invoices directly to clients via email, or download the PDF to share manually.', color: '#e65100' },
        ].map((f) => (
          <Grid item xs={12} sm={6} key={f.title}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: f.color }}>
                  {f.icon}
                  <Typography variant="subtitle1" fontWeight={600}>{f.title}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">{f.desc}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        <PeopleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Step 1: Set Up Your Clients
      </Typography>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Stepper orientation="vertical">
          {CLIENT_STEPS.map((step, index) => (
            <Step key={index} active expanded>
              <StepLabel><Typography variant="subtitle1" fontWeight={600}>{step.label}</Typography></StepLabel>
              <StepContent><Typography variant="body2" color="text.secondary" sx={{ pb: 2 }}>{step.description}</Typography></StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Paper sx={{ p: 3, mb: 4, bgcolor: '#e3f2fd' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Pricing Models Explained</Typography>
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <Chip label="Itemised" size="small" color="primary" sx={{ mr: 1 }} />
            List each food item with quantity and price daily. Best for varied menus. Example: 4x Chapathi @Rs.10, 2x Dal @Rs.20.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <Chip label="Per Head" size="small" color="secondary" sx={{ mr: 1 }} />
            Fixed rate per person per day. Best for hostels, offices with a set meal price. Example: Rs.50/head × 10 people = Rs.500/day.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <Chip label="Fixed Daily" size="small" sx={{ mr: 1 }} />
            Same flat amount charged every working day. Best for simple arrangements. Example: Rs.500/day regardless of items.
          </Typography>
        </Box>
      </Paper>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        <PointOfSaleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Step 2: Log Your Daily Sales
      </Typography>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Stepper orientation="vertical">
          {SALES_STEPS.map((step, index) => (
            <Step key={index} active expanded>
              <StepLabel><Typography variant="subtitle1" fontWeight={600}>{step.label}</Typography></StepLabel>
              <StepContent><Typography variant="body2" color="text.secondary" sx={{ pb: 2 }}>{step.description}</Typography></StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Paper sx={{ p: 3, mb: 4, bgcolor: '#e8f5e9' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Tips for Daily Logging</Typography>
        <Typography variant="body2" color="text.secondary">
          Log sales daily rather than at the end of the month — it's faster and more accurate.
          Use "Copy from previous day" when the menu is the same.
          Weekends and holidays are automatically marked with zero charges.
          You can go back and edit any day's entry if you made a mistake.
        </Typography>
      </Paper>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        <ReceiptLongIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Step 3: Generate & Send Invoices
      </Typography>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Stepper orientation="vertical">
          {INVOICE_STEPS.map((step, index) => (
            <Step key={index} active expanded>
              <StepLabel><Typography variant="subtitle1" fontWeight={600}>{step.label}</Typography></StepLabel>
              <StepContent><Typography variant="body2" color="text.secondary" sx={{ pb: 2 }}>{step.description}</Typography></StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Paper sx={{ p: 3, mb: 4, bgcolor: '#fce4ec' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Invoice Format</Typography>
        <Typography variant="body2" color="text.secondary">
          Each invoice PDF includes: your organisation name and address, client details,
          a day-by-day breakdown showing each food item (e.g., "4x Chapathi @10, 2x Dal Fry @20"),
          packing and courier charges per day, working days count, totals, optional GST calculation,
          and your custom notes. Invoices are numbered sequentially and branded with your organisation details.
        </Typography>
      </Paper>

      <Divider sx={{ my: 4 }} />

      <Paper sx={{ p: 4, bgcolor: '#f5f5f5' }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>How to Get Access</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          The Sales & Invoicing module is available to organisation members with sales access enabled.
        </Typography>
        <Box component="ol" sx={{ pl: 3 }}>
          <Typography component="li" variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
            <strong>Create or join an organisation</strong> — go to Organisation in the sidebar and set up your business (name, address, company number).
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
            <strong>Enable sales access</strong> — the organisation admin enables the Sales module for the organisation.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
            <strong>Add team members</strong> — invite staff to your organisation. They'll see the Sales & Invoicing section in their sidebar.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 0, color: 'text.secondary' }}>
            <strong>Start logging</strong> — add your clients, log daily sales, and generate invoices at month-end.
          </Typography>
        </Box>
      </Paper>

      <Box sx={{ mt: 4, p: 3, bgcolor: '#e3f2fd', borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Questions about Sales & Invoicing?</Typography>
        <Typography variant="body2" color="text.secondary">
          Contact us at <strong>support@signsimple.co.uk</strong> — we're happy to help you get set up.
        </Typography>
      </Box>
    </HelpLayout>
  );
}
