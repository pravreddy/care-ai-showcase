import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, IconButton } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';
import SendIcon from '@mui/icons-material/Send';
import EditIcon from '@mui/icons-material/Edit';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import BookmarkAddIcon from '@mui/icons-material/BookmarkAdd';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import { documentService, templateService } from '../../services/api';
import BulkSendDialog from './BulkSendDialog';

/**
 * Top action bar for the document detail page.
 * Renders Download, Audit Trail, Remind All, Place Fields, Send buttons
 * based on document status.
 */
export default function DocumentActions({ document, onError, onAction }) {
  const navigate = useNavigate();
  const id = document.id;
  const [bulkSendOpen, setBulkSendOpen] = useState(false);

  const handleDownload = async () => {
    try {
      await documentService.download(id, document.title);
    } catch (err) {
      onError('Failed to download document.');
    }
  };

  const handleDownloadAuditCertificate = async () => {
    try {
      await documentService.downloadAuditCertificate(id, document.title);
    } catch (err) {
      onError('Failed to download audit certificate.');
    }
  };

  const handleSaveAsTemplate = async () => {
    const name = prompt('Template name:', document.title);
    if (!name) return;
    try {
      await templateService.saveFromDocument({
        name,
        document_id: id,
        category: 'OTHER',
      });
      alert('Template saved! You can find it in your template library.');
    } catch (err) {
      onError('Failed to save template.');
    }
  };

  const handleSendReminders = async () => {
    try {
      const result = await documentService.sendReminder(id);
      alert(result.message || 'Reminders sent!');
      if (onAction) onAction();
    } catch (err) {
      onError('Failed to send reminders.');
    }
  };

  return (
    <AppBar position="static" color="inherit" elevation={1}>
      <Toolbar>
        <IconButton edge="start" onClick={() => navigate('/documents')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>Document Details</Typography>

        <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleDownload} sx={{ mr: 1 }}>
          Download
        </Button>

        {document.status !== 'DRAFT' && (
          <Button variant="outlined" color="secondary" startIcon={<VerifiedUserIcon />}
            onClick={handleDownloadAuditCertificate} sx={{ mr: 1 }}>
            Audit Trail
          </Button>
        )}

        {document.status === 'PENDING' && (
          <Button variant="outlined" color="warning" startIcon={<NotificationsActiveIcon />}
            onClick={handleSendReminders} sx={{ mr: 1 }}>
            Remind All
          </Button>
        )}

        {document.status === 'DRAFT' && (
          <>
            <Button variant="outlined" startIcon={<BookmarkAddIcon />}
              onClick={handleSaveAsTemplate} sx={{ mr: 1 }}>
              Save as Template
            </Button>
            <Button variant="outlined" startIcon={<EditIcon />}
              onClick={() => navigate(`/documents/${id}/prepare`)} sx={{ mr: 1 }}>
              Place Fields
            </Button>
            <Button variant="outlined" color="info" startIcon={<GroupAddIcon />}
              onClick={() => setBulkSendOpen(true)} sx={{ mr: 1 }}>
              Bulk Send
            </Button>
            <Button variant="contained" startIcon={<SendIcon />}
              onClick={() => navigate(`/documents/${id}/send`)}>
              Send for Signing
            </Button>
          </>
        )}

        <BulkSendDialog
          open={bulkSendOpen}
          onClose={() => { setBulkSendOpen(false); if (onAction) onAction(); }}
          documentId={id}
          documentTitle={document.title}
        />
      </Toolbar>
    </AppBar>
  );
}
