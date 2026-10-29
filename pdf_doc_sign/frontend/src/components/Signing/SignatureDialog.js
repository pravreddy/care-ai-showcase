/**
 * SignatureDialog.js — Professional modal for creating a signature.
 * Opens when signer clicks a field or sidebar tool.
 *
 * Props:
 *   open       — boolean
 *   onClose    — close handler
 *   onSave     — (blob) => void
 *   signerName — pre-fills typed tab
 *   fieldType  — 'SIGNATURE' | 'INITIALS'
 */
import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Tabs, Tab, Box, Typography, Divider,
} from '@mui/material';
import DrawIcon from '@mui/icons-material/Draw';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SIGNATURE_TABS from '../../utils/signatureTabs';

const TAB_ICONS = [<DrawIcon />, <TextFieldsIcon />, <UploadFileIcon />];

export default function SignatureDialog({ open, onClose, onSave, signerName, fieldType }) {
  const [tab, setTab] = useState(0);

  const handleSave = (blob) => {
    onSave(blob);
    onClose();
  };

  const title = fieldType === 'INITIALS' ? 'Add Your Initials' : 'Add Your Signature';
  const ActiveComponent = SIGNATURE_TABS[tab]?.component;
  const activeTab = SIGNATURE_TABS[tab];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { borderRadius: 3 } }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6" fontWeight={700}>{title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          Draw, type, or upload your signature below
        </Typography>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ pt: 2 }}>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          sx={{
            mb: 3,
            '& .MuiTab-root': { textTransform: 'none', fontWeight: 600, minHeight: 44 },
            '& .MuiTabs-indicator': { height: 3, borderRadius: 1.5 },
          }}
        >
          {SIGNATURE_TABS.map((t, i) => (
            <Tab key={i} icon={TAB_ICONS[i]} iconPosition="start" label={t.label} />
          ))}
        </Tabs>

        <Box sx={{ minHeight: 200 }}>
          {ActiveComponent && (
            <ActiveComponent
              onSave={handleSave}
              {...(activeTab.needsName ? { signerName } : {})}
            />
          )}
        </Box>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit" sx={{ textTransform: 'none' }}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}
