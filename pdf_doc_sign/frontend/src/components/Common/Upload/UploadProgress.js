/**
 * UploadProgress.js — Progress bar during upload.
 */
import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

export default function UploadProgress({ progress }) {
  return (
    <Box sx={{ mt: 3 }}>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ height: 8, borderRadius: 4 }}
      />
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
        Uploading & optimising... {progress}%
      </Typography>
    </Box>
  );
}
