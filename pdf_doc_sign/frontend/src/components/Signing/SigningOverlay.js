/**
 * SigningOverlay.js — Renders clickable field indicators on a single PDF page.
 *
 * Props:
 *   pageNum           - current page number
 *   pageWidth         - rendered page width in pixels
 *   pageHeight        - rendered page height in pixels
 *   fields            - all fields for this document
 *   filledFields      - { fieldId: value } map of filled fields
 *   signaturePreviewUrl - URL for signature image preview
 *   onFieldClick      - (field) => void — called when an unfilled field is clicked
 */
import React from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';

const TYPE_LABELS = {
  SIGNATURE: 'Sign here',
  DATE: 'Date',
  NAME: 'Name',
  TEXT: 'Text',
  INITIALS: 'Initials',
  CHECKBOX: 'Tick',
};

export default function SigningOverlay({
  pageNum, pageWidth, pageHeight,
  fields, filledFields, signaturePreviewUrl,
  onFieldClick, onFieldClear,
}) {
  const pageFields = fields.filter(f => f.page === pageNum);
  if (!pageFields.length) return null;

  return pageFields.map((field, i) => {
    const filledValue = filledFields[field.id];
    const isFilled = filledValue !== undefined && filledValue !== null && filledValue !== '';
    const isSignatureType = field.field_type === 'SIGNATURE' || field.field_type === 'INITIALS';
    const isCheckbox = field.field_type === 'CHECKBOX';
    const isChecked = isCheckbox && String(filledValue).toLowerCase() === 'true';
    // When a signature image is placed we want the PDF behind it (table
    // borders, underlines, etc.) to stay visible — so we use a transparent
    // outline (which does not add to the box dimensions) instead of a
    // solid border + bgcolor. Matches the free-sign-tool behaviour which
    // in turn matches DigiSigner.
    const isSignatureFilled = isFilled && isSignatureType;

    return (
      <Box
        key={field.id || i}
        onClick={(e) => {
          e.stopPropagation();
          // Signatures can always be re-opened (to replace/change).
          // Text/name/date fields are always clickable — empty so the signer
          // can fill them, filled so they can correct a typo.
          onFieldClick(field);
        }}
        sx={{
          position: 'absolute',
          left: (field.x_percent / 100) * pageWidth,
          top: (field.y_percent / 100) * pageHeight,
          width: (field.width_percent / 100) * pageWidth,
          height: (field.height_percent / 100) * pageHeight,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'auto',
          cursor: 'pointer',
          overflow: 'hidden',
          transition: 'all 0.2s',
          '&:hover .field-clear': { opacity: 1 },
          // Empty field — prominent pulsing green "sign here" frame.
          // Checkbox fields get their own styling below (no pulse, tighter border).
          ...(!isFilled && !isCheckbox && {
            border: '2px solid #4caf50',
            bgcolor: 'rgba(76, 175, 80, 0.12)',
            borderRadius: '4px',
            '&:hover': {
              bgcolor: 'rgba(76, 175, 80, 0.2)',
              boxShadow: '0 0 8px rgba(0,0,0,0.15)',
            },
            animation: 'fieldPulse 2s infinite',
            '@keyframes fieldPulse': {
              '0%, 100%': { borderColor: '#4caf50' },
              '50%': { borderColor: '#81c784' },
            },
          }),
          // Checkbox — subtle container; the real visual is the nested
          // square rendered below. No pulsing (would be noisy for tiny fields).
          ...(isCheckbox && {
            bgcolor: 'transparent',
            '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' },
          }),
          // Filled with plain text (name / date / text) — subtle blue tint
          ...(isFilled && !isSignatureType && !isCheckbox && {
            border: '1px dashed rgba(21, 101, 192, 0.5)',
            bgcolor: 'rgba(21, 101, 192, 0.06)',
            borderRadius: '4px',
            '&:hover': { bgcolor: 'rgba(21, 101, 192, 0.12)' },
          }),
          // Filled with a signature image — NO opaque frame.
          // Outline (not border) reveals on hover so the field is still
          // discoverable, but doesn't add any dimension to the box and
          // doesn't paint over the PDF content behind it.
          ...(isSignatureFilled && {
            outline: '1px dashed transparent',
            '&:hover': { outline: '1px dashed rgba(21, 101, 192, 0.6)' },
          }),
        }}
      >
        {isCheckbox ? (
          // Checkbox is always rendered the same way regardless of filled
          // state: a neutral box with or without a tick. Clicking toggles.
          <Box sx={{
            width: '70%', height: '70%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: `2px solid ${isChecked ? '#1565c0' : '#4caf50'}`,
            borderRadius: '3px',
            bgcolor: isChecked ? 'rgba(21, 101, 192, 0.08)' : 'white',
          }}>
            {isChecked && <CheckIcon sx={{ fontSize: 18, color: '#1565c0' }} />}
          </Box>
        ) : isFilled ? (
          isSignatureType && signaturePreviewUrl ? (
            <img
              src={signaturePreviewUrl}
              alt="Signature"
              style={{ width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }}
            />
          ) : (
            <Typography variant="caption" sx={{ color: '#1565c0', fontWeight: 600, fontSize: '0.6rem', userSelect: 'none', px: 0.5 }}>
              {filledFields[field.id] === 'signed' ? '✓ Signed' : filledFields[field.id]}
            </Typography>
          )
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
            <TouchAppIcon sx={{ fontSize: 12, color: '#2e7d32' }} />
            <Typography variant="caption" sx={{ color: '#2e7d32', fontWeight: 600, fontSize: '0.6rem', userSelect: 'none' }}>
              {field.label || TYPE_LABELS[field.field_type] || field.field_type}
            </Typography>
          </Box>
        )}

        {isFilled && !isCheckbox && onFieldClear && (
          <IconButton
            className="field-clear"
            size="small"
            title="Clear"
            onClick={(e) => { e.stopPropagation(); onFieldClear(field); }}
            sx={{
              position: 'absolute', top: 0, right: 0,
              width: 16, height: 16, p: 0,
              bgcolor: 'rgba(211,47,47,0.92)', color: 'white',
              borderRadius: '0 0 0 4px',
              opacity: 0.85, transition: 'opacity 0.15s', zIndex: 5,
              '&:hover': { bgcolor: '#b71c1c' },
            }}
          >
            <CloseIcon sx={{ fontSize: 11 }} />
          </IconButton>
        )}
      </Box>
    );
  });
}
