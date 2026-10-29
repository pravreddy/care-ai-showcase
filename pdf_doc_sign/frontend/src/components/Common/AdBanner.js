import React from 'react';
import { Box, Paper, Typography, Button } from '@mui/material';

export default function AdBanner({ user }) {
  if (user?.subscription_plan !== 'FREE') return null;

  return (
    <Paper
      sx={{
        p: 2, mb: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white', borderRadius: 2,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="subtitle1" fontWeight={600}>
            🚀 Upgrade to Pro for unlimited documents!
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Get unlimited signatures, priority support, and no ads — from just £2.50/month
          </Typography>
        </Box>
        <Button
          variant="contained"
          sx={{ bgcolor: 'white', color: '#764ba2', '&:hover': { bgcolor: '#f0f0f0' } }}
          href="/checkout"
        >
          Upgrade Now
        </Button>
      </Box>
    </Paper>
  );
}
