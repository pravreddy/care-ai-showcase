/**
 * UploadAlerts.js — Reusable error/success alert banner.
 */
import React from 'react';
import { Alert } from '@mui/material';

export default function UploadAlerts({ error, success, onClearError, onClearSuccess }) {
  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={onClearError}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={onClearSuccess}>
          {success}
        </Alert>
      )}
    </>
  );
}
