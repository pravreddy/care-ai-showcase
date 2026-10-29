import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Container, Box, Paper, TextField, Button, Typography, 
    Alert, CircularProgress, InputAdornment, IconButton 
} from '@mui/material';
import { Visibility, VisibilityOff, CheckCircle, Cancel } from '@mui/icons-material';
import api from '../../services/api';

export default function SetPassword() {
    const { token } = useParams();
    const navigate = useNavigate();
    
    const [formData, setFormData] = useState({ 
        password: '', 
        confirmPassword: '' 
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [status, setStatus] = useState({ 
        loading: true, 
        verifying: true,
        submitting: false,
        error: '', 
        success: '', 
        invitationData: null 
    });

    // Password validation
    const passwordChecks = {
        length: formData.password.length >= 8,
        match: formData.password === formData.confirmPassword && formData.confirmPassword.length > 0,
    };
    const isPasswordValid = passwordChecks.length && passwordChecks.match;

    useEffect(() => {
        // Verify token on load using the correct backend endpoint
        const verifyToken = async () => {
            try {
                const response = await api.get(`/auth/invite/verify/${token}/`);
                setStatus({ 
                    ...status, 
                    loading: false, 
                    verifying: false,
                    invitationData: response.data 
                });
            } catch (err) {
                const errorMsg = err.response?.data?.error || 'Invalid or expired invitation link.';
                setStatus({ 
                    ...status, 
                    loading: false, 
                    verifying: false,
                    error: errorMsg 
                });
            }
        };
        
        verifyToken();
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validate passwords match
        if (formData.password !== formData.confirmPassword) {
            setStatus({ ...status, error: "Passwords don't match" });
            return;
        }
        
        // Validate password length
        if (formData.password.length < 8) {
            setStatus({ ...status, error: "Password must be at least 8 characters" });
            return;
        }

        setStatus({ ...status, submitting: true, error: '' });
        
        try {
            // Call the correct backend endpoint with token in body
            const response = await api.post('/auth/invite/setup-password/', { 
                token: token,
                password: formData.password,
                confirm_password: formData.confirmPassword
            });
            
            // Store tokens if returned (auto-login)
            if (response.data.tokens) {
                localStorage.setItem('accessToken', response.data.tokens.access);
                localStorage.setItem('refreshToken', response.data.tokens.refresh);
            }
            
            setStatus({ 
                ...status, 
                submitting: false, 
                success: response.data.message || 'Account created successfully! Redirecting...' 
            });
            
            // Redirect to dashboard (they're now logged in) or login
            setTimeout(() => {
                if (response.data.tokens) {
                    navigate('/dashboard');
                } else {
                    navigate('/login');
                }
            }, 2000);
            
        } catch (err) {
            setStatus({ 
                ...status, 
                submitting: false, 
                error: err.response?.data?.error || 'Failed to set password. Please try again.' 
            });
        }
    };

    // Loading state
    if (status.loading || status.verifying) {
        return (
            <Box sx={{ 
                mt: 10, 
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2
            }}>
                <CircularProgress />
                <Typography color="text.secondary">Verifying your invitation...</Typography>
            </Box>
        );
    }

    // Error state (invalid/expired token)
    if (status.error && !status.invitationData) {
        return (
            <Container maxWidth="xs">
                <Paper sx={{ p: 4, mt: 8, textAlign: 'center' }}>
                    <Cancel color="error" sx={{ fontSize: 60, mb: 2 }} />
                    <Typography variant="h5" gutterBottom color="error">
                        Invalid Invitation
                    </Typography>
                    <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                        {status.error}
                    </Alert>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Please contact your administrator for a new invitation link.
                    </Typography>
                    <Button 
                        variant="contained" 
                        onClick={() => navigate('/login')}
                        fullWidth
                    >
                        Go to Login
                    </Button>
                </Paper>
            </Container>
        );
    }

    // Success state
    if (status.success) {
        return (
            <Container maxWidth="xs">
                <Paper sx={{ p: 4, mt: 8, textAlign: 'center' }}>
                    <CheckCircle color="success" sx={{ fontSize: 60, mb: 2 }} />
                    <Typography variant="h5" gutterBottom color="success.main">
                        Welcome to SignSimple!
                    </Typography>
                    <Alert severity="success" sx={{ mb: 2 }}>
                        {status.success}
                    </Alert>
                    <CircularProgress size={24} sx={{ mt: 2 }} />
                </Paper>
            </Container>
        );
    }

    // Main form
    return (
        <Container maxWidth="xs">
            <Paper sx={{ p: 4, mt: 8 }}>
                <Typography variant="h5" gutterBottom sx={{ textAlign: 'center', mb: 1 }}>
                    Set Your Password
                </Typography>
                
                {status.invitationData && (
                    <Box sx={{ textAlign: 'center', mb: 3 }}>
                        <Typography variant="body1" color="text.secondary">
                            Welcome, <strong>{status.invitationData.full_name || status.invitationData.email}</strong>
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Create a secure password to complete your account setup.
                        </Typography>
                    </Box>
                )}
                
                {status.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {status.error}
                    </Alert>
                )}

                <form onSubmit={handleSubmit}>
                    <TextField 
                        fullWidth 
                        label="New Password" 
                        type={showPassword ? 'text' : 'password'}
                        margin="normal" 
                        required
                        autoFocus
                        value={formData.password}
                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                        InputProps={{
                            endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton
                                        onClick={() => setShowPassword(!showPassword)}
                                        edge="end"
                                    >
                                        {showPassword ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                            ),
                        }}
                        helperText={
                            formData.password.length > 0 && !passwordChecks.length 
                                ? "Password must be at least 8 characters" 
                                : ""
                        }
                        error={formData.password.length > 0 && !passwordChecks.length}
                    />
                    
                    <TextField 
                        fullWidth 
                        label="Confirm Password" 
                        type={showConfirm ? 'text' : 'password'}
                        margin="normal" 
                        required
                        value={formData.confirmPassword}
                        onChange={e => setFormData({ ...formData, confirmPassword: e.target.value })}
                        InputProps={{
                            endAdornment: (
                                <InputAdornment position="end">
                                    <IconButton
                                        onClick={() => setShowConfirm(!showConfirm)}
                                        edge="end"
                                    >
                                        {showConfirm ? <VisibilityOff /> : <Visibility />}
                                    </IconButton>
                                </InputAdornment>
                            ),
                        }}
                        helperText={
                            formData.confirmPassword.length > 0 && !passwordChecks.match 
                                ? "Passwords don't match" 
                                : ""
                        }
                        error={formData.confirmPassword.length > 0 && !passwordChecks.match}
                    />

                    {/* Password requirements indicator */}
                    {formData.password.length > 0 && (
                        <Box sx={{ mt: 2, mb: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                                Password requirements:
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                {passwordChecks.length ? (
                                    <CheckCircle color="success" sx={{ fontSize: 16 }} />
                                ) : (
                                    <Cancel color="error" sx={{ fontSize: 16 }} />
                                )}
                                <Typography variant="caption" color={passwordChecks.length ? 'success.main' : 'error'}>
                                    At least 8 characters
                                </Typography>
                            </Box>
                            {formData.confirmPassword.length > 0 && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                    {passwordChecks.match ? (
                                        <CheckCircle color="success" sx={{ fontSize: 16 }} />
                                    ) : (
                                        <Cancel color="error" sx={{ fontSize: 16 }} />
                                    )}
                                    <Typography variant="caption" color={passwordChecks.match ? 'success.main' : 'error'}>
                                        Passwords match
                                    </Typography>
                                </Box>
                            )}
                        </Box>
                    )}
                    
                    <Button 
                        fullWidth 
                        variant="contained" 
                        type="submit" 
                        sx={{ mt: 3 }}
                        disabled={status.submitting || !isPasswordValid}
                    >
                        {status.submitting ? (
                            <>
                                <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
                                Creating Account...
                            </>
                        ) : (
                            'Create My Account'
                        )}
                    </Button>
                </form>
                
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 3 }}>
                    By creating an account, you agree to our Terms of Service and Privacy Policy.
                </Typography>
            </Paper>
        </Container>
    );
}
