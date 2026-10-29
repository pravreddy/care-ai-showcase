import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { setToken, setUser, getMe } from '../services/api';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      // Check for error from backend
      const errorMsg = searchParams.get('error');
      if (errorMsg) {
        setError(errorMsg);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // Extract tokens from URL
      const token = searchParams.get('token');
      const refresh = searchParams.get('refresh');
      const isNewUser = searchParams.get('new_user') === '1';

      if (!token || !refresh) {
        setError('Authentication failed. Missing tokens.');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      // Store tokens
      setToken(token);
      localStorage.setItem('care_ai_refresh', refresh);

      // Fetch user profile
      try {
        const user = await getMe();
        setUser(user);
        navigate('/dashboard', { replace: true });
      } catch (err) {
        setError('Failed to load your profile. Please try logging in again.');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (error) {
    return (
      <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="container-narrow">
          <div className="card" style={{ maxWidth: '440px', margin: '0 auto', textAlign: 'center' }}>
            <div className="alert alert-danger">{error}</div>
            <p style={{ color: 'var(--nhs-mid-grey)', marginTop: 'var(--space-md)' }}>
              Redirecting to login...
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="container-narrow">
        <div className="card" style={{ maxWidth: '440px', margin: '0 auto', textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto var(--space-md)' }} />
          <p style={{ color: 'var(--nhs-mid-grey)' }}>Signing you in...</p>
        </div>
      </div>
    </main>
  );
}
