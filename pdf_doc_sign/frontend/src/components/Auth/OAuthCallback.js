import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Container, Box, Paper, Typography, CircularProgress, Alert } from '@mui/material';
import { authService } from '../../services/api';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const handle = async () => {
      const errMsg = searchParams.get('error');
      if (errMsg) {
        setError(errMsg);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      const token = searchParams.get('token');
      const refresh = searchParams.get('refresh');

      if (!token || !refresh) {
        setError('Authentication failed. Missing tokens.');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      localStorage.setItem('accessToken', token);
      localStorage.setItem('refreshToken', refresh);

      try {
        const user = await authService.getProfile();
        localStorage.setItem('user', JSON.stringify(user));
        navigate('/dashboard', { replace: true });
      } catch {
        setError('Failed to load your profile. Please try again.');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handle();
  }, [searchParams, navigate]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 12, display: 'flex', justifyContent: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center', minWidth: 300 }}>
          {error ? (
            <>
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
              <Typography variant="body2" color="text.secondary">Redirecting to login...</Typography>
            </>
          ) : (
            <>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography variant="body1" color="text.secondary">Signing you in...</Typography>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
}
