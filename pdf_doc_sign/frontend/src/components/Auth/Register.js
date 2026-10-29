import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container, Box, Paper, TextField, Button, Typography,
  Alert, Divider, CircularProgress, Stack, Chip,
} from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import GitHubIcon from '@mui/icons-material/GitHub';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import FacebookIcon from '@mui/icons-material/Facebook';
import WindowIcon from '@mui/icons-material/Window';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { authService } from '../../services/api';

const OAUTH_BUTTONS = [
  { provider: 'google', label: 'Google', icon: <GoogleIcon />, color: '#ea4335' },
  { provider: 'github', label: 'GitHub', icon: <GitHubIcon />, color: '#333' },
  { provider: 'microsoft', label: 'Microsoft', icon: <WindowIcon />, color: '#00a4ef' },
  { provider: 'linkedin', label: 'LinkedIn', icon: <LinkedInIcon />, color: '#0077b5' },
  { provider: 'facebook', label: 'Facebook', icon: <FacebookIcon />, color: '#1877f2' },
];

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '', password: '', password2: '', full_name: '', company_name: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [registered, setRegistered] = useState(false);
  const [providers, setProviders] = useState({});

  useEffect(() => {
    authService.getOAuthProviders().then(setProviders).catch(() => {});
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (formData.password !== formData.password2) {
      setError("Passwords don't match.");
      return;
    }
    setLoading(true);
    try {
      const res = await authService.register(formData);
      if (res.requires_activation) {
        // Email/password registration — needs email activation first
        setRegistered(true);
      } else if (res.tokens) {
        // Direct login (future use)
        localStorage.setItem('accessToken', res.tokens.access);
        localStorage.setItem('refreshToken', res.tokens.refresh);
        localStorage.setItem('user', JSON.stringify(res.user));
        navigate('/dashboard');
      }
    } catch (err) {
      const data = err.response?.data;
      const msg = data?.email?.[0] || data?.password?.[0] || data?.non_field_errors?.[0] || data?.detail || 'Registration failed.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = (provider) => {
    window.location.href = `/api/auth/oauth/${provider}/`;
  };

  const enabledProviders = OAUTH_BUTTONS.filter((b) => providers[b.provider]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 6, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            Start Free Today
          </Typography>

          {/* Value proposition */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
            <Chip icon={<CheckCircleIcon />} label="10 free docs/month" color="success" variant="outlined" size="small" />
            <Chip icon={<CheckCircleIcon />} label="No credit card" color="success" variant="outlined" size="small" />
            <Chip icon={<CheckCircleIcon />} label="Legally binding" color="success" variant="outlined" size="small" />
          </Box>

          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

          {registered && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <strong>Check your email!</strong> We sent an activation link to <strong>{formData.email}</strong>.
              Click the link to activate your account, then sign in.
            </Alert>
          )}

          {/* OAuth + form — hide after successful registration */}
          {!registered && enabledProviders.length > 0 && (
            <Stack spacing={1.5} sx={{ mt: 3 }}>
              {enabledProviders.map(({ provider, label, icon, color }) => (
                <Button
                  key={provider}
                  fullWidth variant="outlined" startIcon={icon}
                  onClick={() => handleOAuth(provider)}
                  sx={{
                    borderColor: '#ddd', color: '#333', textTransform: 'none',
                    fontWeight: 500, py: 1.2,
                    '&:hover': { borderColor: color, color, bgcolor: `${color}08` },
                  }}
                >
                  Sign up with {label}
                </Button>
              ))}
            </Stack>
          )}

          {!registered && enabledProviders.length > 0 && (
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">or sign up with email</Typography>
            </Divider>
          )}

          {!registered && <Box component="form" onSubmit={handleSubmit} sx={{ mt: enabledProviders.length === 0 ? 3 : 0 }}>
            <TextField
              margin="dense" required fullWidth label="Full Name"
              name="full_name" autoFocus value={formData.full_name} onChange={handleChange}
            />
            <TextField
              margin="dense" fullWidth label="Company Name (optional)"
              name="company_name" value={formData.company_name} onChange={handleChange}
            />
            <TextField
              margin="dense" required fullWidth label="Email Address"
              name="email" type="email" autoComplete="email"
              value={formData.email} onChange={handleChange}
            />
            <TextField
              margin="dense" required fullWidth label="Password"
              name="password" type="password" value={formData.password} onChange={handleChange}
              helperText="At least 8 characters"
            />
            <TextField
              margin="dense" required fullWidth label="Confirm Password"
              name="password2" type="password" value={formData.password2} onChange={handleChange}
            />
            <Button
              type="submit" fullWidth variant="contained" disabled={loading}
              sx={{ mt: 2, mb: 2, py: 1.3, fontWeight: 600, textTransform: 'none', fontSize: '1rem' }}
            >
              {loading ? <CircularProgress size={24} /> : 'Create Free Account'}
            </Button>

            <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 1 }}>
              By creating an account you agree to our Terms of Service and Privacy Policy.
            </Typography>

            <Box sx={{ textAlign: 'center' }}>
              <Link to="/login" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">Already have an account? Sign in</Typography>
              </Link>
            </Box>
          </Box>}
        </Paper>
      </Box>
    </Container>
  );
}
