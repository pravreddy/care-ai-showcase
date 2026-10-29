/**
 * DocumentInfoCard.js — Shows document title, size, pages, and signing progress.
 */
import React from 'react';
import { Box, Paper, Typography, Chip } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';

export default function DocumentInfoCard({ document, signer, sigFieldCount, filledSigCount }) {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <DescriptionIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h5">{document?.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            {document?.file_size_mb} MB · {document?.page_count || '?'} page(s) — Expires{' '}
            {signer?.access_expires_at ? new Date(signer.access_expires_at).toLocaleDateString() : 'N/A'}
          </Typography>
        </Box>
        {sigFieldCount > 0 && (
          <Chip
            label={`${filledSigCount}/${sigFieldCount} signed`}
            color={filledSigCount === sigFieldCount ? 'success' : 'warning'}
            size="small"
          />
        )}
      </Box>
    </Paper>
  );
}
