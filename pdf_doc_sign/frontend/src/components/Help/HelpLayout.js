import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Container, Typography, Button, AppBar, Toolbar, Tabs, Tab,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

const HELP_TABS = [
  { label: 'Help Centre', path: '/help' },
  { label: 'How to Sign', path: '/help/how-to-sign' },
  { label: 'How to Send', path: '/help/how-to-send' },
  { label: 'Signatures', path: '/help/how-to-create-signatures' },
  { label: 'Fields', path: '/help/how-to-use-fields' },
  { label: 'Templates', path: '/help/how-to-templates' },
  { label: 'Sales & Invoicing', path: '/help/sales-invoicing' },
  { label: 'FAQ', path: '/help/faq' },
];

export default function HelpLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  const currentTab = HELP_TABS.findIndex((t) => t.path === location.pathname);

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#fafbfc' }}>
      <AppBar position="static" color="inherit" elevation={1}>
        <Toolbar>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mr: 2 }}>
            Home
          </Button>
          <Typography variant="h6" fontWeight={700} color="primary" sx={{ flexGrow: 1 }}>
            SignSimple Help
          </Typography>
          <Button variant="outlined" size="small" onClick={() => navigate('/login')}>
            Sign In
          </Button>
        </Toolbar>
        <Tabs
          value={currentTab >= 0 ? currentTab : 0}
          onChange={(e, idx) => navigate(HELP_TABS[idx].path)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ px: 2 }}
        >
          {HELP_TABS.map((tab) => (
            <Tab key={tab.path} label={tab.label} />
          ))}
        </Tabs>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 5 }}>
        {children}
      </Container>

      <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
        <Typography variant="body2">
          &copy; 2026 Avyangah Technologies Limited (08235853) &mdash;{' '}
          <a href="https://signsimple.co.uk" style={{ color: 'inherit' }}>signsimple.co.uk</a>
        </Typography>
      </Box>
    </Box>
  );
}
