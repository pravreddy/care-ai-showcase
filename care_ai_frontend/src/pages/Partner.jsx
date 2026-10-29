import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { registerPartner, createAPIKey, listAPIKeys, revokeAPIKey, getPartnerUsage } from '../services/api';
import { Key, Plus, Trash2, Copy, Eye, EyeOff, ExternalLink } from 'lucide-react';

export default function Partner() {
  const [hasPartner, setHasPartner] = useState(null); // null = loading
  const [usage, setUsage] = useState(null);
  const [keys, setKeys] = useState([]);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Registration form
  const [companyName, setCompanyName] = useState('');
  const [tier, setTier] = useState('starter');

  // New key form
  const [keyName, setKeyName] = useState('');
  const [testMode, setTestMode] = useState(false);
  const [showKeyForm, setShowKeyForm] = useState(false);

  useEffect(() => {
    loadPartnerData();
  }, []);

  const loadPartnerData = async () => {
    try {
      const u = await getPartnerUsage();
      setUsage(u);
      setHasPartner(true);
      const k = await listAPIKeys();
      setKeys(k);
    } catch {
      setHasPartner(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await registerPartner(companyName, tier);
      await loadPartnerData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await createAPIKey(keyName, testMode);
      setNewKeyResult(res);
      setKeyName('');
      setShowKeyForm(false);
      const k = await listAPIKeys();
      setKeys(k);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (keyId, name) => {
    if (!confirm(`Revoke API key "${name}"? This is immediate and permanent.`)) return;
    try {
      await revokeAPIKey(keyId);
      const k = await listAPIKeys();
      setKeys(k);
    } catch (err) {
      setError(err.message);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // Loading
  if (hasPartner === null) {
    return <main className="main-content"><div className="loading-centre"><div className="spinner-lg" /><p>Loading...</p></div></main>;
  }

  // Not registered yet
  if (!hasPartner) {
    return (
      <main className="main-content">
        <div className="container-narrow">
          <h2 style={{ marginBottom: 'var(--space-sm)' }}>Partner API Access</h2>
          <p style={{ color: 'var(--nhs-dark-grey)', marginBottom: 'var(--space-xl)', lineHeight: 1.6 }}>
            Integrate Care AI into your existing care management app. Get API keys with
            rate limits, usage tracking, and dedicated support.
          </p>

          {error && <div className="alert alert-danger">{error}</div>}

          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-lg)' }}>Register as a Partner</h3>
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label className="form-label">Company name</label>
                <input type="text" className="form-input" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required placeholder="e.g. Best Care Agency Ltd" />
              </div>
              <div className="form-group">
                <label className="form-label">Plan</label>
                <select className="form-select" value={tier} onChange={(e) => setTier(e.target.value)}>
                  <option value="starter">Starter — £80/mo (10k requests, 30 req/min)</option>
                  <option value="professional">Professional — £200/mo (50k requests, 100 req/min)</option>
                  <option value="enterprise">Enterprise — Custom (500k requests, 500 req/min)</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? <><div className="spinner" /> Registering...</> : 'Register partner account'}
              </button>
            </form>
          </div>

          <div style={{ marginTop: 'var(--space-xl)' }}>
            <Link to="/docs" className="btn btn-outline">
              <ExternalLink size={16} /> View API documentation
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // Partner dashboard
  return (
    <main className="main-content">
      <div className="container">
        <h2 style={{ marginBottom: 'var(--space-lg)' }}>Partner Dashboard</h2>

        {error && <div className="alert alert-danger">{error}</div>}

        {/* Usage stats */}
        {usage && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{usage.company_name}</div>
              <div className="stat-label">{usage.tier} plan</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{usage.requests_this_month.toLocaleString()}</div>
              <div className="stat-label">Requests this month</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{usage.requests_remaining.toLocaleString()}</div>
              <div className="stat-label">Remaining quota</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{usage.rate_limit_per_minute}</div>
              <div className="stat-label">Requests per minute</div>
            </div>
          </div>
        )}

        {/* New key alert */}
        {newKeyResult && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--space-xl)' }}>
            <h4 style={{ marginBottom: 'var(--space-sm)' }}>⚠️ Save your API key now</h4>
            <p style={{ marginBottom: 'var(--space-sm)' }}>
              This is the only time you'll see this key. Copy it and store it securely.
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center', background: '#fff', padding: 'var(--space-sm) var(--space-md)', borderRadius: 'var(--radius-sm)', fontFamily: 'monospace', fontSize: '0.85rem', wordBreak: 'break-all' }}>
              <code style={{ flex: 1 }}>{newKeyResult.api_key}</code>
              <button className="btn btn-sm btn-outline" onClick={() => copyToClipboard(newKeyResult.api_key)}>
                <Copy size={14} /> Copy
              </button>
            </div>
            <button className="btn btn-sm btn-outline" style={{ marginTop: 'var(--space-sm)' }} onClick={() => setNewKeyResult(null)}>
              I've saved it, dismiss
            </button>
          </div>
        )}

        {/* API Keys */}
        <div className="card">
          <div className="card-header">
            <h3>API Keys</h3>
            <button className="btn btn-primary btn-sm" onClick={() => setShowKeyForm(true)}>
              <Plus size={14} /> Create key
            </button>
          </div>

          {showKeyForm && (
            <form onSubmit={handleCreateKey} style={{ marginBottom: 'var(--space-lg)', padding: 'var(--space-md)', background: 'var(--nhs-pale-grey)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'end' }}>
                <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="form-label">Key name</label>
                  <input type="text" className="form-input" value={keyName} onChange={(e) => setKeyName(e.target.value)} placeholder="e.g. Production" required />
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  <input type="checkbox" checked={testMode} onChange={(e) => setTestMode(e.target.checked)} />
                  Test mode
                </label>
                <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>Create</button>
                <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowKeyForm(false)}>Cancel</button>
              </div>
            </form>
          )}

          {keys.length === 0 ? (
            <p style={{ color: 'var(--nhs-mid-grey)', textAlign: 'center', padding: 'var(--space-xl)' }}>
              No API keys yet. Create one to start integrating.
            </p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--nhs-pale-grey)' }}>
                  <th style={{ textAlign: 'left', padding: 'var(--space-sm)', color: 'var(--nhs-mid-grey)', fontSize: '0.85rem', fontWeight: 600 }}>Name</th>
                  <th style={{ textAlign: 'left', padding: 'var(--space-sm)', color: 'var(--nhs-mid-grey)', fontSize: '0.85rem', fontWeight: 600 }}>Key</th>
                  <th style={{ textAlign: 'left', padding: 'var(--space-sm)', color: 'var(--nhs-mid-grey)', fontSize: '0.85rem', fontWeight: 600 }}>Type</th>
                  <th style={{ textAlign: 'right', padding: 'var(--space-sm)', color: 'var(--nhs-mid-grey)', fontSize: '0.85rem', fontWeight: 600 }}>Requests</th>
                  <th style={{ textAlign: 'right', padding: 'var(--space-sm)', color: 'var(--nhs-mid-grey)', fontSize: '0.85rem', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: 'var(--space-sm)' }}></th>
                </tr>
              </thead>
              <tbody>
                {keys.map(k => (
                  <tr key={k.id} style={{ borderBottom: '1px solid var(--nhs-pale-grey)' }}>
                    <td style={{ padding: 'var(--space-sm)', fontWeight: 500 }}>{k.name}</td>
                    <td style={{ padding: 'var(--space-sm)', fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--nhs-mid-grey)' }}>{k.key_prefix}</td>
                    <td style={{ padding: 'var(--space-sm)' }}>
                      <span className={`badge ${k.is_test ? 'badge-warning' : 'badge-info'}`}>
                        {k.is_test ? 'test' : 'live'}
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-sm)', textAlign: 'right' }}>{k.total_requests.toLocaleString()}</td>
                    <td style={{ padding: 'var(--space-sm)', textAlign: 'right' }}>
                      <span className={`badge ${k.is_active ? 'badge-success' : 'badge-neutral'}`}>
                        {k.is_active ? 'active' : 'revoked'}
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-sm)', textAlign: 'right' }}>
                      {k.is_active && (
                        <button className="btn btn-danger btn-sm" onClick={() => handleRevoke(k.id, k.name)} title="Revoke key">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ marginTop: 'var(--space-xl)' }}>
          <Link to="/docs" className="btn btn-outline">
            <ExternalLink size={16} /> View API documentation
          </Link>
        </div>
      </div>
    </main>
  );
}
