import React from 'react';
import { Paper, Box, Typography, Avatar, Chip, Divider, Grid } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import { getStatusColor } from './useDocumentData';

/**
 * Document info card showing title, status badge, and metadata grid.
 */
export default function DocumentInfoCard({ document }) {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mr: 2 }}>
          <DescriptionIcon fontSize="large" />
        </Avatar>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h5">{document.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            {document.description || 'No description'}
          </Typography>
        </Box>
        <Chip label={document.status} color={getStatusColor(document.status)} size="large" />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Grid container spacing={3}>
        <Grid item xs={6} md={3}>
          <Typography variant="subtitle2" color="text.secondary">File Size</Typography>
          <Typography variant="body1">{document.file_size_mb} MB</Typography>
          {document.was_compressed && (
            <Typography variant="caption" color="success.main">
              Compressed {document.compression_savings}%
            </Typography>
          )}
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="subtitle2" color="text.secondary">Pages</Typography>
          <Typography variant="body1">{document.page_count || '—'}</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="subtitle2" color="text.secondary">Created</Typography>
          <Typography variant="body1">{new Date(document.created_at).toLocaleDateString()}</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="subtitle2" color="text.secondary">Expires</Typography>
          <Typography variant="body1">
            {document.expires_at ? new Date(document.expires_at).toLocaleDateString() : 'N/A'}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );
}
