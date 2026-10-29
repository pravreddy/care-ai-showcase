import React from 'react';
import {
  Typography, Paper, Box, Grid, Card, CardContent, Chip,
} from '@mui/material';
import DrawIcon from '@mui/icons-material/Draw';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import PersonIcon from '@mui/icons-material/Person';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import GestureIcon from '@mui/icons-material/Gesture';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const FIELD_TYPES = [
  {
    icon: <DrawIcon />,
    name: 'Signature',
    color: '#2e7d32',
    description: 'The primary field — signers draw, type, or upload their signature here.',
    autoFill: 'No — signer must provide their signature manually.',
    common: 'Every signing document needs at least one signature field.',
  },
  {
    icon: <GestureIcon />,
    name: 'Initials',
    color: '#1565c0',
    description: 'A smaller signature field for initials (e.g., on each page of a multi-page contract).',
    autoFill: 'Uses the same signature image as the main Signature field, but displayed smaller.',
    common: 'Useful for contracts where each page needs to be initialled.',
  },
  {
    icon: <PersonIcon />,
    name: 'Full Name',
    color: '#7b1fa2',
    description: 'Displays the signer\'s full name as text (not an image).',
    autoFill: 'Yes — auto-filled from the signer\'s name when they sign.',
    common: 'Place next to or below a signature field for printed name.',
  },
  {
    icon: <CalendarTodayIcon />,
    name: 'Date',
    color: '#e65100',
    description: 'Displays the date when the signer completed their signature.',
    autoFill: 'Yes — auto-filled with the signing date (e.g., "28 Mar 2026").',
    common: 'Place next to signature fields for a dated record.',
  },
  {
    icon: <TextFieldsIcon />,
    name: 'Text',
    color: '#616161',
    description: 'A free-text field where signers can type custom content (job title, company name, etc.).',
    autoFill: 'No — signer fills this in manually.',
    common: 'Useful for title, company, address, or other variable information.',
  },
];

export default function HowToUseFields() {
  return (
    <HelpLayout>
      <SEO
        title="How to Use Signature Fields in Documents"
        description="Learn how to place signature, date, name, initials and text fields on your PDF documents with SignSimple."
        path="/help/how-to-use-fields"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How to Use Fields in Your Documents
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Fields are the interactive elements you place on your PDF — they define where signers
        need to sign, initial, type their name, or enter a date. Here's how to use each type.
      </Typography>

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        Field Types
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        {FIELD_TYPES.map((field) => (
          <Grid item xs={12} key={field.name}>
            <Card variant="outlined">
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                  <Box sx={{ color: field.color }}>{field.icon}</Box>
                  <Typography variant="h6" fontWeight={600}>{field.name}</Typography>
                  <Chip label={field.autoFill.startsWith('Yes') ? 'Auto-fill' : 'Manual'} 
                    size="small" 
                    color={field.autoFill.startsWith('Yes') ? 'success' : 'default'} 
                    variant="outlined" />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {field.description}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Auto-fill:</strong> {field.autoFill}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>When to use:</strong> {field.common}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
        Placing Fields on Your Document
      </Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box component="ol" sx={{ pl: 3, m: 0 }}>
          <Typography component="li" variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
            <strong>Open the field editor</strong> — from the document detail page, click "Place Fields". The PDF opens with an overlay editor.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
            <strong>Choose a field type</strong> — use the sidebar panel to select Signature, Date, Name, Initials, or Text. Or right-click anywhere on the PDF to add a field at that position.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
            <strong>Drag to position</strong> — drag the field to the exact position on the page. Fields can be placed on any page of a multi-page document.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1.5, color: 'text.secondary' }}>
            <strong>Assign to a signer</strong> — each field is assigned to a signer number (Signer 1, Signer 2, etc.). When you add signers later, Signer 1 will see their fields highlighted, Signer 2 will see theirs, and so on.
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 0, color: 'text.secondary' }}>
            <strong>Save</strong> — click Save to store the field positions. You can return to the editor to adjust fields at any time before sending.
          </Typography>
        </Box>
      </Paper>

      <Paper sx={{ p: 3, bgcolor: '#e3f2fd' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Fields and Templates
        </Typography>
        <Typography variant="body2" color="text.secondary">
          When you save a document as a template, all placed fields are saved with it. Next time you use
          the template, the fields are pre-placed at the same positions — you don't need to drag them again.
          This is especially useful for contracts, NDAs, and agreements you send repeatedly.
        </Typography>
      </Paper>
    </HelpLayout>
  );
}
