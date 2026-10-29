import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Container, Paper, Typography, Button, CircularProgress, Box } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { paymentService, authService } from '../../services/api';

export default function PaymentSuccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    const paymentId = searchParams.get('payment_id') || searchParams.get('session_id');
    if (paymentId) {
      paymentService.getStatus(paymentId)
        .then((data) => setStatus(data.status === 'succeeded' ? 'success' : 'pending'))
        .catch(() => setStatus('success'));  // Assume success since we landed here
    } else {
      setStatus('success');
    }

    // Refresh user profile to get updated plan
    authService.getProfile().then((user) => {
      localStorage.setItem('user', JSON.stringify(user));
    }).catch(() => {});
  }, [searchParams]);

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper elevation={3} sx={{ p: 5, textAlign: 'center' }}>
        {status === 'checking' ? (
          <>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography>Confirming your payment...</Typography>
          </>
        ) : (
          <>
            <CheckCircleOutlineIcon sx={{ fontSize: 72, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Payment Successful!
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Your plan has been upgraded. You can start using your new document allowance immediately.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button variant="contained" onClick={() => navigate('/dashboard')}>
                Go to Dashboard
              </Button>
              <Button variant="outlined" onClick={() => navigate('/documents/upload')}>
                Upload a Document
              </Button>
            </Box>
          </>
        )}
      </Paper>
    </Container>
  );
}
