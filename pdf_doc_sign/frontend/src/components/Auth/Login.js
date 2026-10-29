import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  Container, Box, Paper, TextField, Button, Typography,
  Alert, Divider, CircularProgress, Stack,
} from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import GitHubIcon from '@mui/icons-material/GitHub';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import FacebookIcon from '@mui/icons-material/Facebook';
import WindowIcon from '@mui/icons-material/Window';
import { authService } from '../../services/api';

const OAUTH_BUTTONS = [
  { provider: 'google', label: 'Google', icon: <GoogleIcon />, color: '#ea4335' },
  { provider: 'github', label: 'GitHub', icon: <GitHubIcon />, color: '#333' },
  { provider: 'microsoft', label: 'Microsoft', icon: <WindowIcon />, color: '#00a4ef' },
  { provider: 'linkedin', label: 'LinkedIn', icon: <LinkedInIcon />, color: '#0077b5' },
  { provider: 'facebook', label: 'Facebook', icon: <FacebookIcon />, color: '#1877f2' },
];

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [providers, setProviders] = useState(null); // null = loading, {} = loaded

  useEffect(() => {
    const oauthError = searchParams.get('error');
    if (oauthError) setError(oauthError);
    authService.getOAuthProviders().then(setProviders).catch(() => setProviders({}));
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await authService.login(formData);
      localStorage.setItem('accessToken', res.tokens.access);
      localStorage.setItem('refreshToken', res.tokens.refresh);
      localStorage.setItem('user', JSON.stringify(res.user));
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.non_field_errors?.[0] || err.response?.data?.error || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = (provider) => {
    window.location.href = `/api/auth/oauth/${provider}/`;
  };

  const enabledProviders = OAUTH_BUTTONS.filter((b) => providers && providers[b.provider]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            SignSimple
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" gutterBottom>
            Sign in to your account
          </Typography>

          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

          {/* OAuth buttons — show skeleton while loading, then real buttons */}
          {providers === null ? (
            /* Loading: show Google placeholder immediately so users see it */
            <Stack spacing={1.5} sx={{ mt: 3 }}>
              <Button
                fullWidth variant="outlined" startIcon={<GoogleIcon />}
                disabled
                sx={{
                  borderColor: '#ddd', color: '#999', textTransform: 'none',
                  fontWeight: 500, py: 1.2,
                }}
              >
                Continue with Google
              </Button>
            </Stack>
          ) : enabledProviders.length > 0 ? (
            <Stack spacing={1.5} sx={{ mt: 3 }}>
              {enabledProviders.map(({ provider, label, icon, color }) => (
                <Button
                  key={provider} fullWidth variant="outlined" startIcon={icon}
                  onClick={() => handleOAuth(provider)}
                  sx={{
                    borderColor: '#ddd', color: '#333', textTransform: 'none',
                    fontWeight: 500, py: 1.2,
                    '&:hover': { borderColor: color, color, bgcolor: `${color}08` },
                  }}
                >
                  Continue with {label}
                </Button>
              ))}
            </Stack>
          ) : null}

          {(providers === null || enabledProviders.length > 0) && (
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">or sign in with email</Typography>
            </Divider>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: enabledProviders.length === 0 ? 3 : 0 }}>
            <TextField
              margin="normal" required fullWidth label="Email Address"
              name="email" autoComplete="email" autoFocus
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <TextField
              margin="normal" required fullWidth label="Password"
              type="password" name="password" autoComplete="current-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
            <Button
              type="submit" fullWidth variant="contained" disabled={loading}
              sx={{ mt: 3, mb: 2, py: 1.3, fontWeight: 600, textTransform: 'none', fontSize: '1rem' }}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
              <Link to="/forgot-password" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="text.secondary">
                  Forgot password?
                </Typography>
              </Link>
              <Link to="/register" style={{ textDecoration: 'none' }}>
                <Typography variant="body2" color="primary">
                  Don't have an account? Start free — 10 docs/month
                </Typography>
              </Link>
            </Box>
          </Box>
        </Paper>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 4 }}>
          © {new Date().getFullYear()} Avyangah Technologies Limited. All rights reserved.
        </Typography>
      </Box>
    </Container>
  );
}
