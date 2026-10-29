import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Paper, Typography, Button, Alert, CircularProgress, Container } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import { documentService } from '../../services/api';
import PdfViewer from '../Pdf/PdfViewer';

import { useDocumentData } from './useDocumentData';
import DocumentActions from './DocumentActions';
import DocumentInfoCard from './DocumentInfoCard';
import SignersList from './SignersList';
import ActivityLogTable from './ActivityLogTable';

export default function DocumentView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { document, auditLog, loading, error, setError, reload } = useDocumentData(id);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!document) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error || 'Document not found'}</Alert>
        <Button sx={{ mt: 2 }} onClick={() => navigate('/documents')}>Back to Documents</Button>
      </Container>
    );
  }

  const pdfUrl = documentService.getPdfUrl(id);
  const authToken = localStorage.getItem('accessToken');

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      <DocumentActions document={document} onError={setError} onAction={reload} />

      <Container maxWidth="md" sx={{ py: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>{error}</Alert>
        )}

        <DocumentInfoCard document={document} />

        <SignersList documentId={id} signers={document.signers} onError={setError} />

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            <DescriptionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />PDF Preview
          </Typography>
          <PdfViewer pdfUrl={pdfUrl} authToken={authToken} />
        </Paper>

        <ActivityLogTable logs={auditLog} />
      </Container>
    </Box>
  );
}
