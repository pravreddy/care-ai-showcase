/**
 * Care AI API Client
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = '/api/v1';

// --- Token management ---
export function getToken() {
  return localStorage.getItem('care_ai_token');
}

export function setToken(token) {
  localStorage.setItem('care_ai_token', token);
}

export function clearToken() {
  localStorage.removeItem('care_ai_token');
  localStorage.removeItem('care_ai_refresh');
  localStorage.removeItem('care_ai_user');
}

export function getUser() {
  const u = localStorage.getItem('care_ai_user');
  return u ? JSON.parse(u) : null;
}

export function setUser(user) {
  localStorage.setItem('care_ai_user', JSON.stringify(user));
}

export function isLoggedIn() {
  return !!getToken();
}

// --- Fetch wrapper ---
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...options.headers };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (let browser set multipart boundary)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

// --- Auth ---
export async function register(email, password, fullName) {
  const data = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  setToken(data.access_token);
  localStorage.setItem('care_ai_refresh', data.refresh_token);
  // Fetch user profile
  const user = await getMe();
  setUser(user);
  return data;
}

export async function login(email, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  // Check if 2FA is required
  if (data.requires_2fa) {
    // Don't set tokens yet — return the MFA state
    return { requires_2fa: true, mfa_token: data.mfa_token };
  }

  // No 2FA — proceed normally
  setToken(data.access_token);
  localStorage.setItem('care_ai_refresh', data.refresh_token);
  const user = await getMe();
  setUser(user);
  return data;
}

export async function verify2FALogin(mfaToken, code, isRecoveryCode = false) {
  const data = await apiFetch('/auth/login/verify-2fa', {
    method: 'POST',
    body: JSON.stringify({
      mfa_token: mfaToken,
      code: code,
      is_recovery_code: isRecoveryCode,
    }),
  });
  setToken(data.access_token);
  localStorage.setItem('care_ai_refresh', data.refresh_token);
  const user = await getMe();
  setUser(user);
  return data;
}

// --- 2FA Management ---
export async function setup2FA() {
  return apiFetch('/auth/2fa/setup', { method: 'POST' });
}

export async function confirm2FA(code) {
  return apiFetch('/auth/2fa/confirm', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function disable2FA(password) {
  return apiFetch('/auth/2fa/disable', {
    method: 'POST',
    body: JSON.stringify(password),
  });
}

export async function get2FAStatus() {
  return apiFetch('/auth/2fa/status');
}

export async function regenerateRecoveryCodes(password) {
  return apiFetch('/auth/2fa/regenerate-recovery', {
    method: 'POST',
    body: JSON.stringify(password),
  });
}

export async function logout() {
  // Call backend to blacklist the token (real logout)
  try {
    await apiFetch('/auth/logout', { method: 'POST' });
  } catch (e) {
    // Even if backend call fails, still clear local tokens
    console.warn('Backend logout failed:', e);
  }
  clearToken();
}

export async function getMe() {
  return apiFetch('/auth/me');
}

// --- Medical Agent ---
export async function askQuestion(question, strategy = 'auto') {
  return apiFetch('/agent/ask', {
    method: 'POST',
    body: JSON.stringify({ question, strategy, include_sources: true }),
  });
}

export async function getMCPTools() {
  return apiFetch('/agent/mcp/tools');
}

export async function callMCPTool(toolName, args) {
  return apiFetch('/agent/mcp/call', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName, arguments: args }),
  });
}

export async function getCacheStats() {
  return apiFetch('/agent/cache/stats');
}

// --- Clinical Notes ---
export async function uploadVoiceNote(file, clientName = '', noteType = 'full') {
  const form = new FormData();
  form.append('file', file);
  if (clientName) form.append('client_name', clientName);
  form.append('note_type', noteType);

  return apiFetch('/notes/voice', { method: 'POST', body: form });
}

export async function uploadVideoNote(file, clientName = '', noteType = 'full') {
  const form = new FormData();
  form.append('file', file);
  if (clientName) form.append('client_name', clientName);
  form.append('note_type', noteType);

  return apiFetch('/notes/video', { method: 'POST', body: form });
}

export async function submitTextNote(text, clientName = '', noteType = 'full') {
  const form = new FormData();
  form.append('text', text);
  if (clientName) form.append('client_name', clientName);
  form.append('note_type', noteType);

  return apiFetch('/notes/text', { method: 'POST', body: form });
}

export async function listNotes(limit = 20, offset = 0) {
  return apiFetch(`/notes/?limit=${limit}&offset=${offset}`);
}

export async function getNote(noteId) {
  return apiFetch(`/notes/${noteId}`);
}

export async function generateHandover(hours = 12) {
  return apiFetch(`/notes/handover?hours=${hours}`, { method: 'POST' });
}

// --- Partner API ---
export async function registerPartner(companyName, tier = 'starter') {
  return apiFetch('/partner/register', {
    method: 'POST',
    body: JSON.stringify({ company_name: companyName, tier }),
  });
}

export async function createAPIKey(name, testMode = false) {
  return apiFetch('/partner/keys', {
    method: 'POST',
    body: JSON.stringify({ name, test_mode: testMode }),
  });
}

export async function listAPIKeys() {
  return apiFetch('/partner/keys');
}

export async function revokeAPIKey(keyId) {
  return apiFetch(`/partner/keys/${keyId}`, { method: 'DELETE' });
}

export async function getPartnerUsage() {
  return apiFetch('/partner/usage');
}

// --- Health ---
export async function getHealth() {
  const res = await fetch('/health');
  return res.json();
}

// --- Trial (no auth) ---
export async function trialAsk(question) {
  const res = await fetch(`${API_BASE}/trial/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (res.status === 429) {
    const err = await res.json();
    throw { limitReached: true, ...err.detail };
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

export async function trialStatus() {
  const res = await fetch(`${API_BASE}/trial/status`);
  return res.json();
}
