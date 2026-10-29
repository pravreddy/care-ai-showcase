/**
 * FileDropZone.js — Drag-and-drop file selector with validation feedback.
 */
import React, { useState, useCallback } from 'react';
import { Box, Typography, Button } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { validateUploadFile } from '../../../utils/errorHandling';

export default function FileDropZone({ file, onFileSelect, onTitleChange, onError, disabled, maxSizeMB = 10 }) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const processFile = useCallback((f) => {
    const err = validateUploadFile(f, { maxSizeMB });
    if (err) {
      onError(err);
      return;
    }
    onFileSelect(f);
    // Strip extension for default title
    const nameWithoutExt = f.name.replace(/\.[^.]+$/, '');
    if (onTitleChange) onTitleChange(nameWithoutExt);
    onError('');
  }, [maxSizeMB, onFileSelect, onTitleChange, onError]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
  }, [processFile]);

  const handleFileInput = (e) => {
    if (e.target.files?.[0]) processFile(e.target.files[0]);
  };

  const isFileTooLarge = file && file.size > maxSizeMB * 1024 * 1024;
  const fileSizeMB = file ? (file.size / 1024 / 1024).toFixed(2) : null;

  const borderColor = dragActive ? '#1976d2' : isFileTooLarge ? '#d32f2f' : file ? '#4caf50' : '#ccc';
  const bgColor = dragActive ? 'rgba(25,118,210,0.04)' : isFileTooLarge ? 'rgba(211,47,47,0.04)' : file ? 'rgba(76,175,80,0.04)' : 'transparent';

  return (
    <Box
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !disabled && window.document.getElementById('file-input').click()}
      sx={{
        border: `2px dashed ${borderColor}`,
        borderRadius: 2,
        p: 6,
        textAlign: 'center',
        bgcolor: bgColor,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s',
      }}
    >
      <input
        id="file-input"
        type="file"
        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
        style={{ display: 'none' }}
        onChange={handleFileInput}
        disabled={disabled}
      />

      {file ? (
        <Box>
          {isFileTooLarge ? (
            <ErrorOutlineIcon sx={{ fontSize: 60, color: 'error.main', mb: 2 }} />
          ) : (
            <CheckCircleIcon sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          )}
          <Typography variant="h6">{file.name}</Typography>
          <Typography variant="body2" color={isFileTooLarge ? 'error' : 'text.secondary'}>
            {fileSizeMB} MB
            {isFileTooLarge && ` — Too large! Maximum is ${maxSizeMB} MB`}
          </Typography>
          <Button
            size="small"
            sx={{ mt: 1 }}
            onClick={(e) => {
              e.stopPropagation();
              onFileSelect(null);
              if (onTitleChange) onTitleChange('');
              onError('');
            }}
          >
            Change File
          </Button>
        </Box>
      ) : (
        <Box>
          <CloudUploadIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">Drag & drop your file here</Typography>
          <Typography variant="body2" color="text.secondary">PDF, DOC, DOCX, JPG, PNG · max {maxSizeMB} MB · non-PDF files converted automatically</Typography>
        </Box>
      )}
    </Box>
  );
}
