import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;

  // TenantMiddleware: send active org ID on every request
  const orgId = localStorage.getItem('activeOrgId');
  if (orgId) config.headers['X-Organisation-ID'] = orgId;

  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem('refreshToken');
        const res = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh });
        localStorage.setItem('accessToken', res.data.access);
        original.headers.Authorization = `Bearer ${res.data.access}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth ---
export const authService = {
  register: async (data) => (await api.post('/auth/register/', data)).data,
  login: async (creds) => (await api.post('/auth/login/', creds)).data,
  logout: async () => {
    const refresh = localStorage.getItem('refreshToken');
    try { await api.post('/auth/logout/', { refresh }); } catch {}
    localStorage.clear();
  },
  getProfile: async () => (await api.get('/auth/profile/')).data,
  getDashboard: async () => (await api.get('/auth/dashboard/')).data,
  changePassword: async (data) => (await api.post('/auth/change-password/', data)).data,
  forgotPassword: async (email) => (await api.post('/auth/forgot-password/', { email })).data,
  getOAuthProviders: async () => (await api.get('/auth/oauth/providers/')).data,
  resendActivation: async (email) => api.post('/auth/resend-activation/', { email }),
};

// --- Payments ---
export const paymentService = {
  getPlans: async () => (await api.get('/payments/plans/')).data,
  getProviders: async () => (await api.get('/payments/providers/')).data,
  checkout: async (data) => (await api.post('/payments/checkout/', data)).data,
  getStatus: async (paymentId) => (await api.get(`/payments/status/${paymentId}/`)).data,
};

// --- Documents ---
export const documentService = {
  list: async () => (await api.get('/documents/')).data,
  get: async (id) => (await api.get(`/documents/${id}/`)).data,
  upload: async (formData) => (await api.post('/documents/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })).data,
  sendForSigning: async (id, signers, sequential = false) => (await api.post(`/documents/${id}/send_for_signing/`, { signers, sequential })).data,
  auditLog: async (id) => (await api.get(`/documents/${id}/audit_log/`)).data,
  delete: async (id) => (await api.delete(`/documents/${id}/`)).data,
  getPdfUrl: (id) => `${API_BASE_URL}/documents/${id}/pdf/`,
  getFields: async (id) => (await api.get(`/documents/${id}/fields/`)).data,
  saveFields: async (id, fields) => (await api.post(`/documents/${id}/fields/`, { fields })).data,
  download: async (id, title) => {
    const resp = await api.get(`/documents/${id}/download/`, { responseType: 'blob' });
    const blob = resp.data;
    const url = window.URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = title ? `${title}.pdf` : 'document.pdf';
    window.document.body.appendChild(a);
    a.click();
    window.document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },
  bulkSend: async (id, recipients) => (await api.post(`/documents/${id}/bulk_send/`, { recipients })).data,
  sendReminder: async (id, signerId) => {
    const body = signerId ? { signer_id: signerId } : {};
    return (await api.post(`/documents/${id}/send_reminder/`, body)).data;
  },
  downloadAuditCertificate: async (id, title) => {
    const resp = await api.get(`/documents/${id}/audit_certificate/`, { responseType: 'blob' });
    const blob = resp.data;
    const url = window.URL.createObjectURL(blob);
    const a = window.document.createElement('a');
    a.href = url;
    a.download = title ? `audit_certificate_${title}.pdf` : 'audit_certificate.pdf';
    window.document.body.appendChild(a);
    a.click();
    window.document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  },
};

// --- Organisations ---
export const organisationService = {
  list: async () => (await api.get('/organisations/')).data,
  get: async (id) => (await api.get(`/organisations/${id}/`)).data,
  getDetail: async (id) => (await api.get(`/organisations/${id}/`)).data,
  create: async (data) => (await api.post('/organisations/', data)).data,
  update: async (id, data) => (await api.patch(`/organisations/${id}/`, data)).data,
  getMembers: async (id) => (await api.get(`/organisations/${id}/members/`)).data,
  updateMember: async (orgId, membershipId, data) => (await api.patch(`/organisations/${orgId}/members/${membershipId}/`, data)).data,
  removeMember: async (orgId, membershipId) => (await api.delete(`/organisations/${orgId}/members/${membershipId}/`)).data,
  resendMemberSetup: async (orgId, membershipId) => (await api.post(`/organisations/${orgId}/members/${membershipId}/resend-setup/`)).data,
  getBranches: async (orgId) => (await api.get(`/organisations/${orgId}/branches/`)).data,
  createBranch: async (orgId, data) => (await api.post(`/organisations/${orgId}/branches/`, data)).data,
  updateBranch: async (orgId, branchId, data) => (await api.patch(`/organisations/${orgId}/branches/${branchId}/`, data)).data,
  deleteBranch: async (orgId, branchId) => (await api.delete(`/organisations/${orgId}/branches/${branchId}/`)).data,
  requestSalesAccess: async (orgId, data = {}) => (await api.post(`/organisations/${orgId}/request-sales-access/`, data)).data,
  getUsage: async (id) => (await api.get(`/organisations/${id}/usage/`)).data,
  getBranding: async (id) => (await axios.get(`${API_BASE_URL}/organisations/${id}/branding/`)).data,
  getMyOrganisations: async () => api.get('/organisations/my/'),
  createRequest: async (data) => api.post('/organisations/request/', data),
  getMyRequests: async () => api.get('/organisations/requests/'),
  getRequestStatus: async (id) => api.get(`/organisations/request/${id}/`),
  resendVerification: async (id) => api.post(`/organisations/request/${id}/resend/`),
  createMember: async (orgId, data) => api.post(`/organisations/${orgId}/members/create/`, data),
  inviteMember: async (orgId, data) => api.post(`/organisations/${orgId}/invite/`, data),
  getInvitations: async (orgId) => api.get(`/organisations/${orgId}/invitations/`),
  acceptInvitation: async (token) => api.post(`/invitations/${token}/`),
  getInvitationDetails: async (token) => api.get(`/invitations/${token}/`),
  revokeInvitation: async (id) => api.post(`/invitations/${id}/revoke/`),
  checkAutoJoin: async (email) => api.post('/organisations/check-auto-join/', { email }),
  autoJoin: async (orgId) => api.post(`/organisations/${orgId}/auto-join/`),
};

// --- Sales & Invoicing ---
export const salesService = {
  getClients: async (params) => (await api.get('/sales/clients/', { params })).data,
  getClient: async (id) => (await api.get(`/sales/clients/${id}/`)).data,
  createClient: async (data) => (await api.post('/sales/clients/', data)).data,
  updateClient: async (id, data) => (await api.patch(`/sales/clients/${id}/`, data)).data,
  deleteClient: async (id) => (await api.delete(`/sales/clients/${id}/`)).data,
  getDailySales: async (params) => (await api.get('/sales/daily/', { params })).data,
  createDailySale: async (data) => (await api.post('/sales/daily/', data)).data,
  updateDailySale: async (id, data) => (await api.patch(`/sales/daily/${id}/`, data)).data,
  bulkCreateSales: async (data) => (await api.post('/sales/daily/bulk_create/', data)).data,
  getSummary: async (clientId, fromDate, toDate) =>
    (await api.get('/sales/daily/summary/', { params: { client: clientId, from_date: fromDate, to_date: toDate } })).data,
  getDisputes: async (params) => (await api.get('/sales/disputes/', { params })).data,
  createDispute: async (data) => (await api.post('/sales/disputes/', data)).data,
  resolveDispute: async (id, notes, sendEmail) => (await api.post(`/sales/disputes/${id}/resolve/`, { resolution_notes: notes, send_email: sendEmail || false })).data,
  acknowledgeDispute: async (id) => (await api.post(`/sales/disputes/${id}/acknowledge/`)).data,
  confirmDeliveryInApp: async (saleId, note) => (await api.post(`/sales/daily/${saleId}/confirm_in_app/`, { note: note || '' })).data,
  getInvoices: async (params) => (await api.get('/sales/invoices/', { params })).data,
  generateInvoice: async (data) => (await api.post('/sales/invoices/generate/', data)).data,
  downloadInvoice: async (id) => {
    const resp = await api.get(`/sales/invoices/${id}/download/`, { responseType: 'blob' });
    return resp.data;
  },
  sendInvoiceEmail: async (id) => (await api.post(`/sales/invoices/${id}/send_email/`)).data,
  markInvoicePaid: async (id) => (await api.post(`/sales/invoices/${id}/mark_paid/`)).data,
  sendConfirmation: async (saleId, options = {}) => (await api.post(`/sales/daily/${saleId}/send_confirmation/`, options)).data,
  sendBulkConfirmation: async (clientId, fromDate, toDate) =>
    (await api.post('/sales/daily/send_bulk_confirmation/', { client_id: clientId, from_date: fromDate, to_date: toDate })).data,
  getHolidays: async (params) => (await api.get('/sales/holidays/', { params })).data,
  createHoliday: async (data) => (await api.post('/sales/holidays/', data)).data,
};

// --- Delivery Confirmation (public — no auth token) ---
export const confirmationService = {
  getDelivery: async (token) => (await axios.get(`${API_BASE_URL}/confirm-delivery/${token}/`)).data,
  confirm: async (token, note) => (await axios.post(`${API_BASE_URL}/confirm-delivery/${token}/`, { note: note || '' })).data,
  raiseDispute: async (token, disputeType, description) =>
    (await axios.post(`${API_BASE_URL}/confirm-delivery/${token}/dispute/`, {
      dispute_type: disputeType,
      description,
    })).data,
};

// --- Signing (public — no auth token) ---
export const signingService = {
  getDocument: async (token) => (await axios.get(`${API_BASE_URL}/sign/${token}/`)).data,
  sign: async (token, formData) => (await axios.post(`${API_BASE_URL}/sign/${token}/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })).data,
  getPdfUrl: (token) => `${API_BASE_URL}/sign/${token}/pdf/`,
};

// --- Templates ---
export const templateService = {
  list: async (category) => (await api.get('/templates/', { params: category ? { category } : {} })).data,
  get: async (id) => (await api.get(`/templates/${id}/`)).data,
  saveFromDocument: async (data) => (await api.post('/templates/save_from_document/', data)).data,
  useTemplate: async (id, title) => {
    const body = title ? { title } : {};
    return (await api.post(`/templates/${id}/use_template/`, body)).data;
  },
  delete: async (id) => (await api.delete(`/templates/${id}/`)).data,
};

// --- AI Detector ---
export const aiDetectorService = {
  scan: async (file, provider = 'groq') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', provider);
    return (await api.post('/ai-detector/scan/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },
  scanText: async (text, provider = 'groq') => {
    return (await api.post('/ai-detector/scan-text/', { text, provider })).data;
  },
  getScan: async (id) => (await api.get(`/ai-detector/scans/${id}/`)).data,
  reprocessScan: async (id) => (await api.post(`/ai-detector/scans/${id}/`)).data,
  deepScan: async (id) => (await api.post(`/ai-detector/scans/${id}/deep/`)).data,
  getHistory: async () => (await api.get('/ai-detector/history/')).data,
  deleteScan: async (id) => (await api.delete(`/ai-detector/scans/${id}/`)).data,
  getProviders: async () => (await api.get('/ai-detector/providers/')).data,
  getUsage: async () => (await api.get('/ai-detector/usage/')).data,
};

// --- Coupons & Subscriptions ---
export const couponService = {
  generate: async (data) => (await api.post('/coupons/generate/', data)).data,
  grantFree: async (data) => (await api.post('/coupons/grant-free/', data)).data,
  validate: async (code) => (await axios.get(`${API_BASE_URL}/coupons/validate/${code}/`)).data,
  redeem: async (code) => (await api.post('/coupons/redeem/', { code })).data,
  list: async (params) => (await api.get('/coupons/', { params })).data,
  deactivate: async (id) => (await api.patch(`/coupons/${id}/deactivate/`)).data,
};

export const subscriptionService = {
  getMySubscription: async () => (await api.get('/subscriptions/my/')).data,
  getPlans: async () => (await axios.get(`${API_BASE_URL}/subscriptions/plans/`)).data,
};

// --- Chatbot (public — no auth token) ---
export const chatbotService = {
  start: async (page, referrer) => (await axios.post(`${API_BASE_URL}/chatbot/start/`, { page, referrer })).data,
  sendMessage: async (sessionId, message) => (await axios.post(`${API_BASE_URL}/chatbot/${sessionId}/message/`, { message })).data,
  getSession: async (sessionId) => (await axios.get(`${API_BASE_URL}/chatbot/${sessionId}/`)).data,
  // Admin (authenticated)
  getLeads: async (params) => (await api.get('/chatbot/leads/', { params })).data,
  getSessions: async (params) => (await api.get('/chatbot/sessions/', { params })).data,
};

// --- Plagiarism Checker ---
export const plagiarismService = {
  scan: async (file, provider = 'groq') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', provider);
    return (await api.post('/plagiarism/scan/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },
  scanText: async (text, provider = 'groq') => {
    return (await api.post('/plagiarism/scan-text/', { text, provider })).data;
  },
  getHistory: async () => (await api.get('/plagiarism/history/')).data,
  deleteScan: async (id) => (await api.delete(`/plagiarism/scans/${id}/`)).data,
  getProviders: async () => (await api.get('/plagiarism/providers/')).data,
};

// --- Platform Admin (superuser only) ---
export const platformAdminService = {
  getOrgs: async () => (await api.get('/platform/organisations/')).data,
  enableSales: async (orgId) => (await api.post(`/platform/organisations/${orgId}/enable-sales/`)).data,
  disableSales: async (orgId) => (await api.post(`/platform/organisations/${orgId}/disable-sales/`)).data,
  setPlan: async (orgId, plan) => (await api.post(`/platform/organisations/${orgId}/set-plan/`, { plan })).data,
  setStatus: async (orgId, status) => (await api.post(`/platform/organisations/${orgId}/set-status/`, { status })).data,
};

export default api;
