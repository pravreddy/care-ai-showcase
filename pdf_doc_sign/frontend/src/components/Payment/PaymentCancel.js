import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Paper, Typography, Button, Box } from '@mui/material';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';

export default function PaymentCancel() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper elevation={3} sx={{ p: 5, textAlign: 'center' }}>
        <CancelOutlinedIcon sx={{ fontSize: 72, color: 'warning.main', mb: 2 }} />
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Payment Cancelled
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          No worries — you haven't been charged. You can try again whenever you're ready,
          or continue with your current free plan.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button variant="contained" onClick={() => navigate('/checkout')}>
            Try Again
          </Button>
          <Button variant="outlined" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}
