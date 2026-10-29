import React from 'react';
import { Typography, Paper, Stepper, Step, StepLabel, StepContent, Box, Chip } from '@mui/material';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const STEPS = [
  {
    label: 'Upload your document',
    description: 'Go to Documents → Upload and select a PDF file (up to 10 MB). The document is automatically compressed and stored securely. You\'ll see a preview immediately after upload.',
  },
  {
    label: 'Place signature fields',
    description: 'Click "Place Fields" on the document detail page. The PDF opens in an editor where you can drag signature, date, name, and initials fields onto specific positions on any page. Use the sidebar to pick the field type, or right-click on the PDF to add a field. Each field is assigned to a signer (Signer 1, Signer 2, etc.).',
  },
  {
    label: 'Add signers and send',
    description: 'Click "Send for Signing" and enter each signer\'s name and email address. You can add multiple signers — each will receive their own signing link via email. Once sent, the document status changes to "Pending".',
  },
  {
    label: 'Track progress',
    description: 'On the document detail page, you can see which signers have completed and which are still pending. You\'ll receive an email notification each time a signer completes. Use the "Remind All" button or the bell icon next to each signer to send reminder emails.',
  },
  {
    label: 'Download the signed document',
    description: 'Once all signers have completed, the document status changes to "Signed". Click "Download" to get the signed PDF with signatures embedded at the exact positions. Click "Audit Trail" to download a certificate with SHA-256 hash, signer details, IP addresses, and timestamps.',
  },
];

export default function HowToSend() {
  return (
    <HelpLayout>
      <SEO
        title="How to Send Documents for Signing"
        description="Learn how to upload PDFs, place signature fields, add signers, and send for e-signature with SignSimple. Complete step-by-step guide."
        path="/help/how-to-send"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How to Send a Document for Signing
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Send a document to one or more people for electronic signature — the complete workflow.
      </Typography>

      <Paper sx={{ p: 4 }}>
        <Stepper orientation="vertical">
          {STEPS.map((step, index) => (
            <Step key={index} active expanded>
              <StepLabel>
                <Typography variant="subtitle1" fontWeight={600}>{step.label}</Typography>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary" sx={{ pb: 2 }}>
                  {step.description}
                </Typography>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Paper sx={{ p: 3, mt: 4, bgcolor: '#e8f5e9' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Bulk Send
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Need to send the same document to many people (e.g., an NDA to 20 new hires)?
          Use the <Chip label="Bulk Send" size="small" color="info" /> button on the document detail page.
          Enter up to 100 recipients — each gets their own independent copy to sign.
        </Typography>
      </Paper>
    </HelpLayout>
  );
}
