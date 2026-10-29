/**
 * PlagiarismPage.js
 * Full plagiarism checker for logged-in users.
 * - File upload OR paste text (tabs)
 * - Sentence-level highlighting (Copied / Similar / Original)
 * - Plagiarism % gauge
 * - Explanation panel
 * - Scan history with delete
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, LinearProgress, Alert,
  Chip, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, CircularProgress, Divider, Tooltip, Tab, Tabs,
  TextField, IconButton,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import HistoryIcon from '@mui/icons-material/History';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ArticleIcon from '@mui/icons-material/Article';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { plagiarismService } from '../../services/api';

const SUPPORTED_TYPES = ['pdf', 'docx', 'txt', 'pptx', 'xlsx'];
const ACCEPT = '.pdf,.docx,.txt,.pptx,.xlsx';
const MAX_MB = 10;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function verdictColour(verdict) {
  if (verdict === 'LIKELY_PLAGIARISED') return 'error';
  if (verdict === 'POSSIBLY_SIMILAR')  return 'warning';
  if (verdict === 'MOSTLY_ORIGINAL')   return 'success';
  return 'default';
}

function verdictLabel(verdict, plagPct) {
  if (verdict === 'LIKELY_PLAGIARISED') return `High Plagiarism · ${plagPct}%`;
  if (verdict === 'POSSIBLY_SIMILAR')   return `Some Similarities · ${plagPct}%`;
  if (verdict === 'MOSTLY_ORIGINAL')    return `Mostly Original · ${100 - plagPct}% original`;
  if (verdict === 'INSUFFICIENT_TEXT')  return 'Not enough text';
  if (verdict === 'PENDING')            return 'Processing…';
  if (verdict === 'ERROR')              return 'Check failed';
  return verdict || '—';
}

function VerdictIcon({ verdict }) {
  if (verdict === 'MOSTLY_ORIGINAL')   return <CheckCircleOutlineIcon color="success" fontSize="large" />;
  if (verdict === 'POSSIBLY_SIMILAR')  return <WarningAmberIcon color="warning" fontSize="large" />;
  if (verdict === 'LIKELY_PLAGIARISED') return <ErrorOutlineIcon color="error" fontSize="large" />;
  return <ContentCopyIcon color="action" fontSize="large" />;
}

// ─── Sentence colours ─────────────────────────────────────────────────────────
function sentenceBg(label) {
  if (label === 'Copied')   return 'rgba(211,47,47,0.13)';
  if (label === 'Original') return 'rgba(46,125,50,0.10)';
  return 'rgba(237,108,2,0.10)';
}
function sentenceBorder(label) {
  if (label === 'Copied')   return '#d32f2f';
  if (label === 'Original') return '#2e7d32';
  return '#ed6c02';
}

// ─── Gauge ────────────────────────────────────────────────────────────────────
function PlagiarismGauge({ plagPct, origPct }) {
  return (
    <Box sx={{ mt: 2.5 }}>
      <Box sx={{ height: 22, borderRadius: 11, overflow: 'hidden', display: 'flex' }}>
        <Box sx={{ width: `${origPct}%`, bgcolor: '#2e7d32', transition: 'width 0.9s ease' }} />
        <Box sx={{ width: `${plagPct}%`, bgcolor: '#d32f2f', transition: 'width 0.9s ease' }} />
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#2e7d32' }} />
          <Typography variant="caption" color="text.secondary">{origPct}% Original</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#d32f2f' }} />
          <Typography variant="caption" color="text.secondary">{plagPct}% Plagiarised</Typography>
        </Box>
      </Box>
    </Box>
  );
}

// ─── Sentence Highlighter ─────────────────────────────────────────────────────
function SentenceHighlighter({ sentences }) {
  if (!sentences?.length) return null;
  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: 'flex', gap: 1.5, mb: 1.5, flexWrap: 'wrap' }}>
        {[
          { label: 'Copied',   colour: '#d32f2f', bg: 'rgba(211,47,47,0.1)' },
          { label: 'Similar',  colour: '#ed6c02', bg: 'rgba(237,108,2,0.1)' },
          { label: 'Original', colour: '#2e7d32', bg: 'rgba(46,125,50,0.1)' },
        ].map((l) => (
          <Box key={l.label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 14, height: 14, borderRadius: 1, bgcolor: l.bg, border: `2px solid ${l.colour}` }} />
            <Typography variant="caption" color="text.secondary">{l.label}</Typography>
          </Box>
        ))}
      </Box>
      <Box sx={{ lineHeight: 2.2, fontSize: '0.88rem' }}>
        {sentences.map((s, i) => (
          <Tooltip
            key={i}
            title={
              s.possible_source
                ? `${s.label} · Possible source: ${s.possible_source}`
                : `${s.label} · ${Math.round((s.plagiarism_probability || 0) * 100)}% similarity`
            }
            placement="top"
          >
            <span
              style={{
                backgroundColor: sentenceBg(s.label),
                borderBottom: `2px solid ${sentenceBorder(s.label)}`,
                borderRadius: 3,
                padding: '1px 2px',
                marginRight: 4,
                cursor: 'default',
                display: 'inline',
              }}
            >
              {s.text}
            </span>
          </Tooltip>
        ))}
      </Box>
    </Box>
  );
}

// ─── Result Card ──────────────────────────────────────────────────────────────
function ResultCard({ result }) {
  const plagPct  = result.plagiarism_percentage ?? 0;
  const origPct  = result.original_percentage  ?? (100 - plagPct);
  const colour   = verdictColour(result.verdict);
  const [tab, setTab] = useState(0);

  const hasSentences  = result.sentence_matches?.length > 0;
  const hasExplanation = !!result.explanation;

  const tabs = [];
  if (hasSentences)    tabs.push({ label: 'Sentence Analysis', icon: <ContentCopyIcon fontSize="small" /> });
  if (result.extracted_text) tabs.push({ label: 'Full Text',   icon: <ArticleIcon fontSize="small" /> });
  if (hasExplanation)  tabs.push({ label: 'Analysis Notes',    icon: <LightbulbIcon fontSize="small" /> });

  return (
    <Paper elevation={2} sx={{ mt: 3, borderLeft: 5, borderColor: `${colour}.main`, overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ p: 2.5, pb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, flexWrap: 'wrap' }}>
          <VerdictIcon verdict={result.verdict} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={700} noWrap sx={{ maxWidth: 500 }}>
              {result.original_filename}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
              <Chip label={verdictLabel(result.verdict, plagPct)} color={colour} size="small" sx={{ fontWeight: 700 }} />
              <Chip label={result.provider === 'groq' ? 'Groq Pattern Analysis' : result.provider} size="small" variant="outlined" />
              <Chip label={result.file_type?.toUpperCase()} size="small" variant="outlined" />
            </Box>
          </Box>
        </Box>

        {result.plagiarism_percentage !== null && (
          <PlagiarismGauge plagPct={plagPct} origPct={origPct} />
        )}

        {result.error_message && (
          <Alert severity="warning" sx={{ mt: 2 }}>{result.error_message}</Alert>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'block' }}>
          {result.text_length?.toLocaleString()} characters checked
        </Typography>
      </Box>

      {/* Tabs */}
      {tabs.length > 0 && (
        <>
          <Divider />
          <Box sx={{ px: 1 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ minHeight: 42 }}>
              {tabs.map((t, i) => (
                <Tab key={i} label={t.label} icon={t.icon} iconPosition="start"
                  sx={{ fontSize: '0.8rem', minHeight: 42 }} />
              ))}
            </Tabs>
          </Box>
          <Box sx={{ px: 2.5, pb: 2.5, pt: 1 }}>
            {tabs[tab]?.label === 'Sentence Analysis' && (
              <SentenceHighlighter sentences={result.sentence_matches} />
            )}
            {tabs[tab]?.label === 'Full Text' && result.extracted_text && (
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                <Typography variant="body2" component="pre"
                  sx={{ fontFamily: 'monospace', fontSize: '0.78rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.7 }}>
                  {result.extracted_text}
                </Typography>
              </Paper>
            )}
            {tabs[tab]?.label === 'Analysis Notes' && result.explanation && (
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <LightbulbIcon color="warning" fontSize="small" />
                  <Typography variant="subtitle2" fontWeight={600}>Analysis summary</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                  {result.explanation}
                </Typography>
                <Alert severity="info" sx={{ mt: 2 }} icon={false}>
                  <Typography variant="caption">
                    This is <strong>pattern-based analysis</strong> — not a live web search.
                    Sentences flagged as "Copied" match known textbook/encyclopaedic writing patterns.
                    For real source matching with URLs, upgrade to Pro.
                  </Typography>
                </Alert>
              </Paper>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
}

// ─── Drop Zone ────────────────────────────────────────────────────────────────
function DropZone({ onFile, loading }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  }, [onFile]);

  return (
    <Box
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !loading && inputRef.current.click()}
      sx={{
        border: '2px dashed',
        borderColor: dragging ? 'primary.main' : 'grey.400',
        borderRadius: 3, p: 5, textAlign: 'center',
        cursor: loading ? 'not-allowed' : 'pointer',
        bgcolor: dragging ? 'primary.50' : 'grey.50',
        transition: 'all 0.2s',
        '&:hover': { borderColor: 'primary.main', bgcolor: 'primary.50' },
      }}
    >
      <input ref={inputRef} type="file" accept={ACCEPT} style={{ display: 'none' }}
        onChange={(e) => { if (e.target.files[0]) onFile(e.target.files[0]); }} />
      {loading ? (
        <Box><CircularProgress size={40} />
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1.5 }}>Checking for plagiarism…</Typography>
        </Box>
      ) : (
        <Box>
          <UploadFileIcon sx={{ fontSize: 52, color: 'primary.main', mb: 1 }} />
          <Typography variant="h6" fontWeight={600}>Drop your file here</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>or click to browse</Typography>
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
            {SUPPORTED_TYPES.map((t) => <Chip key={t} label={`.${t}`} size="small" variant="outlined" />)}
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>Max {MAX_MB}MB</Typography>
        </Box>
      )}
    </Box>
  );
}

// ─── Text Paste Zone ─────────────────────────────────────────────────────────
function TextPasteZone({ onText, loading }) {
  const [text, setText] = useState('');
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;

  return (
    <Box>
      <TextField
        multiline rows={8} fullWidth
        placeholder="Paste your essay, article, or assignment here to check for plagiarism…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
        sx={{ '& .MuiOutlinedInput-root': { fontFamily: 'inherit', fontSize: '0.9rem', lineHeight: 1.7 } }}
      />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {text.length.toLocaleString()} characters · {wordCount} words
          {text.length < 100 && text.length > 0 && (
            <span style={{ color: '#d32f2f' }}> · minimum 100 characters</span>
          )}
        </Typography>
        <Button
          variant="contained" size="medium"
          disabled={loading || text.trim().length < 100}
          onClick={() => onText(text.trim())}
          startIcon={loading ? <CircularProgress size={16} /> : <ContentCopyIcon />}
        >
          {loading ? 'Checking…' : 'Check Plagiarism'}
        </Button>
      </Box>
    </Box>
  );
}

// ─── History Table ────────────────────────────────────────────────────────────
function HistoryTable({ history, onDelete, onClearAll }) {
  if (!history.length) return null;
  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon fontSize="small" color="action" />
          <Typography variant="subtitle1" fontWeight={600}>Recent Checks</Typography>
          <Chip label={history.length} size="small" />
        </Box>
        <Button size="small" startIcon={<DeleteOutlineIcon />} onClick={onClearAll} color="inherit">
          Clear All
        </Button>
      </Box>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.50' }}>
              <TableCell sx={{ fontWeight: 600 }}>File / Text</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Verdict</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Plagiarism %</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Checked</TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">Delete</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>{row.original_filename}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={verdictLabel(row.verdict, row.plagiarism_percentage)}
                    color={verdictColour(row.verdict)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {row.plagiarism_percentage !== null ? `${row.plagiarism_percentage}%` : '—'}
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(row.created_at).toLocaleDateString('en-GB', {
                      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
                    })}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Delete this check">
                    <IconButton size="small" color="error" onClick={() => onDelete(row.id)}>
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function PlagiarismPage() {
  const [inputTab, setInputTab] = useState(0);
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState('');
  const [history, setHistory]   = useState([]);

  useEffect(() => {
    plagiarismService.getHistory()
      .then((data) => setHistory(data.results || []))
      .catch(() => {});
  }, []);

  const handleResult = (data) => {
    setResult(data);
    setHistory((prev) => [data, ...prev.filter((h) => h.id !== data.id).slice(0, 49)]);
  };

  const handleFile = async (file) => {
    setError(''); setResult(null);
    const ext = file.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_TYPES.includes(ext)) { setError(`Unsupported: .${ext}`); return; }
    if (file.size > MAX_MB * 1024 * 1024) { setError(`Max ${MAX_MB}MB.`); return; }
    setLoading(true);
    try {
      handleResult(await plagiarismService.scan(file));
    } catch (err) {
      setError(err.response?.data?.error || 'Check failed. Please try again.');
    } finally { setLoading(false); }
  };

  const handleText = async (text) => {
    setError(''); setResult(null);
    setLoading(true);
    try {
      handleResult(await plagiarismService.scanText(text));
    } catch (err) {
      setError(err.response?.data?.error || 'Check failed. Please try again.');
    } finally { setLoading(false); }
  };

  const handleDelete = async (id) => {
    try {
      await plagiarismService.deleteScan(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
      if (result?.id === id) setResult(null);
    } catch {}
  };

  const handleClearAll = async () => {
    await Promise.allSettled(history.map((h) => plagiarismService.deleteScan(h.id)));
    setHistory([]); setResult(null);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
          <ContentCopyIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h5" fontWeight={700}>Plagiarism Checker</Typography>
          <Tooltip title="Upload a file or paste text to check for copied or similar content. Sentences are colour-coded: red = likely copied, orange = similar, green = original.">
            <HelpOutlineIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
          </Tooltip>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Detect copied content with sentence-level highlighting. Powered by Groq pattern analysis.
        </Typography>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Input tabs */}
      <Paper variant="outlined" sx={{ borderRadius: 3, overflow: 'hidden', mb: 2 }}>
        <Tabs
          value={inputTab}
          onChange={(_, v) => { setInputTab(v); setError(''); setResult(null); }}
          sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50', minHeight: 44 }}
        >
          <Tab icon={<UploadFileIcon fontSize="small" />} iconPosition="start"
            label="Upload File" sx={{ minHeight: 44, fontSize: '0.85rem' }} />
          <Tab icon={<TextFieldsIcon fontSize="small" />} iconPosition="start"
            label="Paste Text" sx={{ minHeight: 44, fontSize: '0.85rem' }} />
        </Tabs>
        <Box sx={{ p: 2.5 }}>
          {inputTab === 0
            ? <DropZone onFile={handleFile} loading={loading} />
            : <TextPasteZone onText={handleText} loading={loading} />
          }
        </Box>
      </Paper>

      {loading && <LinearProgress sx={{ borderRadius: 1 }} />}
      {error   && <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {result  && <ResultCard result={result} />}

      {/* Info box */}
      <Paper variant="outlined" sx={{ p: 2.5, mt: 3, bgcolor: 'grey.50' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>How it works</Typography>
        <Typography variant="body2" color="text.secondary">
          Your text is analysed by Groq (Llama 3.1) for signs of copied content — sudden style shifts,
          encyclopaedic language, well-known passages, and structural patterns common in plagiarised work.
          Colours: 🔴 red = likely copied, 🟠 orange = similar, 🟢 green = original.
          This is pattern analysis, not a live web search — results are indicative.
        </Typography>
      </Paper>

      <HistoryTable history={history} onDelete={handleDelete} onClearAll={handleClearAll} />
    </Box>
  );
}
