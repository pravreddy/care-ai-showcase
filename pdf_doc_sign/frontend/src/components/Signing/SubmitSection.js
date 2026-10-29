/**
 * SubmitSection.js — Agreement text + Sign Document button.
 */
import React from 'react';
import { Box, Paper, Typography, Button, Alert, CircularProgress } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TouchAppIcon from '@mui/icons-material/TouchApp';

export default function SubmitSection({ hasFields, allFieldsFilled, signatureBlob, submitting, onSubmit }) {
  return (
    <Paper sx={{ p: 3 }}>
      {hasFields && signatureBlob && (
        <Alert severity="success" sx={{ mb: 2 }}>
          All fields completed! Click "Sign Document" below to finish.
        </Alert>
      )}
      {hasFields && !signatureBlob && (
        <Alert severity="warning" sx={{ mb: 2 }} icon={<TouchAppIcon />}>
          Please click the green "Sign here" fields in the document above to add your signature.
        </Alert>
      )}

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        By clicking "Sign Document", you agree that your electronic signature is legally binding
        and that you have reviewed the document above.
      </Typography>
      <Button
        variant="contained"
        size="large"
        fullWidth
        onClick={onSubmit}
        disabled={!allFieldsFilled || submitting}
        startIcon={submitting ? <CircularProgress size={20} color="inherit" /> : <CheckCircleIcon />}
        sx={{ py: 1.5, fontSize: '1.1rem' }}
      >
        {submitting ? 'Signing...' : 'Sign Document'}
      </Button>
    </Paper>
  );
}
