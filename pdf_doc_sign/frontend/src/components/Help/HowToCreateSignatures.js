import React from 'react';
import {
  Typography, Paper, Box, Grid, Card, CardContent,
} from '@mui/material';
import DrawIcon from '@mui/icons-material/Draw';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import ImageIcon from '@mui/icons-material/Image';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const METHODS = [
  {
    icon: <DrawIcon sx={{ fontSize: 48 }} />,
    title: 'Draw Your Signature',
    color: '#2e7d32',
    steps: [
      'Click on a signature field or the "Add Signature" section',
      'Select the "Draw" tab in the signature dialog',
      'Use your mouse, trackpad, or finger (on mobile) to draw your signature',
      'Click "Apply" to place it on the document',
    ],
    tip: 'Take your time — you can clear and redraw as many times as you like before applying.',
  },
  {
    icon: <KeyboardIcon sx={{ fontSize: 48 }} />,
    title: 'Type Your Signature',
    color: '#1565c0',
    steps: [
      'Click on a signature field or the "Add Signature" section',
      'Select the "Type" tab in the signature dialog',
      'Type your full name — a stylised signature is generated automatically',
      'Click "Apply" to place it on the document',
    ],
    tip: 'The typed signature uses a handwriting-style font to create a professional-looking signature from your name.',
  },
  {
    icon: <ImageIcon sx={{ fontSize: 48 }} />,
    title: 'Upload a Signature Image',
    color: '#f57c00',
    steps: [
      'Click on a signature field or the "Add Signature" section',
      'Select the "Upload" tab in the signature dialog',
      'Choose a PNG or JPG image of your handwritten signature',
      'The image is cropped and resized automatically',
      'Click "Apply" to place it on the document',
    ],
    tip: 'For best results, sign on white paper with a dark pen, then photograph it with good lighting. A transparent background PNG works best.',
  },
];

export default function HowToCreateSignatures() {
  return (
    <HelpLayout>
      <SEO
        title="How to Create Your Electronic Signature"
        description="Three ways to create your e-signature with SignSimple: draw, type, or upload an image. All legally binding under UK law."
        path="/help/how-to-create-signatures"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        How to Create Your Signature
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        SignSimple offers three ways to create your electronic signature. All three are equally valid
        and legally binding — choose whichever is most convenient for you.
      </Typography>

      <Grid container spacing={3}>
        {METHODS.map((method) => (
          <Grid item xs={12} key={method.title}>
            <Card variant="outlined">
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ color: method.color }}>{method.icon}</Box>
                  <Typography variant="h5" fontWeight={600}>{method.title}</Typography>
                </Box>

                <Box component="ol" sx={{ pl: 3, mb: 2 }}>
                  {method.steps.map((step, i) => (
                    <Typography component="li" variant="body2" key={i} sx={{ mb: 1, color: 'text.secondary' }}>
                      {step}
                    </Typography>
                  ))}
                </Box>

                <Paper sx={{ p: 2, bgcolor: '#f5f5f5', borderLeft: `4px solid ${method.color}` }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Tip:</strong> {method.tip}
                  </Typography>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3, mt: 4, bgcolor: '#e8f5e9' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Saving Your Signature
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your signature is saved automatically when you sign a document. If you sign multiple documents,
          your last signature is available as the default for future use — so you don't have to redraw it every time.
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mt: 2, bgcolor: '#fff3e0' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Legal Validity
        </Typography>
        <Typography variant="body2" color="text.secondary">
          All three signature methods (draw, type, upload) are equally legally valid under UK law
          (Electronic Communications Act 2000), EU regulation (eIDAS), and international frameworks.
          What matters legally is the intent to sign, not the visual style of the signature.
        </Typography>
      </Paper>
    </HelpLayout>
  );
}
