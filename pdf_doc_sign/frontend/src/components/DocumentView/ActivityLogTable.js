import React from 'react';
import {
  Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';

/**
 * Activity log table showing the document's audit trail.
 */
export default function ActivityLogTable({ logs }) {
  if (!logs || logs.length === 0) return null;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />Activity Log
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Action</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell>
                  <Chip label={log.action} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{log.description}</TableCell>
                <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
