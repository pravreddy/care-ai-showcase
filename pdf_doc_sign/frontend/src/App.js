import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { HelmetProvider } from 'react-helmet-async';

import Landing from './components/Landing/Landing';
import FreeSignTool from './components/Landing/FreeSignTool';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import OAuthCallback from './components/Auth/OAuthCallback';
import SetPassword from './components/Auth/SetPassword';
import ForgotPassword from './components/Auth/ForgotPassword';
import SigningPage from './components/Signing/SigningPage';
import Checkout from './components/Payment/Checkout';
import PaymentSuccess from './components/Payment/PaymentSuccess';
import PaymentCancel from './components/Payment/PaymentCancel';
import PrivateRoute from './components/Common/PrivateRoute';
import Layout from './components/Common/Layout';
import SendForSigning from './components/Common/SendForSigning';
import DocumentView from './components/DocumentView';
import PrepareDocument from './components/Documents/PrepareDocument';
import ConfirmDeliveryPage from './components/Sales/ConfirmDeliveryPage';
import ChatWidget from './components/Chatbot/ChatWidget';
import HelpHub from './components/Help/HelpHub';
import HowToSign from './components/Help/HowToSign';
import AICheckerPage from './components/AIChecker/AICheckerPage';
import HowToSend from './components/Help/HowToSend';
import HowToTemplates from './components/Help/HowToTemplates';
import FAQ from './components/Help/FAQ';
import HowToCreateSignatures from './components/Help/HowToCreateSignatures';
import HowToUseFields from './components/Help/HowToUseFields';
import SalesHelp from './components/Help/SalesHelp';

const theme = createTheme({
  palette: {
    primary: { main: '#1565c0' },
    secondary: { main: '#f57c00' },
    background: { default: '#fafbfc' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: { borderRadius: 10 },
});

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

function App() {
  return (
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
        <HelmetProvider>
          <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Routes>
              {/* Public */}
              <Route path="/" element={<Landing />} />
              <Route path="/free-electronic-signature" element={<FreeSignTool />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/oauth/callback" element={<OAuthCallback />} />

              {/* Password Reset */}
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/set-password/:token" element={<SetPassword />} />

              {/* Public pages (no login needed) */}
              <Route path="/sign/:token" element={<SigningPage />} />
              <Route path="/confirm-delivery/:token" element={<ConfirmDeliveryPage />} />

              {/* Help Pages (public) */}
              <Route path="/help" element={<HelpHub />} />
              <Route path="/help/how-to-sign" element={<HowToSign />} />
              <Route path="/help/how-to-send" element={<HowToSend />} />
              <Route path="/help/how-to-create-signatures" element={<HowToCreateSignatures />} />
              <Route path="/help/how-to-use-fields" element={<HowToUseFields />} />
              <Route path="/help/how-to-templates" element={<HowToTemplates />} />
              <Route path="/help/sales-invoicing" element={<SalesHelp />} />
              <Route path="/help/faq" element={<FAQ />} />

              {/* Payment */}
              <Route path="/checkout" element={<PrivateRoute><Checkout /></PrivateRoute>} />
              <Route path="/payment/success" element={<PrivateRoute><PaymentSuccess /></PrivateRoute>} />
              <Route path="/payment/cancel" element={<PrivateRoute><PaymentCancel /></PrivateRoute>} />

              {/* Sales & Invoicing */}
              <Route path="/sales" element={<PrivateRoute><Layout page="sales" /></PrivateRoute>} />
              <Route path="/sales/clients" element={<PrivateRoute><Layout page="clients" /></PrivateRoute>} />
              <Route path="/sales/invoices" element={<PrivateRoute><Layout page="invoices" /></PrivateRoute>} />

              {/* Document Signing Flow */}
              <Route path="/documents/:id" element={<PrivateRoute><DocumentView /></PrivateRoute>} />
              <Route path="/documents/:id/prepare" element={<PrivateRoute><PrepareDocument /></PrivateRoute>} />
              <Route path="/documents/:id/send" element={<PrivateRoute><SendForSigning /></PrivateRoute>} />

              {/* Dashboard pages (wrapped in Layout with sidebar) */}
              <Route path="/dashboard" element={<PrivateRoute><Layout page="dashboard" /></PrivateRoute>} />
              <Route path="/documents" element={<PrivateRoute><Layout page="documents" /></PrivateRoute>} />
              <Route path="/templates" element={<PrivateRoute><Layout page="templates" /></PrivateRoute>} />
              <Route path="/documents/upload" element={<PrivateRoute><Layout page="upload" /></PrivateRoute>} />
              <Route path="/profile" element={<PrivateRoute><Layout page="profile" /></PrivateRoute>} />
              <Route path="/subscription" element={<PrivateRoute><Layout page="subscription" /></PrivateRoute>} />
              <Route path="/organisation" element={<PrivateRoute><Layout page="organisation" /></PrivateRoute>} />
              <Route path="/deliveries" element={<PrivateRoute><Layout page="deliveries" /></PrivateRoute>} />
              <Route path="/disputes" element={<PrivateRoute><Layout page="disputes" /></PrivateRoute>} />
              <Route path="/ai-detector" element={<PrivateRoute><Layout page="ai-detector" /></PrivateRoute>} />
              <Route path="/plagiarism" element={<PrivateRoute><Layout page="plagiarism" /></PrivateRoute>} />
              <Route path="/ai-checker" element={<AICheckerPage />} />
              <Route path="/platform-admin" element={<PrivateRoute><Layout page="platform-admin" /></PrivateRoute>} />
              <Route path="/coupons-admin" element={<PrivateRoute><Layout page="coupons-admin" /></PrivateRoute>} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>

            {/* AI Chatbot — floating widget on public pages */}
            <ChatWidget />
          </Router>
          </ThemeProvider>
        </HelmetProvider>
      </GoogleOAuthProvider>
  );
}

export default App;
