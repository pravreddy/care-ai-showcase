/**
 * Layout.js — Main app shell with sidebar navigation and content routing.
 * 
 * All page components are in their own files:
 *   Dashboard/DashboardPage.js
 *   Documents/DocumentsPage.js, Documents/UploadPage.js
 *   Profile/ProfilePage.js
 *   Subscription/SubscriptionPage.js
 *   Organisation/OrganisationPage.js
 *   Sales/DailySalesEntry.js, Sales/InvoiceGenerator.js, Sales/ClientsManager.js
 */
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, Avatar, Menu, MenuItem,
  Container, Paper, Chip, Divider,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';
import DescriptionIcon from '@mui/icons-material/Description';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PersonIcon from '@mui/icons-material/Person';
import PaymentIcon from '@mui/icons-material/Payment';
import BusinessIcon from '@mui/icons-material/Business';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import LogoutIcon from '@mui/icons-material/Logout';
import PeopleIcon from '@mui/icons-material/People';
import { authService, organisationService } from '../../services/api';

// Page components — each in its own file
import DashboardPage from '../Dashboard/DashboardPage';
import DocumentsPage from '../Documents/DocumentsPage';
import UploadPage from '../Documents/UploadPage';
import ProfilePage from '../Profile/ProfilePage';
import SubscriptionPage from '../Subscription/SubscriptionPage';
import OrganisationPage from '../Organisation/OrganisationPage';
import DailySalesEntry from '../Sales/DailySalesEntry';
import InvoiceGenerator from '../Sales/InvoiceGenerator';
import ClientsManager from '../Sales/ClientsManager';
import MyDeliveriesPage from '../Sales/MyDeliveriesPage';
import MyDisputesPage from '../Sales/MyDisputesPage';
import TemplatesPage from '../Templates/TemplatesPage';
import PlatformAdminPage from '../Platform/PlatformAdminPage';
import CouponAdminPage from '../Platform/CouponAdminPage';
import AIDetectorPage from '../AIDetector/AIDetectorPage';
import PlagiarismPage from '../Plagiarism/PlagiarismPage';

const DRAWER_WIDTH = 240;

export default function Layout({ page }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [orgs, setOrgs] = useState([]);
  const [activeOrgId, setActiveOrgId] = useState(localStorage.getItem('activeOrgId') || '');

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) setUser(JSON.parse(stored));

    // Fetch user's organisations and auto-select if single org
    organisationService.getMyOrganisations()
      .then((res) => {
        const orgList = res.data || [];
        setOrgs(orgList);
        const savedOrgId = localStorage.getItem('activeOrgId');
        if (orgList.length === 1) {
          // Auto-select single org
          const orgId = orgList[0].organisation_id;
          localStorage.setItem('activeOrgId', orgId);
          localStorage.setItem('activeOrgName', orgList[0].organisation_name);
          setActiveOrgId(orgId);
        } else if (savedOrgId && orgList.some((o) => o.organisation_id === savedOrgId)) {
          // Saved org is still valid
          setActiveOrgId(savedOrgId);
        } else if (orgList.length > 1) {
          // Clear invalid saved org
          localStorage.removeItem('activeOrgId');
          localStorage.removeItem('activeOrgName');
          setActiveOrgId('');
        }
      })
      .catch(() => {});
  }, []);

  const handleOrgChange = (orgId) => {
    const org = orgs.find((o) => o.organisation_id === orgId);
    if (org) {
      localStorage.setItem('activeOrgId', orgId);
      localStorage.setItem('activeOrgName', org.organisation_name);
      setActiveOrgId(orgId);
      // Reload page to refresh data with new org context
      window.location.reload();
    }
  };

  const handleLogout = async () => { await authService.logout(); navigate('/login'); };
  const canAccessSales = user?.can_access_sales;
  const isClientUser = user?.is_client_user;
  const isSuperuser = user?.is_platform_admin || user?.is_superuser; // is_platform_admin covers Avyangah org admins too

  // ─── Build sidebar navigation ───
  let navSections = [];
  if (isClientUser) {
    navSections = [
      { label: 'Deliveries', items: [
        { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
        { label: 'My Deliveries', icon: <LocalShippingIcon />, path: '/deliveries' },
        { label: 'Raise Concern', icon: <ReportProblemIcon />, path: '/disputes' },
      ]},
      { label: 'Account', items: [
        { label: 'Profile', icon: <PersonIcon />, path: '/profile' },
      ]},
    ];
  } else {
    navSections = [
      { label: 'Main', items: [
        { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
        { label: 'Documents', icon: <DescriptionIcon />, path: '/documents' },
        { label: 'Upload', icon: <UploadFileIcon />, path: '/documents/upload' },
        { label: 'Templates', icon: <DescriptionIcon />, path: '/templates' },
        { label: 'AI Detector', icon: <SmartToyIcon />,   path: '/ai-detector' },
        { label: 'Plagiarism',   icon: <ContentCopyIcon />, path: '/plagiarism' },
      ]},
    ];
    if (canAccessSales) {
      navSections.push({ label: 'Sales & Invoicing', items: [
        { label: 'Clients', icon: <PeopleIcon />, path: '/sales/clients' },
        { label: 'Daily Sales', icon: <PointOfSaleIcon />, path: '/sales' },
        { label: 'Invoices', icon: <ReceiptLongIcon />, path: '/sales/invoices' },
        { label: 'Concerns', icon: <ReportProblemIcon />, path: '/disputes' },
      ]});
    }
    navSections.push({ label: 'Settings', items: [
      { label: 'Organisation', icon: <BusinessIcon />, path: '/organisation' },
      { label: 'Profile', icon: <PersonIcon />, path: '/profile' },
      { label: 'Subscription', icon: <PaymentIcon />, path: '/subscription' },
    ]});
    if (isSuperuser) {
      navSections.push({ label: 'Platform', items: [
        { label: 'Admin Panel', icon: <AdminPanelSettingsIcon />, path: '/platform-admin' },
        { label: 'Coupons', icon: <CardGiftcardIcon />, path: '/coupons-admin' },
      ]});
    }
  }

  // ─── Route to the right page component ───
  const renderPageContent = () => {
    switch (page) {
      case 'dashboard':     return <DashboardPage user={user} />;
      case 'documents':     return <DocumentsPage user={user} />;
      case 'upload':        return <UploadPage user={user} />;
      case 'templates':    return <TemplatesPage />;
      case 'profile':       return <ProfilePage user={user} />;
      case 'subscription':  return <SubscriptionPage user={user} />;
      case 'organisation':  return <OrganisationPage user={user} />;
      case 'clients':       return <ClientsManager />;
      case 'sales':         return <DailySalesEntry />;
      case 'invoices':      return <InvoiceGenerator />;
      case 'deliveries':    return <MyDeliveriesPage user={user} />;
      case 'disputes':      return <MyDisputesPage user={user} />;
      case 'platform-admin': return <PlatformAdminPage user={user} />;
      case 'coupons-admin': return <CouponAdminPage user={user} />;
      case 'ai-detector':   return <AIDetectorPage />;
      case 'plagiarism':     return <PlagiarismPage />;
      default:
        return (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ textTransform: 'capitalize' }}>{page}</Typography>
            <Typography variant="body1" color="text.secondary">This section is coming soon.</Typography>
          </Paper>
        );
    }
  };

  const getPageTitle = () => {
    const titles = {
      dashboard: 'Dashboard', documents: 'Documents', upload: 'Upload', templates: 'Templates',
      profile: 'Profile', subscription: 'Subscription', organisation: 'Organisation',
      clients: 'Clients', sales: 'Daily Sales', invoices: 'Invoice Generator',
      deliveries: 'My Deliveries', disputes: 'Concerns', 'ai-detector': 'AI Detector',
      'coupons-admin': 'Coupons & Access',
    };
    return titles[page] || page;
  };

  return (
    <Box sx={{ display: 'flex' }}>
      {/* ─── Sidebar ─── */}
      <Drawer variant="permanent" sx={{ width: DRAWER_WIDTH, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}>
        <Toolbar>
          <Typography variant="h6" fontWeight={700} color="primary" noWrap sx={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            SignSimple
          </Typography>
        </Toolbar>
        {navSections.map((section, si) => (
          <Box key={section.label}>
            {si > 0 && <Divider sx={{ my: 0.5 }} />}
            <Typography variant="caption" color="text.secondary" fontWeight={600}
              sx={{ px: 2, pt: 1.5, pb: 0.5, display: 'block', textTransform: 'uppercase', letterSpacing: 1 }}>
              {section.label}
            </Typography>
            <List dense disablePadding>
              {section.items.map((item) => (
                <ListItemButton key={item.path} selected={location.pathname === item.path} onClick={() => navigate(item.path)} sx={{ py: 0.8 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: '0.9rem' }} />
                </ListItemButton>
              ))}
            </List>
          </Box>
        ))}
        {!isClientUser && user?.subscription_plan === 'FREE' && (
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.main', color: 'white', borderRadius: 2, cursor: 'pointer' }} onClick={() => navigate('/checkout')}>
              <ShoppingCartIcon sx={{ mb: 0.5 }} />
              <Typography variant="body2" fontWeight={600}>Upgrade Plan</Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>From £2.50/month</Typography>
            </Paper>
          </Box>
        )}
      </Drawer>

      {/* ─── Main content ─── */}
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="sticky" color="inherit" elevation={1}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1, textTransform: 'capitalize' }}>{getPageTitle()}</Typography>
            {/* Org selector for multi-org users */}
            {orgs.length > 1 && (
              <Box sx={{ mr: 2 }}>
                <select
                  value={activeOrgId}
                  onChange={(e) => handleOrgChange(e.target.value)}
                  style={{
                    padding: '6px 12px', borderRadius: 8, border: '1px solid #ccc',
                    fontSize: '0.85rem', background: 'white', cursor: 'pointer',
                  }}
                >
                  <option value="">Select Organisation</option>
                  {orgs.map((o) => (
                    <option key={o.organisation_id} value={o.organisation_id}>
                      {o.organisation_name} ({o.role_display})
                    </option>
                  ))}
                </select>
              </Box>
            )}
            {/* Single-org: show org name */}
            {orgs.length === 1 && (
              <Chip label={orgs[0].organisation_name} size="small" variant="outlined" sx={{ mr: 1 }} />
            )}
            {user && !isClientUser && (
              <Chip label={`${user.subscription_plan} · ${user.documents_remaining ?? '?'} docs left`} size="small" variant="outlined" color="primary" sx={{ mr: 2 }} />
            )}
            {isClientUser && <Chip label="Client Portal" size="small" color="secondary" sx={{ mr: 2 }} />}
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <Avatar src={user?.profile_picture} sx={{ width: 32, height: 32 }}>{user?.full_name?.charAt(0) || '?'}</Avatar>
            </IconButton>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
              <MenuItem disabled><Typography variant="body2">{user?.email}</Typography></MenuItem>
              <MenuItem onClick={() => { setAnchorEl(null); navigate('/profile'); }}><PersonIcon sx={{ mr: 1 }} fontSize="small" /> Profile</MenuItem>
              {!isClientUser && <MenuItem onClick={() => { setAnchorEl(null); navigate('/checkout'); }}><ShoppingCartIcon sx={{ mr: 1 }} fontSize="small" /> Upgrade</MenuItem>}
              <MenuItem onClick={handleLogout}><LogoutIcon sx={{ mr: 1 }} fontSize="small" /> Logout</MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>
        <Container maxWidth="xl" sx={{ py: 4 }}>{renderPageContent()}</Container>
      </Box>
    </Box>
  );
}
