/**
 * UploadPage.js — Upload PDF and proceed to field placement.
 *
 * Uses:
 *   - useUpload hook for upload state management
 *   - FileDropZone for drag-and-drop file selection
 *   - UploadAlerts for error/success messages
 *   - UploadProgress for progress bar
 *   - errorHandling utils for client-side file validation
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Button, TextField,
  Alert, Stepper, Step, StepLabel,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SendIcon from '@mui/icons-material/Send';
import AdBanner from '../Common/AdBanner';
import { FileDropZone, UploadAlerts, UploadProgress } from '../Common/Upload';
import useUpload from '../../hooks/useUpload';

export default function UploadPage({ user }) {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');

  const {
    uploading, progress, error, success,
    handleUpload, setError, setSuccess, maxFileSizeMB,
  } = useUpload((result) => {
    setTimeout(() => navigate(`/documents/${result.id}/prepare`), 1500);
  });

  const canUpload = user?.documents_remaining > 0;
  const isFileTooLarge = file && file.size > maxFileSizeMB * 1024 * 1024;

  return (
    <Box>
      <AdBanner user={user} />

      <UploadAlerts
        error={error}
        success={success}
        onClearError={() => setError('')}
        onClearSuccess={() => setSuccess('')}
      />

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 3 }}>
          <CloudUploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Upload Document
        </Typography>

        {/* Usage warning */}
        {!canUpload && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            You've used all your documents this month ({user?.documents_limit || 10} limit).
            <Button size="small" sx={{ ml: 1 }} onClick={() => navigate('/checkout')}>Upgrade Plan</Button>
          </Alert>
        )}

        {/* Progress stepper */}
        <Stepper activeStep={file ? 1 : 0} sx={{ mb: 4 }}>
          <Step><StepLabel>Upload Document</StepLabel></Step>
          <Step><StepLabel>Place Signature Fields</StepLabel></Step>
          <Step><StepLabel>Add Signers</StepLabel></Step>
          <Step><StepLabel>Send for Signing</StepLabel></Step>
        </Stepper>

        {/* File drop zone */}
        <FileDropZone
          file={file}
          onFileSelect={setFile}
          onTitleChange={setTitle}
          onError={setError}
          disabled={!canUpload}
          maxSizeMB={maxFileSizeMB}
        />

        {/* Title input */}
        {file && (
          <TextField
            fullWidth
            label="Document Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            sx={{ mt: 3 }}
            placeholder="e.g., Employment Contract - John Smith"
          />
        )}

        {/* Upload progress */}
        {uploading && <UploadProgress progress={progress} />}

        {/* Upload button */}
        {file && !uploading && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => handleUpload(file, title)}
              disabled={!canUpload || !title.trim() || isFileTooLarge}
              startIcon={<SendIcon />}
            >
              Upload & Place Signature Fields
            </Button>
          </Box>
        )}

        {/* Instructions */}
        <Box sx={{ mt: 4, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>What happens next?</Typography>
          <Typography variant="body2" color="text.secondary">
            1. Your PDF is securely uploaded and optimised ·
            2. Place signature fields on the PDF ·
            3. Add signers (email addresses) ·
            4. They receive a secure link to sign ·
            5. You get notified when signed ·
            6. Download the legally signed document
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}
