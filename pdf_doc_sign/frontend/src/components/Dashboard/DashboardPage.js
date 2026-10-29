import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Grid, Card, CardContent, Chip,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DescriptionIcon from '@mui/icons-material/Description';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import AdBanner from '../Common/AdBanner';

export default function DashboardPage({ user }) {
  const navigate = useNavigate();
  const canAccessSales = user?.can_access_sales;
  const isClientUser = user?.is_client_user;

  if (isClientUser) {
    return (
      <Box>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>Welcome to Your Delivery Portal!</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            View your deliveries, acknowledge receipt, and raise any concerns.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/deliveries')}>
                <CardContent>
                  <LocalShippingIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h6">My Deliveries</Typography>
                  <Typography variant="body2" color="text.secondary">View items delivered to you</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/disputes')}>
                <CardContent>
                  <ReportProblemIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h6">Raise a Concern</Typography>
                  <Typography variant="body2" color="text.secondary">Report missing or incorrect items</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <AdBanner user={user} />
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Welcome to SignSimple!</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>Sign PDF documents securely and legally.</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={canAccessSales ? 4 : 6}>
            <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/documents/upload')}>
              <CardContent>
                <UploadFileIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">Upload Document</Typography>
                <Typography variant="body2" color="text.secondary">Upload a PDF to get it signed securely</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={canAccessSales ? 4 : 6}>
            <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/documents')}>
              <CardContent>
                <DescriptionIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h6">My Documents</Typography>
                <Typography variant="body2" color="text.secondary">View and manage your documents</Typography>
              </CardContent>
            </Card>
          </Grid>
          {canAccessSales && (
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 4 } }} onClick={() => navigate('/sales')}>
                <CardContent>
                  <PointOfSaleIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h6">Daily Sales</Typography>
                  <Typography variant="body2" color="text.secondary">Track deliveries and generate invoices</Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </Paper>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Quick Stats</Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} md={3}><Typography variant="subtitle2" color="text.secondary">Plan</Typography><Typography variant="h6">{user?.subscription_plan || 'FREE'}</Typography></Grid>
          <Grid item xs={6} md={3}><Typography variant="subtitle2" color="text.secondary">Documents Left</Typography><Typography variant="h6">{user?.documents_remaining ?? '10'}</Typography></Grid>
          <Grid item xs={6} md={3}><Typography variant="subtitle2" color="text.secondary">Signed In Via</Typography><Typography variant="h6" sx={{ textTransform: 'capitalize' }}>{user?.auth_provider || 'Email'}</Typography></Grid>
          <Grid item xs={6} md={3}><Typography variant="subtitle2" color="text.secondary">Account Status</Typography><Chip label="Active" color="success" size="small" /></Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
