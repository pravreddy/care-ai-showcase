import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, TextField, Button, Alert, DialogActions } from '@mui/material';
import api from '../../services/api';

export default function ForceChangePassword({ open, onComplete }) {
    const [passwords, setPasswords] = useState({ new: '', confirm: '' });
    const [error, setError] = useState('');

    const handleUpdate = async () => {
        if (passwords.new !== passwords.confirm) return setError("Passwords don't match");
        try {
            await api.post('/auth/force-change-password/', { [cite: 188]
            new_password: passwords.new,
                confirm_password: passwords.confirm
        });
            onComplete();
        } catch (err) { setError(err.response?.data?.error || 'Update failed'); }
    };

    return (
        <Dialog open={open} disableEscapeKeyDown>
            <DialogTitle>Update Your Password</DialogTitle>
            <DialogContent>
                <Alert severity="info" sx={{ mb: 2 }}>For security, please change your temporary password.</Alert>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <TextField fullWidth label="New Password" type="password" margin="dense"
                           onChange={e => setPasswords({...passwords, new: e.target.value})} />
                <TextField fullWidth label="Confirm New Password" type="password" margin="dense"
                           onChange={e => setPasswords({...passwords, confirm: e.target.value})} />
            </DialogContent>
            <DialogActions>
                <Button onClick={handleUpdate} variant="contained" fullWidth>Update & Login</Button>
            </DialogActions>
        </Dialog>
    );
}