import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { login, verify2FALogin } from '../services/api';
import { Shield } from 'lucide-react';

const GOOGLE_SVG = (
  <svg width="18" height="18" viewBox="0 0 48 48" style={{ marginRight: 8 }}>
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
  </svg>
);

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // 2FA state
  const [needs2FA, setNeeds2FA] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [useRecovery, setUseRecovery] = useState(false);
  const codeInputRef = useRef(null);

  // Show OAuth error from redirect if present
  useEffect(() => {
    const oauthError = searchParams.get('error');
    if (oauthError) {
      setError(oauthError);
    }
  }, [searchParams]);

  // Auto-focus the TOTP input when 2FA stage appears
  useEffect(() => {
    if (needs2FA && codeInputRef.current) {
      codeInputRef.current.focus();
    }
  }, [needs2FA]);

  // Stage 1: Email + Password
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.requires_2fa) {
        // Move to Stage 2
        setNeeds2FA(true);
        setMfaToken(result.mfa_token);
      } else {
        // No 2FA — go straight to dashboard
        navigate('/dashboard');
      }
    } catch (err) {
      const msg = err.message || 'Invalid email or password';
      if (msg.includes('locked') || msg.includes('Too many')) {
        setError('🔒 ' + msg);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  // Stage 2: TOTP Code (or Recovery Code)
  const handleTOTPSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await verify2FALogin(mfaToken, totpCode, useRecovery);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Invalid code');
      setTotpCode('');
    } finally {
      setLoading(false);
    }
  };

  // Auto-submit when 6 digits entered (TOTP only, not recovery)
  const handleCodeChange = (val) => {
    // Strip non-alphanumeric except dash (for recovery codes)
    const cleaned = useRecovery ? val : val.replace(/\D/g, '');
    setTotpCode(cleaned);
  };

  const handleGoogleLogin = () => {
    // Redirect to backend Google OAuth endpoint
    window.location.href = '/api/v1/auth/google';
  };

  return (
    <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="container-narrow">
        <div className="card" style={{ maxWidth: '440px', margin: '0 auto' }}>

          {/* Stage 1: Password */}
          {!needs2FA && (
            <>
              <h2 style={{ marginBottom: 'var(--space-sm)' }}>Sign in</h2>
              <p style={{ color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xl)' }}>
                Access your Care AI dashboard
              </p>

              {error && <div className="alert alert-danger">{error}</div>}

              {/* Google Sign-In Button */}
              <button
                type="button"
                onClick={handleGoogleLogin}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '10px 16px',
                  border: '1px solid var(--nhs-border)',
                  borderRadius: '8px',
                  background: '#fff',
                  color: '#3c4043',
                  fontSize: '0.95rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  marginBottom: 'var(--space-lg)',
                  transition: 'background 0.15s, box-shadow 0.15s',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = '#f8f9fa';
                  e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = '#fff';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {GOOGLE_SVG}
                Continue with Google
              </button>

              {/* Divider */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                marginBottom: 'var(--space-lg)', color: 'var(--nhs-mid-grey)',
              }}>
                <div style={{ flex: 1, height: 1, background: 'var(--nhs-border)' }} />
                <span style={{ fontSize: '0.85rem' }}>or sign in with email</span>
                <div style={{ flex: 1, height: 1, background: 'var(--nhs-border)' }} />
              </div>

              <form onSubmit={handlePasswordSubmit}>
                <div className="form-group">
                  <label className="form-label">Email address</label>
                  <input
                    type="email" className="form-input" value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required autoFocus placeholder="you@example.co.uk"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Password</label>
                  <input
                    type="password" className="form-input" value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required placeholder="Your password"
                  />
                </div>
                <button type="submit" className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
                  {loading ? <><div className="spinner" /> Signing in...</> : 'Sign in'}
                </button>
              </form>

              <p style={{ textAlign: 'center', marginTop: 'var(--space-lg)', color: 'var(--nhs-mid-grey)' }}>
                Don't have an account? <Link to="/register">Start your free trial</Link>
              </p>
            </>
          )}

          {/* Stage 2: 2FA Verification */}
          {needs2FA && (
            <>
              <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
                <div style={{
                  width: 56, height: 56, borderRadius: '50%',
                  background: 'var(--nhs-light-blue)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', margin: '0 auto var(--space-md)',
                }}>
                  <Shield size={28} color="var(--nhs-blue)" />
                </div>
                <h2 style={{ marginBottom: 'var(--space-sm)' }}>Two-factor authentication</h2>
                <p style={{ color: 'var(--nhs-mid-grey)' }}>
                  {useRecovery
                    ? 'Enter one of your recovery codes'
                    : 'Enter the 6-digit code from your authenticator app'
                  }
                </p>
              </div>

              {error && <div className="alert alert-danger">{error}</div>}

              <form onSubmit={handleTOTPSubmit}>
                <div className="form-group">
                  <label className="form-label">
                    {useRecovery ? 'Recovery code' : 'Verification code'}
                  </label>
                  <input
                    ref={codeInputRef}
                    type="text"
                    className="form-input"
                    value={totpCode}
                    onChange={(e) => handleCodeChange(e.target.value)}
                    required
                    autoComplete="one-time-code"
                    inputMode={useRecovery ? 'text' : 'numeric'}
                    placeholder={useRecovery ? 'XXXX-XXXX' : '000000'}
                    maxLength={useRecovery ? 9 : 6}
                    style={{
                      fontSize: '1.5rem', textAlign: 'center',
                      letterSpacing: useRecovery ? '0.1em' : '0.3em',
                      fontFamily: 'monospace',
                    }}
                  />
                </div>

                <button type="submit" className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
                  {loading ? <><div className="spinner" /> Verifying...</> : 'Verify'}
                </button>
              </form>

              <div style={{
                textAlign: 'center', marginTop: 'var(--space-lg)',
                paddingTop: 'var(--space-md)', borderTop: '1px solid var(--nhs-border)',
              }}>
                <button
                  onClick={() => { setUseRecovery(!useRecovery); setTotpCode(''); setError(''); }}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--nhs-blue)', fontSize: '0.9rem',
                  }}
                >
                  {useRecovery ? '← Use authenticator app instead' : 'Lost your phone? Use a recovery code'}
                </button>
              </div>

              <div style={{ textAlign: 'center', marginTop: 'var(--space-sm)' }}>
                <button
                  onClick={() => { setNeeds2FA(false); setMfaToken(''); setTotpCode(''); setError(''); }}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--nhs-mid-grey)', fontSize: '0.85rem',
                  }}
                >
                  ← Back to login
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
