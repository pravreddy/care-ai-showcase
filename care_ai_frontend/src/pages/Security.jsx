import React, { useState, useEffect } from 'react';
import { Shield, Smartphone, Key, AlertTriangle, Check, Copy, RefreshCw } from 'lucide-react';
import { setup2FA, confirm2FA, disable2FA, get2FAStatus, regenerateRecoveryCodes } from '../services/api';

export default function Security() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Setup flow
  const [setupData, setSetupData] = useState(null); // { secret, qr_code, provisioning_uri }
  const [confirmCode, setConfirmCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState(null);

  // Disable flow
  const [showDisable, setShowDisable] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');

  // Recovery regen
  const [showRegenerate, setShowRegenerate] = useState(false);
  const [regenPassword, setRegenPassword] = useState('');

  useEffect(() => { loadStatus(); }, []);

  async function loadStatus() {
    try {
      const s = await get2FAStatus();
      setStatus(s);
    } catch (e) {
      setError('Failed to load 2FA status');
    } finally {
      setLoading(false);
    }
  }

  // --- Enable 2FA ---
  async function handleSetup() {
    setError(''); setSuccess('');
    try {
      const data = await setup2FA();
      setSetupData(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleConfirm(e) {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      const result = await confirm2FA(confirmCode);
      setRecoveryCodes(result.recovery_codes);
      setSetupData(null);
      setConfirmCode('');
      await loadStatus();
      setSuccess('2FA enabled successfully!');
    } catch (e) {
      setError(e.message);
    }
  }

  // --- Disable 2FA ---
  async function handleDisable(e) {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      await disable2FA(disablePassword);
      setShowDisable(false);
      setDisablePassword('');
      setRecoveryCodes(null);
      await loadStatus();
      setSuccess('2FA has been disabled');
    } catch (e) {
      setError(e.message);
    }
  }

  // --- Regenerate Recovery Codes ---
  async function handleRegenerate(e) {
    e.preventDefault();
    setError(''); setSuccess('');
    try {
      const result = await regenerateRecoveryCodes(regenPassword);
      setRecoveryCodes(result.recovery_codes);
      setShowRegenerate(false);
      setRegenPassword('');
      await loadStatus();
      setSuccess('New recovery codes generated');
    } catch (e) {
      setError(e.message);
    }
  }

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      setSuccess('Copied to clipboard');
      setTimeout(() => setSuccess(''), 2000);
    });
  }

  if (loading) {
    return (
      <main className="main-content">
        <div className="container-narrow" style={{ textAlign: 'center', padding: 'var(--space-3xl)' }}>
          <div className="spinner" /> Loading security settings...
        </div>
      </main>
    );
  }

  return (
    <main className="main-content">
      <div className="container-narrow" style={{ maxWidth: '640px' }}>
        <h2 style={{ marginBottom: 'var(--space-sm)' }}>
          <Shield size={24} style={{ marginRight: 8, verticalAlign: 'middle' }} />
          Security Settings
        </h2>
        <p style={{ color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xl)' }}>
          Manage two-factor authentication and recovery options
        </p>

        {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-lg)' }}>{error}</div>}
        {success && <div className="alert alert-success" style={{ marginBottom: 'var(--space-lg)' }}>{success}</div>}

        {/* --- Status Card --- */}
        <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
              <div style={{
                width: 44, height: 44, borderRadius: '50%',
                background: status?.enabled ? '#e8f5e9' : '#fff3e0',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {status?.enabled
                  ? <Check size={22} color="var(--nhs-green)" />
                  : <AlertTriangle size={22} color="#f57c00" />
                }
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.05rem' }}>Two-Factor Authentication</h3>
                <p style={{ margin: 0, color: 'var(--nhs-mid-grey)', fontSize: '0.9rem' }}>
                  {status?.enabled
                    ? `Active — ${status.recovery_codes_remaining} recovery codes remaining`
                    : 'Not enabled — your account is less secure'
                  }
                </p>
              </div>
            </div>
            {!status?.enabled && !setupData && (
              <button className="btn btn-primary" onClick={handleSetup}>
                <Smartphone size={16} /> Enable 2FA
              </button>
            )}
            {status?.enabled && !showDisable && (
              <button className="btn btn-danger" onClick={() => setShowDisable(true)}
                style={{ background: 'var(--nhs-red)', borderColor: 'var(--nhs-red)' }}>
                Disable
              </button>
            )}
          </div>
        </div>

        {/* --- NHS Compliance Note --- */}
        {!status?.enabled && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--space-lg)' }}>
            <strong>NHS DSPT Requirement:</strong> Multi-factor authentication is mandatory for
            systems accessing health data. Enable 2FA to meet NHS Data Security Standard 8.
          </div>
        )}

        {/* --- Setup Flow: QR Code --- */}
        {setupData && !recoveryCodes && (
          <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
            <h3><Smartphone size={20} style={{ marginRight: 8 }} /> Set up your authenticator</h3>

            <div style={{ margin: 'var(--space-lg) 0' }}>
              <p style={{ marginBottom: 'var(--space-md)' }}>
                <strong>Step 1:</strong> Scan this QR code with your authenticator app
                (Google Authenticator, Microsoft Authenticator, or Authy)
              </p>

              <div style={{ textAlign: 'center', padding: 'var(--space-lg)', background: '#fafafa', borderRadius: 'var(--radius-md)' }}>
                {setupData.qr_code.startsWith('data:') ? (
                  <img src={setupData.qr_code} alt="2FA QR Code"
                    style={{ maxWidth: 220, border: '4px solid white', borderRadius: 8 }} />
                ) : (
                  <p style={{ fontFamily: 'monospace', fontSize: '0.8rem', wordBreak: 'break-all' }}>
                    {setupData.provisioning_uri}
                  </p>
                )}
              </div>

              <details style={{ marginTop: 'var(--space-md)', fontSize: '0.9rem' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--nhs-blue)' }}>
                  Can't scan? Enter this code manually
                </summary>
                <div style={{
                  marginTop: 'var(--space-sm)', padding: 'var(--space-md)',
                  background: '#f5f5f5', borderRadius: 'var(--radius-sm)',
                  fontFamily: 'monospace', fontSize: '1.1rem', letterSpacing: '0.15em',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  {setupData.secret}
                  <button onClick={() => copyToClipboard(setupData.secret)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}>
                    <Copy size={16} />
                  </button>
                </div>
              </details>
            </div>

            <form onSubmit={handleConfirm}>
              <p><strong>Step 2:</strong> Enter the 6-digit code from your app to verify</p>
              <div className="form-group" style={{ maxWidth: 240 }}>
                <input
                  type="text" className="form-input" value={confirmCode}
                  onChange={(e) => setConfirmCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000" maxLength={6} inputMode="numeric" autoComplete="one-time-code"
                  style={{ fontSize: '1.5rem', textAlign: 'center', letterSpacing: '0.3em', fontFamily: 'monospace' }}
                />
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                <button type="submit" className="btn btn-primary" disabled={confirmCode.length !== 6}>
                  <Check size={16} /> Verify & Enable
                </button>
                <button type="button" className="btn btn-secondary"
                  onClick={() => { setSetupData(null); setConfirmCode(''); }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- Recovery Codes (shown once after setup or regeneration) --- */}
        {recoveryCodes && (
          <div className="card" style={{ marginBottom: 'var(--space-lg)', border: '2px solid var(--nhs-green)' }}>
            <h3><Key size={20} style={{ marginRight: 8 }} /> Save your recovery codes</h3>
            <div className="alert alert-warning" style={{ margin: 'var(--space-md) 0' }}>
              <strong>Save these now!</strong> Each code can only be used once. If you lose your phone,
              these are the only way to access your account. Store them somewhere safe — not on your phone.
            </div>

            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-sm)',
              background: '#fafafa', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)',
              fontFamily: 'monospace', fontSize: '1.05rem',
            }}>
              {recoveryCodes.map((code, i) => (
                <div key={i} style={{ padding: '6px 12px', background: 'white', borderRadius: 4 }}>
                  {code}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
              <button className="btn btn-secondary"
                onClick={() => copyToClipboard(recoveryCodes.join('\n'))}>
                <Copy size={16} /> Copy all
              </button>
              <button className="btn btn-primary"
                onClick={() => setRecoveryCodes(null)}>
                I've saved them
              </button>
            </div>
          </div>
        )}

        {/* --- Disable 2FA --- */}
        {showDisable && (
          <div className="card" style={{ marginBottom: 'var(--space-lg)', border: '2px solid var(--nhs-red)' }}>
            <h3 style={{ color: 'var(--nhs-red)' }}>Disable Two-Factor Authentication</h3>
            <p style={{ color: 'var(--nhs-dark-grey)' }}>
              This will remove the extra security layer from your account. Enter your password to confirm.
            </p>
            <form onSubmit={handleDisable}>
              <div className="form-group" style={{ maxWidth: 300 }}>
                <input type="password" className="form-input" value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  placeholder="Enter your password" required />
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                <button type="submit" className="btn btn-danger"
                  style={{ background: 'var(--nhs-red)', borderColor: 'var(--nhs-red)' }}>
                  Disable 2FA
                </button>
                <button type="button" className="btn btn-secondary"
                  onClick={() => { setShowDisable(false); setDisablePassword(''); }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- Regenerate Recovery Codes --- */}
        {status?.enabled && (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>
                  <Key size={18} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                  Recovery Codes
                </h3>
                <p style={{ margin: '4px 0 0', color: 'var(--nhs-mid-grey)', fontSize: '0.9rem' }}>
                  {status.recovery_codes_remaining} codes remaining
                  {status.recovery_codes_remaining <= 2 && (
                    <span style={{ color: 'var(--nhs-red)', fontWeight: 600 }}> — generate new ones soon</span>
                  )}
                </p>
              </div>
              {!showRegenerate && (
                <button className="btn btn-secondary" onClick={() => setShowRegenerate(true)}>
                  <RefreshCw size={16} /> Regenerate
                </button>
              )}
            </div>

            {showRegenerate && (
              <form onSubmit={handleRegenerate} style={{ marginTop: 'var(--space-md)' }}>
                <p style={{ fontSize: '0.9rem', color: 'var(--nhs-dark-grey)' }}>
                  This will invalidate all existing recovery codes. Enter your password to confirm.
                </p>
                <div className="form-group" style={{ maxWidth: 300 }}>
                  <input type="password" className="form-input" value={regenPassword}
                    onChange={(e) => setRegenPassword(e.target.value)}
                    placeholder="Enter your password" required />
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                  <button type="submit" className="btn btn-primary">
                    <RefreshCw size={16} /> Generate New Codes
                  </button>
                  <button type="button" className="btn btn-secondary"
                    onClick={() => { setShowRegenerate(false); setRegenPassword(''); }}>
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
