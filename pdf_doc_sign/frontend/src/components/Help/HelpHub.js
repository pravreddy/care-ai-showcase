import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography, Grid, Card, CardContent, CardActionArea, Box, Paper, Stepper,
  Step, StepLabel, StepContent, Divider,
} from '@mui/material';
import DrawIcon from '@mui/icons-material/Draw';
import SendIcon from '@mui/icons-material/Send';
import FileCopyIcon from '@mui/icons-material/FileCopy';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import CreateIcon from '@mui/icons-material/Create';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const GUIDES = [
  {
    title: 'How to Sign a Document',
    description: 'Received a document to sign? Learn how to review, sign, and submit in minutes.',
    icon: <DrawIcon sx={{ fontSize: 40 }} />,
    path: '/help/how-to-sign',
    color: '#2e7d32',
  },
  {
    title: 'How to Send for Signing',
    description: 'Upload a PDF, place signature fields, add signers, and send — step by step.',
    icon: <SendIcon sx={{ fontSize: 40 }} />,
    path: '/help/how-to-send',
    color: '#1565c0',
  },
  {
    title: 'How to Create Signatures',
    description: 'Three ways to create your signature: draw, type, or upload an image.',
    icon: <CreateIcon sx={{ fontSize: 40 }} />,
    path: '/help/how-to-create-signatures',
    color: '#00838f',
  },
  {
    title: 'How to Use Fields',
    description: 'Place signature, date, name, initials, and text fields on your documents.',
    icon: <ViewModuleIcon sx={{ fontSize: 40 }} />,
    path: '/help/how-to-use-fields',
    color: '#ad1457',
  },
  {
    title: 'How to Use Templates',
    description: 'Save time by creating reusable templates with pre-placed signature fields.',
    icon: <FileCopyIcon sx={{ fontSize: 40 }} />,
    path: '/help/how-to-templates',
    color: '#f57c00',
  },
  {
    title: 'Sales & Invoicing',
    description: 'Track daily food deliveries, manage clients, and generate monthly invoices with GST support.',
    icon: <RestaurantMenuIcon sx={{ fontSize: 40 }} />,
    path: '/help/sales-invoicing',
    color: '#e65100',
  },
  {
    title: 'Frequently Asked Questions',
    description: 'Common questions about security, legal validity, pricing, and more.',
    icon: <HelpOutlineIcon sx={{ fontSize: 40 }} />,
    path: '/help/faq',
    color: '#7b1fa2',
  },
];

const QUICK_START = [
  { label: 'Create a free account', description: 'Sign up at signsimple.co.uk — no credit card required.' },
  { label: 'Upload a PDF', description: 'Go to Documents → Upload and select your file (up to 10 MB).' },
  { label: 'Place signature fields', description: 'Click "Place Fields" and drag signature/date/name fields onto the PDF.' },
  { label: 'Add signers and send', description: 'Click "Send for Signing", enter names and emails, and hit send.' },
  { label: 'Track and download', description: 'Monitor progress, send reminders, and download the signed PDF when complete.' },
];

export default function HelpHub() {
  const navigate = useNavigate();

  return (
    <HelpLayout>
      <SEO
        title="Help Centre – How to Sign, Send & Use Templates"
        description="Learn how to sign documents, send for signing, use templates, and more with SignSimple. Step-by-step guides for UK e-signatures."
        path="/help"
        keywords="signsimple help, how to sign documents, e-signature guide, UK electronic signature help"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How can we help?
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Get started with SignSimple — free electronic signatures for individuals and businesses.
      </Typography>

      {/* Quick Start */}
      <Paper sx={{ p: 4, mb: 5, bgcolor: '#f5f5f5' }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Quick Start Guide
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Send your first document for signing in under 5 minutes.
        </Typography>
        <Stepper orientation="vertical">
          {QUICK_START.map((step, index) => (
            <Step key={index} active expanded>
              <StepLabel>
                <Typography variant="subtitle2" fontWeight={600}>{step.label}</Typography>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary">{step.description}</Typography>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Divider sx={{ mb: 4 }} />

      {/* Detailed Guides */}
      <Typography variant="h5" fontWeight={600} sx={{ mb: 3 }}>
        Detailed Guides
      </Typography>

      <Grid container spacing={3}>
        {GUIDES.map((guide) => (
          <Grid item xs={12} sm={6} md={4} key={guide.path}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardActionArea onClick={() => navigate(guide.path)} sx={{ p: 3, height: '100%' }}>
                <CardContent sx={{ p: 0 }}>
                  <Box sx={{ color: guide.color, mb: 2 }}>{guide.icon}</Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {guide.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {guide.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Use Cases */}
      <Paper sx={{ p: 4, mt: 5, bgcolor: '#e8f5e9' }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Who Uses SignSimple?
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {[
            { title: 'Small Businesses', desc: 'Contracts, NDAs, and agreements — signed online without printing.' },
            { title: 'HR & Recruitment', desc: 'Offer letters, onboarding forms, and policies — bulk send to new hires.' },
            { title: 'Real Estate', desc: 'Tenancy agreements, property contracts, and landlord forms.' },
            { title: 'Legal', desc: 'Client engagement letters, settlement agreements, and consent forms.' },
            { title: 'Freelancers', desc: 'Project agreements, invoices, and service contracts.' },
            { title: 'Food & Catering', desc: 'Daily sales tracking, delivery agreements, and supplier contracts.' },
          ].map((uc) => (
            <Grid item xs={12} sm={6} md={4} key={uc.title}>
              <Box>
                <Typography variant="subtitle2" fontWeight={600}>{uc.title}</Typography>
                <Typography variant="body2" color="text.secondary">{uc.desc}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Support */}
      <Box sx={{ mt: 5, p: 3, bgcolor: '#e3f2fd', borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Need more help?
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Contact us at <strong>support@signsimple.co.uk</strong> — we typically respond within 24 hours.
        </Typography>
      </Box>
    </HelpLayout>
  );
}
