import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Grid, Card, CardContent, CardActions,
  Button, Chip, Divider, LinearProgress,
} from '@mui/material';
import PaymentIcon from '@mui/icons-material/Payment';
import StarIcon from '@mui/icons-material/Star';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';

export default function SubscriptionPage({ user }) {
  const navigate = useNavigate();
  const docsUsed = user?.documents_used_this_month || 0;
  const docsLimit = user?.documents_limit || 10;
  const docsRemaining = user?.documents_remaining || 10;
  const usagePercent = (docsUsed / docsLimit) * 100;

  const plans = [
    { name: 'FREE', price: '£0', period: 'forever', features: ['10 documents/month', 'Basic e-signatures', 'Email support'], current: user?.subscription_plan === 'FREE' },
    { name: 'STARTER', price: '£2.50', period: '/month', features: ['50 documents/month', 'Advanced signatures', 'Priority support', 'No ads'], current: user?.subscription_plan === 'STARTER', popular: true },
    { name: 'PROFESSIONAL', price: '£9.99', period: '/month', features: ['Unlimited documents', 'Team collaboration', 'API access', 'Custom branding', 'Dedicated support'], current: user?.subscription_plan === 'PROFESSIONAL' },
  ];

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 3 }}><PaymentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Your Subscription</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}><Typography variant="subtitle2" color="text.secondary">Current Plan</Typography><Chip label={user?.subscription_plan || 'FREE'} color={user?.subscription_plan === 'FREE' ? 'default' : 'primary'} sx={{ mt: 0.5 }} /></Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">Documents This Month</Typography>
            <Typography variant="h4">{docsUsed} / {docsLimit}</Typography>
            <LinearProgress variant="determinate" value={usagePercent} sx={{ mt: 1, height: 8, borderRadius: 4 }} color={usagePercent > 80 ? 'warning' : 'primary'} />
          </Grid>
          <Grid item xs={12} md={4}><Typography variant="subtitle2" color="text.secondary">Documents Remaining</Typography><Typography variant="h4" color={docsRemaining < 3 ? 'warning.main' : 'text.primary'}>{docsRemaining}</Typography></Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" sx={{ mb: 2 }}>Available Plans</Typography>
      <Grid container spacing={3}>
        {plans.map((plan) => (
          <Grid item xs={12} md={4} key={plan.name}>
            <Card variant={plan.popular ? 'elevation' : 'outlined'} sx={{ height: '100%', position: 'relative', border: plan.current ? '2px solid #1976d2' : undefined, boxShadow: plan.popular ? 4 : undefined }}>
              {plan.popular && <Chip label="Most Popular" color="primary" size="small" icon={<StarIcon />} sx={{ position: 'absolute', top: -12, right: 16 }} />}
              <CardContent>
                <Typography variant="h6">{plan.name}</Typography>
                <Box sx={{ my: 2 }}><Typography variant="h3" component="span">{plan.price}</Typography><Typography variant="body2" component="span" color="text.secondary">{plan.period}</Typography></Box>
                <Divider sx={{ my: 2 }} />
                {plan.features.map((f, i) => <Typography key={i} variant="body2" sx={{ py: 0.5 }}>✓ {f}</Typography>)}
              </CardContent>
              <CardActions sx={{ p: 2, pt: 0 }}>
                {plan.current ? <Button fullWidth variant="outlined" disabled>Current Plan</Button>
                  : <Button fullWidth variant={plan.popular ? 'contained' : 'outlined'} onClick={() => navigate('/checkout')} startIcon={<RocketLaunchIcon />}>{plan.price === '£0' ? 'Downgrade' : 'Upgrade'}</Button>}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
