/**
 * freeSignConfig.js — Single source of truth for FreeSignTool configuration.
 * Add fonts, colours, or tool definitions here — nothing else needs changing.
 */

export const SIG_FONTS = [
  { label: 'Brush Script', css: '"Brush Script MT", cursive' },
  { label: 'Dancing',      css: '"Dancing Script", cursive' },
  { label: 'Pinyon',       css: '"Pinyon Script", cursive' },
  { label: 'Great Vibes',  css: '"Great Vibes", cursive' },
  { label: 'Sacramento',   css: '"Sacramento", cursive' },
  { label: 'Courier',      css: '"Courier New", monospace' },
];

export const SIG_COLORS = [
  { label: 'Black', value: '#1a1a1a' },
  { label: 'Blue',  value: '#1565c0' },
  { label: 'Green', value: '#2e7d32' },
];

// Default values
export const DEFAULT_FONT  = SIG_FONTS[0].css;
export const DEFAULT_COLOR = SIG_COLORS[0].value;
export const DEFAULT_SIG_SIZE = 150;

// Tool types — used for placing mode
export const TOOL_TYPES = {
  SIGNATURE:  'signature',
  INITIALS:   'initials',
  TEXT:       'text',
  DATE:       'date',
  CHECKMARK:  'checkmark',
};
