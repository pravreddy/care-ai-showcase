import React from 'react';
import { Typography, Paper, Box, Stepper, Step, StepLabel, StepContent } from '@mui/material';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const STEPS = [
  {
    label: 'Open the signing link',
    description: 'You\'ll receive an email from SignSimple with a green "Review & Sign" button. Click it to open the secure signing page. No account or login is required — the link is unique to you.',
  },
  {
    label: 'Review the document',
    description: 'The document opens in a full PDF preview. Scroll through all pages to read the content. Green highlighted areas show where your signature is needed.',
  },
  {
    label: 'Add your signature',
    description: 'Click on any green signature field, or use the signature section below the document. You can draw your signature with your mouse or finger, type your name to generate a signature, or upload an image of your handwritten signature.',
  },
  {
    label: 'Submit',
    description: 'Once all required fields are filled, click "Sign Document". You\'ll see a confirmation that your signature has been recorded. The document owner will be notified automatically.',
  },
  {
    label: 'You\'re done',
    description: 'Once all parties have signed, everyone receives a notification email. The document owner can download the completed signed PDF with an audit trail certificate.',
  },
];

export default function HowToSign() {
  return (
    <HelpLayout>
      <SEO
        title="How to Sign a Document"
        description="Step-by-step guide to signing documents with SignSimple. Draw, type or upload your signature — no account needed. Legally binding under UK law."
        path="/help/how-to-sign"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How to Sign a Document
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Someone sent you a document to sign? Here's what to do — it takes less than 2 minutes.
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

      <Paper sx={{ p: 3, mt: 4, bgcolor: '#fff3e0' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Tips
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your signing link expires after 90 days. If it has expired, ask the sender to resend the document.
          Your signature is legally binding — treat it the same as signing a paper document.
          If you have concerns about the document content, contact the sender directly before signing.
        </Typography>
      </Paper>
    </HelpLayout>
  );
}
