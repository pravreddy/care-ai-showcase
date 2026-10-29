/**
 * SigningHeader.js — Top bar on the signing page.
 */
import React from 'react';
import { Box, Paper, Typography, Container } from '@mui/material';

export default function SigningHeader({ signer }) {
  return (
    <Paper elevation={1} sx={{ py: 2, px: 3 }}>
      <Container maxWidth="md">
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={700} color="primary">SignSimple</Typography>
          <Typography variant="body2" color="text.secondary">
            Signing as: {signer?.signer_name} ({signer?.signer_email})
          </Typography>
        </Box>
      </Container>
    </Paper>
  );
}
