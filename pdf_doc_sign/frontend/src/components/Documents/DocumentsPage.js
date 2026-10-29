import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Button, Alert, CircularProgress, Chip,
  IconButton, Tooltip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import FolderIcon from '@mui/icons-material/Folder';
import SendIcon from '@mui/icons-material/Send';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import { documentService } from '../../services/api';
import { getDocumentErrorMessage } from '../../utils/errorHandling';
import AdBanner from '../Common/AdBanner';

export default function DocumentsPage({ user }) {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { loadDocuments(); }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await documentService.list();
      setDocuments(data.results || data || []);
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'load'));
    } finally { setLoading(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document?')) return;
    try {
      await documentService.delete(id);
      setDocuments(documents.filter(d => d.id !== id));
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'delete'));
    }
  };

  const handleDownload = async (doc) => {
    try {
      await documentService.download(doc.id, doc.title);
    } catch (err) {
      setError(getDocumentErrorMessage(err, 'download'));
    }
  };

  const getStatusColor = (status) => {
    const m = { SIGNED: 'success', PENDING: 'warning', DRAFT: 'default', EXPIRED: 'error' };
    return m[status] || 'default';
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;

  return (
    <Box>
      <AdBanner user={user} />
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5"><DescriptionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />My Documents</Typography>
          <Button variant="contained" startIcon={<CloudUploadIcon />} onClick={() => navigate('/documents/upload')}>Upload New</Button>
        </Box>

        {documents.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 6 }}>
            <FolderIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>No documents yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Upload a PDF to get started with e-signatures</Typography>
            <Button variant="contained" startIcon={<CloudUploadIcon />} onClick={() => navigate('/documents/upload')}>Upload Your First Document</Button>
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Pages</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DescriptionIcon sx={{ mr: 1, color: 'primary.main' }} />
                        {doc.title}
                      </Box>
                    </TableCell>
                    <TableCell><Chip label={doc.status} size="small" color={getStatusColor(doc.status)} /></TableCell>
                    <TableCell>{doc.page_count || '—'}</TableCell>
                    <TableCell>{doc.file_size_mb} MB</TableCell>
                    <TableCell>{new Date(doc.created_at).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="View"><IconButton size="small" onClick={() => navigate(`/documents/${doc.id}`)}><VisibilityIcon /></IconButton></Tooltip>
                      {doc.status === 'DRAFT' && (
                        <>
                          <Tooltip title="Place Fields"><IconButton size="small" color="secondary" onClick={() => navigate(`/documents/${doc.id}/prepare`)}><EditIcon /></IconButton></Tooltip>
                          <Tooltip title="Send for Signing"><IconButton size="small" color="primary" onClick={() => navigate(`/documents/${doc.id}/send`)}><SendIcon /></IconButton></Tooltip>
                        </>
                      )}
                      <Tooltip title="Download"><IconButton size="small" onClick={() => handleDownload(doc)}><DownloadIcon /></IconButton></Tooltip>
                      <Tooltip title="Delete"><IconButton size="small" color="error" onClick={() => handleDelete(doc.id)}><DeleteIcon /></IconButton></Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
}
