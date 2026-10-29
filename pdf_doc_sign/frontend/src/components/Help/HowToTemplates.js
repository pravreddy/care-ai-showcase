import React from 'react';
import { Typography, Paper, Stepper, Step, StepLabel, StepContent, Box } from '@mui/material';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const CREATE_STEPS = [
  {
    label: 'Prepare a document with fields',
    description: 'Upload a PDF and place your signature fields (signature, date, name, initials) using the field editor. Position them exactly where you want signers to sign.',
  },
  {
    label: 'Save as template',
    description: 'On the document detail page, click "Save as Template". Give it a name and optionally choose a category (NDA, Contract, Agreement, etc.). The PDF and all field positions are saved together.',
  },
  {
    label: 'Find it in your library',
    description: 'Go to Templates in the sidebar to see all your saved templates, plus any system templates available to everyone.',
  },
];

const USE_STEPS = [
  {
    label: 'Open your template library',
    description: 'Navigate to Templates from the sidebar. You\'ll see your saved templates as cards, filterable by category.',
  },
  {
    label: 'Click "Use Template"',
    description: 'Click the "Use Template" button on any template card. Enter a title for the new document (e.g., "NDA — John Smith"). A new draft document is created automatically.',
  },
  {
    label: 'Fields are pre-placed',
    description: 'The new document has all signature fields already positioned — exactly where you placed them in the original. You can adjust them if needed using the field editor, then send for signing.',
  },
];

export default function HowToTemplates() {
  return (
    <HelpLayout>
      <SEO
        title="How to Use Document Templates"
        description="Save time with reusable PDF templates. Pre-place signature fields once and reuse them for contracts, NDAs, and agreements."
        path="/help/how-to-templates"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How to Use Templates
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Save time by creating reusable templates — the PDF and signature field positions are saved together,
        so you don't have to place fields every time.
      </Typography>

      <Typography variant="h5" fontWeight={600} sx={{ mt: 2, mb: 2 }}>
        Creating a Template
      </Typography>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Stepper orientation="vertical">
          {CREATE_STEPS.map((step, index) => (
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

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        Using a Template
      </Typography>
      <Paper sx={{ p: 4 }}>
        <Stepper orientation="vertical">
          {USE_STEPS.map((step, index) => (
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

      <Paper sx={{ p: 3, mt: 4, bgcolor: '#e3f2fd' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Template Categories
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Organise your templates by category: NDA, Contract, Invoice, Proposal, Agreement, or Other.
          Use the filter buttons on the Templates page to quickly find what you need.
        </Typography>
      </Paper>
    </HelpLayout>
  );
}
