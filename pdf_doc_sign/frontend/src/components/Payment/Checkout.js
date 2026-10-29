import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container, Box, Paper, Typography, Button, Grid, Stack, Chip,
  ToggleButton, ToggleButtonGroup, CircularProgress, Alert, Divider,
} from '@mui/material';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import BoltIcon from '@mui/icons-material/Bolt';
import { paymentService } from '../../services/api';

export default function Checkout() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedPlan = searchParams.get('plan') || '';

  const [plans, setPlans] = useState(null);
  const [providers, setProviders] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(preselectedPlan);
  const [paymentMethod, setPaymentMethod] = useState('open_banking');
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      paymentService.getPlans(),
      paymentService.getProviders(),
    ]).then(([plansData, providersData]) => {
      setPlans(plansData);
      setProviders(providersData);
      // Default to open_banking if available, else card
      if (!providersData.open_banking?.available && providersData.card?.available) {
        setPaymentMethod('card');
      }
    }).catch(() => setError('Failed to load payment options'));
  }, []);

  const handleCheckout = async () => {
    if (!selectedPlan) { setError('Please select a plan'); return; }
    setLoading(true);
    setError('');

    try {
      const resp = await paymentService.checkout({
        plan: selectedPlan,
        payment_method: paymentMethod,
        quantity: selectedPlan === 'EXTRA_DOCS' ? quantity : 1,
      });
      // Redirect to payment provider
      window.location.href = resp.checkout_url;
    } catch (err) {
      setError(err.response?.data?.error || 'Payment failed. Please try again.');
      setLoading(false);
    }
  };

  if (!plans || !providers) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  const planOptions = [
    { key: 'STARTER', ...plans.plans.STARTER, highlight: false },
    { key: 'PROFESSIONAL', ...plans.plans.PROFESSIONAL, highlight: true },
    { key: 'EXTRA_DOCS', name: 'Extra Documents', price_gbp: plans.extra_docs.price_gbp, description: `£${plans.extra_docs.price_gbp} per ${plans.extra_docs.bundle_size} documents`, highlight: false },
  ];

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Upgrade Your Plan
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Choose your plan and payment method. Upgrade or buy extra documents instantly.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Plan Selection */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {planOptions.map((plan) => (
          <Grid item xs={12} md={4} key={plan.key}>
            <Paper
              elevation={selectedPlan === plan.key ? 6 : 1}
              onClick={() => setSelectedPlan(plan.key)}
              sx={{
                p: 3, cursor: 'pointer', textAlign: 'center',
                border: selectedPlan === plan.key ? '2px solid' : '1px solid #eee',
                borderColor: selectedPlan === plan.key ? 'primary.main' : '#eee',
                transition: 'all 0.2s',
                '&:hover': { borderColor: 'primary.main', transform: 'translateY(-2px)' },
              }}
            >
              {plan.highlight && (
                <Chip label="BEST VALUE" color="primary" size="small" sx={{ mb: 1 }} />
              )}
              <Typography variant="h6" fontWeight={600}>{plan.name}</Typography>
              <Typography sx={{ fontSize: '2rem', fontWeight: 800, my: 1 }}>
                £{plan.price_gbp}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {plan.key === 'EXTRA_DOCS' ? 'one-off' : 'per month'}
              </Typography>
              {plan.documents_per_month && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {plan.documents_per_month.toLocaleString()} docs/month
                </Typography>
              )}
              {selectedPlan === plan.key && (
                <CheckCircleIcon color="primary" sx={{ mt: 1 }} />
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Extra docs quantity */}
      {selectedPlan === 'EXTRA_DOCS' && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            How many bundles? (100 documents each)
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button size="small" variant="outlined" onClick={() => setQuantity(Math.max(1, quantity - 1))}>−</Button>
            <Typography variant="h5" fontWeight={700} sx={{ px: 2 }}>{quantity}</Typography>
            <Button size="small" variant="outlined" onClick={() => setQuantity(quantity + 1)}>+</Button>
            <Typography color="text.secondary" sx={{ ml: 2 }}>
              = {quantity * 100} documents for £{(quantity * plans.extra_docs.price_gbp).toFixed(2)}
            </Typography>
          </Stack>
        </Paper>
      )}

      {/* Payment Method Selection */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Payment Method
        </Typography>
        <ToggleButtonGroup
          value={paymentMethod}
          exclusive
          onChange={(_, val) => val && setPaymentMethod(val)}
          fullWidth
          sx={{ mt: 1 }}
        >
          {providers.open_banking?.available && (
            <ToggleButton value="open_banking" sx={{ py: 2, textTransform: 'none' }}>
              <Stack alignItems="center" spacing={0.5}>
                <AccountBalanceIcon />
                <Typography fontWeight={600}>Pay by Bank</Typography>
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <BoltIcon sx={{ fontSize: 14, color: 'success.main' }} />
                  <Typography variant="caption" color="success.main">Instant & free</Typography>
                </Stack>
              </Stack>
            </ToggleButton>
          )}
          {providers.card?.available && (
            <ToggleButton value="card" sx={{ py: 2, textTransform: 'none' }}>
              <Stack alignItems="center" spacing={0.5}>
                <CreditCardIcon />
                <Typography fontWeight={600}>Pay by Card</Typography>
                <Typography variant="caption" color="text.secondary">Visa, Mastercard</Typography>
              </Stack>
            </ToggleButton>
          )}
        </ToggleButtonGroup>

        {paymentMethod === 'open_banking' && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            You'll be redirected to select your bank and approve the payment instantly. No card details needed.
          </Typography>
        )}
      </Paper>

      <Divider sx={{ mb: 3 }} />

      {/* Checkout Button */}
      <Button
        variant="contained" size="large" fullWidth
        onClick={handleCheckout}
        disabled={!selectedPlan || loading}
        sx={{ py: 1.5, fontWeight: 700, fontSize: '1.1rem', textTransform: 'none' }}
      >
        {loading ? <CircularProgress size={24} /> : (
          selectedPlan === 'EXTRA_DOCS'
            ? `Pay £${(quantity * plans.extra_docs.price_gbp).toFixed(2)} for ${quantity * 100} documents`
            : selectedPlan
              ? `Subscribe for £${plans.plans[selectedPlan]?.price_gbp}/month`
              : 'Select a plan'
        )}
      </Button>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 2 }}>
        Payments processed securely. Cancel anytime. No hidden fees.
      </Typography>
    </Container>
  );
}
