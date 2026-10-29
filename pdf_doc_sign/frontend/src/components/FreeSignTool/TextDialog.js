/**
 * TextDialog — Modal for entering free text to place on the PDF.
 * Props: open, onClose, onConfirm(text, fontSize, color), mode ('text'|'date')
 * All state owned here (simple enough — no need to hoist).
 */
import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Stack, Typography, ToggleButton,
  ToggleButtonGroup, Slider, Box,
} from '@mui/material';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';

const FONT_SIZES = [10, 12, 14, 16, 18, 20, 24, 28, 32];
const COLORS = ['#000000', '#1565c0', '#c62828', '#2e7d32', '#6a1b9a'];

const todayFormatted = () => {
  const d = new Date();
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
};

export default function TextDialog({ open, onClose, onConfirm, mode }) {
  const [text, setText] = useState('');
  const [fontSize, setFontSize] = useState(16);
  const [color, setColor] = useState('#000000');

  // When dialog opens: pre-fill date if mode is 'date'
  useEffect(() => {
    if (open) {
      setText(mode === 'date' ? todayFormatted() : '');
      setFontSize(mode === 'date' ? 14 : 16);
      setColor('#000000');
    }
  }, [open, mode]);

  const handleConfirm = () => {
    if (!text.trim()) return;
    onConfirm(text.trim(), fontSize, color);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {mode === 'date' ? (
          <><CalendarTodayIcon color="primary" /> Add Date</>
        ) : (
          <><TextFieldsIcon color="primary" /> Add Text</>
        )}
      </DialogTitle>

      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label={mode === 'date' ? 'Date text' : 'Enter text'}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleConfirm()}
          placeholder={mode === 'date' ? todayFormatted() : 'e.g. Approved, Initials, Name...'}
          sx={{ mt: 1 }}
          inputProps={{ 'data-testid': 'text-input' }}
        />

        {/* Font size */}
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ minWidth: 70 }}>Font size:</Typography>
          <ToggleButtonGroup
            value={fontSize}
            exclusive
            onChange={(_, v) => v && setFontSize(v)}
            size="small"
            data-testid="font-size-group"
          >
            {FONT_SIZES.map((s) => (
              <ToggleButton key={s} value={s} sx={{ px: 1.5, minWidth: 40 }}>
                {s}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Stack>

        {/* Colour */}
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ minWidth: 70 }}>Colour:</Typography>
          <Stack direction="row" spacing={1}>
            {COLORS.map((c) => (
              <Box
                key={c}
                onClick={() => setColor(c)}
                data-testid={`color-${c}`}
                sx={{
                  width: 28, height: 28, borderRadius: '50%',
                  bgcolor: c, cursor: 'pointer',
                  border: color === c ? '3px solid #1976d2' : '2px solid #ccc',
                }}
              />
            ))}
          </Stack>
        </Stack>

        {/* Live preview */}
        {text.trim() && (
          <Box
            sx={{
              mt: 3, p: 2,
              border: '1px dashed #ccc', borderRadius: 1,
              minHeight: 48, display: 'flex', alignItems: 'center',
            }}
            data-testid="text-preview"
          >
            <Typography
              sx={{
                fontSize: `${fontSize}px`,
                color,
                fontFamily: mode === 'date'
                  ? '"Courier New", monospace'
                  : '"Helvetica Neue", Arial, sans-serif',
                fontWeight: mode === 'date' ? 400 : 400,
              }}
            >
              {text}
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} color="inherit">Cancel</Button>
        <Button
          variant="contained"
          onClick={handleConfirm}
          disabled={!text.trim()}
          data-testid="text-confirm-btn"
        >
          Place on PDF
        </Button>
      </DialogActions>
    </Dialog>
  );
}
