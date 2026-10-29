import React, { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, Grid, Avatar, Chip, Divider, CircularProgress,
} from '@mui/material';
import { authService } from '../../services/api';
import AdBanner from '../Common/AdBanner';

export default function ProfilePage({ user }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfile = async () => {
      try { setProfile(await authService.getProfile()); } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    loadProfile();
  }, []);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  const displayUser = profile || user;

  return (
    <Box>
      <AdBanner user={user} />
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar src={displayUser?.profile_picture} sx={{ width: 80, height: 80, mr: 3 }}>
            {displayUser?.full_name?.charAt(0) || '?'}
          </Avatar>
          <Box>
            <Typography variant="h5">{displayUser?.full_name || 'No name set'}</Typography>
            <Typography variant="body1" color="text.secondary">{displayUser?.email}</Typography>
            {displayUser?.auth_provider && (
              <Chip label={`Signed in with ${displayUser.auth_provider}`} size="small" sx={{ mt: 1 }} />
            )}
          </Box>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}><Typography variant="subtitle2" color="text.secondary">Full Name</Typography><Typography>{displayUser?.full_name || '—'}</Typography></Grid>
          <Grid item xs={12} md={6}><Typography variant="subtitle2" color="text.secondary">Email</Typography><Typography>{displayUser?.email}</Typography></Grid>
          <Grid item xs={12} md={6}><Typography variant="subtitle2" color="text.secondary">Phone</Typography><Typography>{displayUser?.phone || '—'}</Typography></Grid>
          <Grid item xs={12} md={6}><Typography variant="subtitle2" color="text.secondary">Company</Typography><Typography>{displayUser?.company_name || '—'}</Typography></Grid>
        </Grid>
      </Paper>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Subscription</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}><Typography variant="subtitle2" color="text.secondary">Plan</Typography><Chip label={displayUser?.subscription_plan || 'FREE'} color="primary" /></Grid>
          <Grid item xs={12} md={4}><Typography variant="subtitle2" color="text.secondary">Documents Remaining</Typography><Typography variant="h6">{displayUser?.documents_remaining ?? '?'}</Typography></Grid>
          <Grid item xs={12} md={4}><Typography variant="subtitle2" color="text.secondary">Documents Used</Typography><Typography variant="h6">{displayUser?.documents_used_this_month ?? '0'}</Typography></Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
