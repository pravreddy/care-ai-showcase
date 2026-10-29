/**
 * AIDetectorPage.js — v4
 * AI Content Detection with Turnitin-style report view.
 *
 * Changes from v3:
 *  - "View Full Report" button on result card opens TurnitinReport
 *  - Shows chunks analysed count
 *  - Progress indicator during multi-chunk analysis
 *  - Result card shows AI sentence count
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, LinearProgress, Alert,
  Chip, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, CircularProgress, Divider, Tooltip, Tab, Tabs,
  ToggleButton, ToggleButtonGroup, TextField, IconButton,
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import HistoryIcon from '@mui/icons-material/History';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ArticleIcon from '@mui/icons-material/Article';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import ReplayIcon from '@mui/icons-material/Replay';
import { aiDetectorService } from '../../services/api';
import TurnitinReport from './TurnitinReport';

const SUPPORTED_TYPES = ['pdf', 'docx', 'txt', 'pptx', 'xlsx'];
const ACCEPT = '.pdf,.docx,.txt,.pptx,.xlsx';
const MAX_MB = 10;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function verdictColour(verdict) {
  if (verdict === 'LIKELY_AI') return 'error';
  if (verdict === 'POSSIBLY_AI') return 'warning';
  if (verdict === 'LIKELY_HUMAN') return 'success';
  return 'default';
}

function verdictLabel(verdict, aiPct) {
  if (verdict === 'LIKELY_AI')    return `Likely AI · ${aiPct}% AI`;
  if (verdict === 'POSSIBLY_AI')  return `Possibly AI · ${aiPct}% AI`;
  if (verdict === 'LIKELY_HUMAN') return `Likely Human · ${100 - aiPct}% Human`;
  if (verdict === 'INSUFFICIENT_TEXT') return 'Not enough text';
  if (verdict === 'ERROR')        return 'Detection failed';
  return verdict || '—';
}

function providerLabel(provider) {
  const map = { huggingface: 'HuggingFace', groq: 'Groq', grok: 'Grok', openai: 'OpenAI' };
  return map[provider] || provider;
}

// ─── Sentence colour ─────────────────────────────────────────────────────────
function sentenceBg(label) {
  if (label === 'AI') return 'rgba(0, 188, 212, 0.18)';   // cyan like Turnitin
  if (label === 'Human') return 'rgba(46,125,50,0.10)';
  return 'rgba(156,39,176,0.12)';                          // purple for mixed
}
function sentenceBorder(label) {
  if (label === 'AI') return '#00bcd4';
  if (label === 'Human') return '#2e7d32';
  return '#9c27b0';
}

// ─── Gauge ────────────────────────────────────────────────────────────────────
function AiGauge({ aiPct, humanPct, mixedPct }) {
  return (
    <Box sx={{ mt: 2.5 }}>
      <Box sx={{ height: 22, borderRadius: 11, overflow: 'hidden', display: 'flex' }}>
        <Box sx={{ width: `${humanPct}%`, bgcolor: '#2e7d32', transition: 'width 0.9s ease' }} />
        <Box sx={{ width: `${mixedPct || 0}%`, bgcolor: '#9c27b0', transition: 'width 0.9s ease' }} />
        <Box sx={{ width: `${aiPct}%`, bgcolor: '#00bcd4', transition: 'width 0.9s ease' }} />
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mt: 1, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#2e7d32' }} />
          <Typography variant="caption" color="text.secondary">{humanPct}% Human</Typography>
        </Box>
        {mixedPct > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#9c27b0' }} />
            <Typography variant="caption" color="text.secondary">{mixedPct}% Mixed</Typography>
          </Box>
        )}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#00bcd4' }} />
          <Typography variant="caption" color="text.secondary">{aiPct}% AI</Typography>
        </Box>
      </Box>
    </Box>
  );
}

// ─── Sentence Highlighter ─────────────────────────────────────────────────────
function SentenceHighlighter({ sentences }) {
  if (!sentences || !sentences.length) return null;
  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: 'flex', gap: 1.5, mb: 1.5, flexWrap: 'wrap' }}>
        {[
          { label: 'AI', colour: '#00bcd4', bg: 'rgba(0,188,212,0.15)' },
          { label: 'Mixed', colour: '#9c27b0', bg: 'rgba(156,39,176,0.1)' },
          { label: 'Human', colour: '#2e7d32', bg: 'rgba(46,125,50,0.1)' },
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
            title={`${s.label} — ${Math.round((s.ai_probability || 0) * 100)}% AI probability`}
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
function ResultCard({ result, onViewReport, onDeepScan }) {
  const aiPct = result.ai_percentage ?? 0;
  const humanPct = result.human_percentage ?? (100 - aiPct);
  const mixedPct = result.mixed_percentage ?? 0;
  const colour = verdictColour(result.verdict);
  const [tab, setTab] = useState(0);
  const hasSentences = result.sentence_analysis?.length > 0;
  const hasExplanation = !!result.explanation;

  const tabs = [];
  if (hasSentences) tabs.push({ label: 'Sentence Analysis', icon: <SmartToyIcon fontSize="small" /> });
  if (result.extracted_text) tabs.push({ label: 'Full Text', icon: <ArticleIcon fontSize="small" /> });
  if (hasExplanation) tabs.push({ label: 'AI Reasoning', icon: <LightbulbIcon fontSize="small" /> });

  // v4: count AI sentences
  const aiSentences = (result.sentence_analysis || []).filter(s => s.label === 'AI').length;
  const totalSentences = (result.sentence_analysis || []).length;

  return (
    <Paper elevation={2} sx={{ mt: 3, borderLeft: 5, borderColor: `${colour}.main`, overflow: 'hidden' }}>
      {/* Header */}
      <Box sx={{ p: 2.5, pb: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, flexWrap: 'wrap' }}>
          {result.verdict === 'LIKELY_HUMAN'
            ? <PersonIcon color="success" fontSize="large" />
            : <SmartToyIcon color={result.verdict === 'LIKELY_AI' ? 'error' : 'warning'} fontSize="large" />
          }
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={700} noWrap sx={{ maxWidth: 500 }}>
              {result.original_filename}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
              <Chip label={verdictLabel(result.verdict, aiPct)} color={colour} size="small" sx={{ fontWeight: 700 }} />
              {result.provider === 'groq_deep' && (
                <Chip label="Deep Scan" size="small" variant="outlined" color="secondary" />
              )}
              <Chip label={result.file_type?.toUpperCase()} size="small" variant="outlined" />
              {result.chunks_analysed > 1 && (
                <Chip label={`${result.chunks_analysed} sections analysed`} size="small" variant="outlined" color="info" />
              )}
            </Box>
          </Box>

          {/* View Full Report button */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            {result.provider !== 'groq_deep' && onDeepScan && (
              <Button variant="outlined" size="small" startIcon={<SearchIcon />} onClick={onDeepScan}
                sx={{ fontWeight: 700, whiteSpace: 'nowrap' }}>Run Deep Scan</Button>
            )}
            <Button variant="contained" size="small" startIcon={<AssessmentIcon />} onClick={onViewReport}
              sx={{ fontWeight: 700, whiteSpace: 'nowrap' }}>View Full Report</Button>
          </Box>
        </Box>

        {result.ai_percentage !== null && (
          <AiGauge aiPct={aiPct} humanPct={humanPct} mixedPct={mixedPct} />
        )}

        {result.error_message && (
          <Alert severity="warning" sx={{ mt: 2 }}>{result.error_message}</Alert>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'block' }}>
          {result.file_type !== 'txt' || result.original_filename !== 'Pasted text'
            ? `${(result.file_size_bytes / 1024).toFixed(0)} KB · `
            : ''
          }
          {result.text_length?.toLocaleString()} chars · {totalSentences} sentences analysed
          {aiSentences > 0 && (
            <span style={{ color: '#d32f2f', fontWeight: 600 }}>
              {' '}· {aiSentences} flagged as AI
            </span>
          )}
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
              <SentenceHighlighter sentences={result.sentence_analysis} />
            )}
            {tabs[tab]?.label === 'Full Text' && result.extracted_text && (
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                <Typography variant="body2" component="pre"
                  sx={{ fontFamily: 'monospace', fontSize: '0.78rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.7 }}>
                  {result.extracted_text}
                </Typography>
              </Paper>
            )}
            {tabs[tab]?.label === 'AI Reasoning' && result.explanation && (
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <LightbulbIcon color="warning" fontSize="small" />
                  <Typography variant="subtitle2" fontWeight={600}>
                    Detection reasoning
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                  {result.explanation}
                </Typography>
              </Paper>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
}

// ─── Provider Selector ───────────────────────────────────────────────────────
function ProviderSelector({ providers, selected, onChange }) {
  if (!providers.length) return null;
  return (
    <Box sx={{ mb: 2.5 }}>
      <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ mb: 0.5, display: 'block' }}>
        Detection Engine
      </Typography>
      <ToggleButtonGroup value={selected} exclusive onChange={(_, v) => v && onChange(v)} size="small">
        {providers.map((p) => (
          <ToggleButton key={p.id} value={p.id} disabled={!p.available} sx={{ px: 2, fontSize: '0.8rem' }}>
            <Tooltip title={p.available ? `${p.description} · ${p.cost}` : 'API key not configured'}>
              <span>
                {p.name}
                {p.has_sentences && (
                  <SmartToyIcon fontSize="inherit" sx={{ ml: 0.5, verticalAlign: 'middle', color: 'primary.main', opacity: 0.7 }} />
                )}
              </span>
            </Tooltip>
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
      {providers.find((p) => p.id === selected)?.has_sentences && (
        <Typography variant="caption" color="primary.dark" sx={{ mt: 0.5, display: 'block' }}>
          🔍 Sentence-level highlighting + full document chunking enabled
        </Typography>
      )}
    </Box>
  );
}

// ─── File Drop Zone ───────────────────────────────────────────────────────────
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
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1.5 }}>
            Uploading document…
          </Typography>
        </Box>
      ) : (
        <Box>
          <UploadFileIcon sx={{ fontSize: 52, color: 'primary.main', mb: 1 }} />
          <Typography variant="h6" fontWeight={600}>Drop your file here</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>or click to browse · full document analysis up to 50,000 chars</Typography>
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
            {SUPPORTED_TYPES.map((t) => (
              <Chip key={t} label={`.${t}`} size="small" variant="outlined" />
            ))}
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
        placeholder="Paste or type text here to check if it was written by AI…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
        sx={{ '& .MuiOutlinedInput-root': { fontFamily: 'inherit', fontSize: '0.9rem', lineHeight: 1.7 } }}
      />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {text.length.toLocaleString()} characters · {wordCount} words
          {text.length < 50 && text.length > 0 && (
            <span style={{ color: '#d32f2f' }}> · minimum 50 characters</span>
          )}
        </Typography>
        <Button
          variant="contained" size="medium"
          disabled={loading || text.trim().length < 50}
          onClick={() => onText(text.trim())}
          startIcon={loading ? <CircularProgress size={16} /> : <SmartToyIcon />}
        >
          {loading ? 'Submitting…' : 'Detect AI'}
        </Button>
      </Box>
    </Box>
  );
}

// ─── History Table ────────────────────────────────────────────────────────────
function HistoryTable({ history, onDelete, onClearAll, onViewReport, onReprocess }) {
  if (!history.length) return null;
  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon fontSize="small" color="action" />
          <Typography variant="subtitle1" fontWeight={600}>Recent Scans</Typography>
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
              <TableCell sx={{ fontWeight: 600 }}>Provider</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Verdict</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>AI %</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Sections</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Scanned</TableCell>
              <TableCell sx={{ fontWeight: 600 }} align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 180 }}>{row.original_filename}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={row.provider === 'groq_deep' ? 'Deep' : 'Quick'}
                    size="small" variant="outlined"
                    color={row.provider === 'groq_deep' ? 'secondary' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  {row.status === 'processing' ? (
                    <Chip label="Processing…" color="info" size="small" icon={<CircularProgress size={12} />} />
                  ) : (
                    <Chip label={verdictLabel(row.verdict, row.ai_percentage)} color={verdictColour(row.verdict)} size="small" />
                  )}
                </TableCell>
                <TableCell>{row.ai_percentage !== null ? `${row.ai_percentage}%` : '—'}</TableCell>
                <TableCell>{row.chunks_analysed || 1}</TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(row.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'flex-end' }}>
                    {row.status === 'failed' && (
                      <Tooltip title="Reprocess this scan">
                        <IconButton size="small" color="warning" onClick={() => onReprocess(row.id)}>
                          <ReplayIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {row.sentence_analysis?.length > 0 && (
                      <Tooltip title="View full report">
                        <IconButton size="small" color="primary" onClick={() => onViewReport(row)}>
                          <AssessmentIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete this scan">
                      <IconButton size="small" color="error" onClick={() => onDelete(row.id)}>
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

// ─── Processing Card (simple — no polling) ───────────────────────────────────
function ProcessingCard({ scan }) {
  if (!scan) return null;
  return (
    <Paper elevation={2} sx={{ mt: 3, borderLeft: 5, borderColor: 'info.main', overflow: 'hidden' }}>
      <Box sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <SmartToyIcon color="info" fontSize="large" />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={700}>{scan.original_filename}</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip label="Processing" color="info" size="small" sx={{ fontWeight: 700 }} />
              <Chip label={scan.file_type?.toUpperCase()} size="small" variant="outlined" />
              <Chip label={`${(scan.text_length || 0).toLocaleString()} chars`} size="small" variant="outlined" />
            </Box>
          </Box>
        </Box>
        <Alert severity="info" sx={{ mt: 2 }} icon={false}>
          <Typography variant="body2" fontWeight={600}>Your document is being analysed.</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            You can close this page and do other things. Come back and click the refresh
            button below to check if your results are ready.
          </Typography>
        </Alert>
      </Box>
    </Paper>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function AIDetectorPage() {
  const [inputTab, setInputTab] = useState(0); // 0=file, 1=text
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [providers, setProviders] = useState([]);
  // Default to 'auto' (fast cloud). Users can pick a specific engine, e.g. Local LLM.
  const [selectedProvider, setSelectedProvider] = useState('auto');
  const [reportResult, setReportResult] = useState(null);
  const [processingScan, setProcessingScan] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadHistory = async () => {
    try {
      const data = await aiDetectorService.getHistory();
      const scans = data.results || [];
      setHistory(scans);
      // If we were showing a processing card, check if it's done
      if (processingScan) {
        const updated = scans.find(s => s.id === processingScan.id);
        if (updated && (updated.status === 'completed' || updated.status === 'failed')) {
          setProcessingScan(null);
          if (updated.status === 'completed') setResult(updated);
          else setError(updated.error_message || 'Detection failed.');
        }
      }
    } catch {} // silently fail
  };

  useEffect(() => {
    aiDetectorService.getHistory()
      .then((data) => {
        const scans = data.results || [];
        setHistory(scans);
        // Check if any scans are still processing
        const pending = scans.find(s => s.status === 'processing');
        if (pending) setProcessingScan(pending);
      })
      .catch(() => {});
    aiDetectorService.getProviders()
      .then((data) => setProviders(data.providers || []))
      .catch(() => {});
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadHistory();
    setRefreshing(false);
  };

  const handleResult = (data) => {
    // Backend returns 'processing' — show card, user refreshes later
    if (data.status === 'processing' || data.status === 'pending') {
      setProcessingScan(data);
      setLoading(false);
      setHistory((prev) => [data, ...prev.filter((h) => h.id !== data.id).slice(0, 49)]);
      return;
    }
    setResult(data);
    setHistory((prev) => [data, ...prev.filter((h) => h.id !== data.id).slice(0, 49)]);
  };

  const handleFile = async (file) => {
    setError('');
    setResult(null);
    const ext = file.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_TYPES.includes(ext)) {
      setError(`Unsupported file type: .${ext}`);
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File too large. Maximum is ${MAX_MB}MB.`);
      return;
    }
    setLoading(true);
    try {
      handleResult(await aiDetectorService.scan(file, selectedProvider));
    } catch (err) {
      setError(err.response?.data?.error || 'Detection failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleText = async (text) => {
    setError('');
    setResult(null);
    setLoading(true);
    try {
      handleResult(await aiDetectorService.scanText(text, selectedProvider));
    } catch (err) {
      setError(err.response?.data?.error || 'Detection failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await aiDetectorService.deleteScan(id);
      setHistory((prev) => prev.filter((h) => h.id !== id));
      if (result?.id === id) setResult(null);
    } catch {
      // silently fail
    }
  };

  const handleClearAll = async () => {
    await Promise.allSettled(history.map((h) => aiDetectorService.deleteScan(h.id)));
    setHistory([]);
    setResult(null);
  };

  const handleDeepScan = async (scanId) => {
    try {
      const data = await aiDetectorService.deepScan(scanId);
      setProcessingScan(data);
      setHistory((prev) => [data, ...prev.slice(0, 49)]);
    } catch (err) {
      setError(err.response?.data?.error || 'Deep scan failed.');
    }
  };

  const handleReprocess = async (id) => {
    try {
      const data = await aiDetectorService.reprocessScan(id);
      setProcessingScan(data);
      setResult(null);
      setError('');
      setHistory((prev) => prev.map((h) => h.id === id ? data : h));
    } catch (err) {
      setError(err.response?.data?.error || 'Reprocess failed.');
    }
  };

  // ── v4: If viewing a report, show TurnitinReport instead ──
  if (reportResult) {
    return (
      <TurnitinReport
        result={reportResult}
        onClose={() => setReportResult(null)}
      />
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
          <SmartToyIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h5" fontWeight={700}>AI Content Detector</Typography>
          <Tooltip title="Upload a file or paste text to check if it was written by AI. Analyses the FULL document with sentence-level highlighting.">
            <HelpOutlineIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
          </Tooltip>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Full-document AI detection with sentence-level highlighting.
        </Typography>
      </Box>

      <Divider sx={{ mb: 3 }} />

      {/* Engine selector — defaults to Auto (fast cloud); Local LLM is opt-in */}
      <ProviderSelector
        providers={providers.filter((p) => p.available)}
        selected={selectedProvider}
        onChange={setSelectedProvider}
      />

      {/* Input tabs */}
      <Paper variant="outlined" sx={{ borderRadius: 3, overflow: 'hidden', mb: 2 }}>
        <Tabs value={inputTab} onChange={(_, v) => { setInputTab(v); setError(''); setResult(null); }}
          sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50', minHeight: 44 }}>
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

      {/* Error */}
      {error && <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>{error}</Alert>}

      {/* Processing indicator + Refresh button */}
      {processingScan && <ProcessingCard scan={processingScan} />}

      {/* Refresh button — always visible when there's a processing scan or history */}
      {(processingScan || history.some(h => h.status === 'processing')) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button
            variant="contained" color="info" size="large"
            startIcon={refreshing ? <CircularProgress size={18} color="inherit" /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
            sx={{ fontWeight: 700, px: 4 }}
          >
            {refreshing ? 'Checking…' : 'Refresh Results'}
          </Button>
        </Box>
      )}

      {/* Result */}
      {result && !processingScan && (
        <ResultCard
          result={result}
          onViewReport={() => setReportResult(result)}
          onDeepScan={() => handleDeepScan(result.id)}
        />
      )}

      {/* How it works */}
      <Paper variant="outlined" sx={{ p: 2.5, mt: 3, bgcolor: 'grey.50' }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>How it works</Typography>
        <Typography variant="body2" color="text.secondary">
          Upload your document or paste text. Our detection engine analyses the full content
          with sentence-level highlighting, showing which parts appear AI-generated.
          Results typically appear within seconds. You can return anytime and click
          "Refresh Results" to check scans in progress. Click "View Full Report"
          for a detailed Turnitin-style report.
        </Typography>
      </Paper>

      {/* History with report view */}
      <HistoryTable
        history={history}
        onDelete={handleDelete}
        onClearAll={handleClearAll}
        onViewReport={(scan) => setReportResult(scan)}
        onReprocess={handleReprocess}
      />
    </Box>
  );
}
