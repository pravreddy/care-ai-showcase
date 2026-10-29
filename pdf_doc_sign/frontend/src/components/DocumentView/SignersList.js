import React from 'react';
import {
  Paper, Typography, List, ListItem, ListItemIcon, ListItemText,
  Box, Chip, IconButton, LinearProgress,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PendingIcon from '@mui/icons-material/Pending';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import { documentService } from '../../services/api';

function getSignerStatusIcon(status) {
  switch (status) {
    case 'SIGNED': return <CheckCircleIcon color="success" />;
    case 'PENDING': return <PendingIcon color="warning" />;
    case 'DECLINED': return <PendingIcon color="error" />;
    default: return <PendingIcon />;
  }
}

function getSignerChipColor(status) {
  if (status === 'SIGNED') return 'success';
  if (status === 'PENDING') return 'warning';
  return 'default';
}

/**
 * List of signers for a document, with status chips and per-signer reminder buttons.
 */
export default function SignersList({ documentId, signers, onError }) {
  const handleRemind = async (signerId, signerName) => {
    try {
      const result = await documentService.sendReminder(documentId, signerId);
      alert(result.message || `Reminder sent to ${signerName}`);
    } catch (err) {
      if (onError) onError('Failed to send reminder.');
    }
  };

  if (!signers || signers.length === 0) return null;

  const total = signers.length;
  const signedCount = signers.filter((s) => s.status === 'SIGNED').length;
  const pending = total - signedCount;
  const pct = total ? (signedCount / total) * 100 : 0;

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Signers
      </Typography>

      {/* Overall progress — shows how much of the document is signed */}
      <Box sx={{ mb: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">Signing progress</Typography>
          <Typography variant="body2" fontWeight={600}>
            {signedCount} of {total} signed{pending > 0 ? ` — ${pending} pending` : ''}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={pct}
          color={signedCount === total ? 'success' : 'primary'}
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>
      <List>
        {signers.map((signer, index) => (
          <ListItem key={signer.id || index} divider={index < signers.length - 1}>
            <ListItemIcon>{getSignerStatusIcon(signer.status)}</ListItemIcon>
            <ListItemText primary={signer.signer_name} secondary={signer.signer_email} />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip label={signer.status} size="small" color={getSignerChipColor(signer.status)} />
              {signer.status === 'PENDING' && (
                <IconButton size="small" color="warning" title="Send reminder"
                  onClick={() => handleRemind(signer.id, signer.signer_name)}>
                  <NotificationsActiveIcon fontSize="small" />
                </IconButton>
              )}
              {signer.signed_at && (
                <Typography variant="caption" color="text.secondary">
                  Signed: {new Date(signer.signed_at).toLocaleString()}
                </Typography>
              )}
            </Box>
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
