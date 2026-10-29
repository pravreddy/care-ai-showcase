/**
 * FileUploadArea — Professional drag-and-drop upload zone.
 * Shows file type icons, prominent CTA, drag highlight.
 */
import React, { useRef, useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import LockIcon from '@mui/icons-material/Lock';

// Inline SVG file type icons (PDF/DOC/XLS/JPG) — no external dep needed
const FileIcon = ({ ext, color }) => (
  <Box sx={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', mx: 0.5 }}>
    <svg width="36" height="44" viewBox="0 0 36 44" fill="none">
      <rect x="1" y="1" width="34" height="42" rx="3" fill="white" stroke={color} strokeWidth="1.5"/>
      <path d="M22 1v10h10" stroke={color} strokeWidth="1.5" fill="none"/>
      <path d="M22 1l10 10" stroke={color} strokeWidth="1.5" fill="none"/>
      <rect x="0" y="26" width="36" height="14" rx="2" fill={color}/>
      <text x="18" y="37" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold" fontFamily="Arial">{ext}</text>
    </svg>
  </Box>
);

export default function FileUploadArea({ onFileSelect }) {
  const fileInputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFileSelect(file);
  };

  return (
    <Box
      onClick={() => fileInputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      data-testid="upload-area"
      sx={{
        border: dragging ? '2.5px solid #1976d2' : '2.5px dashed #bdbdbd',
        borderRadius: 3,
        bgcolor: dragging ? '#e3f2fd' : '#fafafa',
        p: { xs: 5, md: 8 },
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': { borderColor: '#1976d2', bgcolor: '#f0f7ff' },
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf,.pdf,.doc,.docx,image/jpeg,image/png"
        hidden
        onChange={handleChange}
        data-testid="file-input"
      />

      {/* Supported file type icons */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <FileIcon ext="PDF" color="#e53935" />
        <FileIcon ext="DOC" color="#1565c0" />
        <FileIcon ext="JPG" color="#f57c00" />
        <FileIcon ext="PNG" color="#7b1fa2" />
      </Box>

      <Typography variant="h5" fontWeight={700} color="text.primary" gutterBottom>
        Drop your file or{' '}
        <Box component="span" sx={{ color: 'primary.main', textDecoration: 'underline' }}>
          choose file
        </Box>
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
        PDF, DOC, DOCX, JPG, PNG · up to 20 MB
      </Typography>
      <Typography variant="caption" color="text.disabled" sx={{ mb: 4, display: 'block' }}>
        Word and image files are converted to PDF automatically
      </Typography>

      <Button
        variant="contained"
        size="large"
        sx={{
          textTransform: 'none',
          fontWeight: 700,
          px: 6,
          py: 1.5,
          fontSize: '1rem',
          borderRadius: 2,
          boxShadow: 2,
        }}
        onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
      >
        Choose PDF File
      </Button>

      <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
        <LockIcon sx={{ fontSize: 14, color: 'text.disabled' }} />
        <Typography variant="caption" color="text.disabled">
          100% private — your file never leaves your browser
        </Typography>
      </Box>
    </Box>
  );
}
