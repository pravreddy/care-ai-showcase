import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Container, Box, Paper, TextField, Button, Typography, Alert, CircularProgress,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { authService } from '../../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [hint, setHint] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) { setError('Please enter your email address'); return; }

    setLoading(true);
    setError('');
    setSuccess('');
    setHint('');

    try {
      const res = await authService.forgotPassword(email.trim());
      setSuccess(res.message || 'If an account with that email exists, a reset link has been sent.');
      if (res.hint) setHint(res.hint);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            SignSimple
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" gutterBottom>
            Reset your password
          </Typography>

          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
          {hint && <Alert severity="info" sx={{ mt: 2 }}>{hint}</Alert>}

          {!success ? (
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Enter your email address and we'll send you a link to reset your password.
              </Typography>

              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                margin="normal"
                required
                autoFocus
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{ mt: 2, py: 1.2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Send Reset Link'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Check your email inbox for a password reset link. The link expires in 24 hours.
              </Typography>
              <Button
                variant="outlined"
                onClick={() => { setSuccess(''); setEmail(''); }}
                sx={{ mt: 1 }}
              >
                Try a different email
              </Button>
            </Box>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              component={Link}
              to="/login"
              startIcon={<ArrowBackIcon />}
              sx={{ textTransform: 'none' }}
            >
              Back to Sign In
            </Button>
          </Box>
        </Paper>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 3, textAlign: 'center' }}>
          © 2026 Avyangah Technologies Limited. All rights reserved.
        </Typography>
      </Box>
    </Container>
  );
}
