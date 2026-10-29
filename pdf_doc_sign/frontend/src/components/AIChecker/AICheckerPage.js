/**
 * AICheckerPage.js — Public combined AI + Plagiarism checker
 * Route: /ai-checker (public, no login required to view)
 *
 * - Works fully when logged in
 * - Shows sign-up prompt when not logged in
 * - Combined AI detection + Plagiarism on one page (tabs)
 * - Student-focused messaging
 * - SEO: via react-helmet-async
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Paper, Typography, Button, LinearProgress, Alert,
  Chip, Divider, Tooltip, Tab, Tabs, TextField,
  CircularProgress, AppBar, Toolbar, Container, Grid,
} from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import PersonIcon from '@mui/icons-material/Person';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import SchoolIcon from '@mui/icons-material/School';
import LockIcon from '@mui/icons-material/Lock';
import { aiDetectorService, plagiarismService } from '../../services/api';
import SEO from '../Common/SEO';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function isLoggedIn() {
  return !!localStorage.getItem('accessToken');
}

function aiVerdictColour(verdict) {
  if (verdict === 'LIKELY_AI')    return 'error';
  if (verdict === 'POSSIBLY_AI')  return 'warning';
  if (verdict === 'LIKELY_HUMAN') return 'success';
  return 'default';
}

function plagVerdictColour(verdict) {
  if (verdict === 'LIKELY_PLAGIARISED') return 'error';
  if (verdict === 'POSSIBLY_SIMILAR')   return 'warning';
  if (verdict === 'MOSTLY_ORIGINAL')    return 'success';
  return 'default';
}

// ─── Sentence highlighting ────────────────────────────────────────────────────
function SentenceHighlighter({ sentences, type }) {
  if (!sentences?.length) return null;

  const getColours = (label) => {
    if (type === 'ai') {
      if (label === 'AI')    return { bg: 'rgba(211,47,47,0.13)', border: '#d32f2f' };
      if (label === 'Human') return { bg: 'rgba(46,125,50,0.10)', border: '#2e7d32' };
      return { bg: 'rgba(237,108,2,0.10)', border: '#ed6c02' };
    }
    if (label === 'Copied')   return { bg: 'rgba(211,47,47,0.13)', border: '#d32f2f' };
    if (label === 'Original') return { bg: 'rgba(46,125,50,0.10)', border: '#2e7d32' };
    return { bg: 'rgba(237,108,2,0.10)', border: '#ed6c02' };
  };

  return (
    <Box sx={{ mt: 1.5, lineHeight: 2.2, fontSize: '0.88rem' }}>
      {sentences.map((s, i) => {
        const c = getColours(s.label);
        const prob = type === 'ai'
          ? Math.round((s.ai_probability || 0) * 100)
          : Math.round((s.plagiarism_probability || 0) * 100);
        return (
          <Tooltip key={i} title={`${s.label} — ${prob}%`} placement="top">
            <span style={{
              backgroundColor: c.bg,
              borderBottom: `2px solid ${c.border}`,
              borderRadius: 3, padding: '1px 2px', marginRight: 4,
              cursor: 'default', display: 'inline',
            }}>
              {s.text}
            </span>
          </Tooltip>
        );
      })}
    </Box>
  );
}

// ─── Score Gauge ─────────────────────────────────────────────────────────────
function ScoreGauge({ leftPct, rightPct, leftLabel, rightLabel, leftColour, rightColour }) {
  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ height: 18, borderRadius: 9, overflow: 'hidden', display: 'flex' }}>
        <Box sx={{ width: `${leftPct}%`, bgcolor: leftColour, transition: 'width 0.9s ease' }} />
        <Box sx={{ width: `${rightPct}%`, bgcolor: rightColour, transition: 'width 0.9s ease' }} />
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mt: 0.8 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: leftColour }} />
          <Typography variant="caption" color="text.secondary">{leftPct}% {leftLabel}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: rightColour }} />
          <Typography variant="caption" color="text.secondary">{rightPct}% {rightLabel}</Typography>
        </Box>
      </Box>
    </Box>
  );
}

// ─── Result Panel ─────────────────────────────────────────────────────────────
function ResultPanel({ aiResult, plagResult }) {
  if (!aiResult && !plagResult) return null;

  return (
    <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
      {aiResult && (
        <Paper elevation={2} sx={{ borderLeft: 5, borderColor: `${aiVerdictColour(aiResult.verdict)}.main`, p: 2.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <SmartToyIcon color={aiResult.verdict === 'LIKELY_HUMAN' ? 'success' : 'error'} />
            <Typography variant="subtitle1" fontWeight={700}>AI Detection</Typography>
            <Chip
              label={
                aiResult.verdict === 'LIKELY_AI'    ? `${aiResult.ai_percentage}% AI Generated` :
                aiResult.verdict === 'POSSIBLY_AI'  ? `${aiResult.ai_percentage}% Possibly AI` :
                aiResult.verdict === 'LIKELY_HUMAN' ? `${100 - (aiResult.ai_percentage || 0)}% Human Written` :
                aiResult.verdict
              }
              color={aiVerdictColour(aiResult.verdict)}
              size="small"
              sx={{ fontWeight: 700 }}
            />
          </Box>
          {aiResult.ai_percentage !== null && (
            <ScoreGauge
              leftPct={aiResult.human_percentage ?? (100 - aiResult.ai_percentage)}
              rightPct={aiResult.ai_percentage}
              leftLabel="Human" rightLabel="AI"
              leftColour="#2e7d32" rightColour="#d32f2f"
            />
          )}
          {aiResult.sentence_analysis?.length > 0 && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', fontWeight: 600 }}>
                Sentence breakdown
              </Typography>
              <SentenceHighlighter sentences={aiResult.sentence_analysis} type="ai" />
            </>
          )}
          {aiResult.explanation && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, fontStyle: 'italic' }}>
              {aiResult.explanation}
            </Typography>
          )}
        </Paper>
      )}

      {plagResult && (
        <Paper elevation={2} sx={{ borderLeft: 5, borderColor: `${plagVerdictColour(plagResult.verdict)}.main`, p: 2.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <ContentCopyIcon color={plagResult.verdict === 'MOSTLY_ORIGINAL' ? 'success' : 'error'} />
            <Typography variant="subtitle1" fontWeight={700}>Plagiarism Check</Typography>
            <Chip
              label={
                plagResult.verdict === 'LIKELY_PLAGIARISED' ? `${plagResult.plagiarism_percentage}% Plagiarised` :
                plagResult.verdict === 'POSSIBLY_SIMILAR'   ? `${plagResult.plagiarism_percentage}% Similar` :
                plagResult.verdict === 'MOSTLY_ORIGINAL'    ? `${plagResult.original_percentage}% Original` :
                plagResult.verdict
              }
              color={plagVerdictColour(plagResult.verdict)}
              size="small"
              sx={{ fontWeight: 700 }}
            />
          </Box>
          {plagResult.plagiarism_percentage !== null && (
            <ScoreGauge
              leftPct={plagResult.original_percentage ?? (100 - plagResult.plagiarism_percentage)}
              rightPct={plagResult.plagiarism_percentage}
              leftLabel="Original" rightLabel="Plagiarised"
              leftColour="#2e7d32" rightColour="#d32f2f"
            />
          )}
          {plagResult.sentence_matches?.length > 0 && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', fontWeight: 600 }}>
                Sentence breakdown
              </Typography>
              <SentenceHighlighter sentences={plagResult.sentence_matches} type="plagiarism" />
            </>
          )}
          {plagResult.explanation && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, fontStyle: 'italic' }}>
              {plagResult.explanation}
            </Typography>
          )}
          <Alert severity="info" sx={{ mt: 2 }} icon={false}>
            <Typography variant="caption">
              Pattern analysis only — not a live web search. Upgrade to Pro for real source URLs.
            </Typography>
          </Alert>
        </Paper>
      )}
    </Box>
  );
}

// ─── Sign-up prompt (shown when not logged in) ────────────────────────────────
function SignUpPrompt({ navigate }) {
  return (
    <Paper
      elevation={3}
      sx={{
        p: 4, textAlign: 'center', borderRadius: 3,
        background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
        color: 'white',
      }}
    >
      <LockIcon sx={{ fontSize: 48, mb: 1, opacity: 0.9 }} />
      <Typography variant="h5" fontWeight={700} gutterBottom>
        Create a Free Account to Check Your Work
      </Typography>
      <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
        Sign up free and get AI detection + plagiarism checking included.
        No credit card required.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button variant="contained" size="large" onClick={() => navigate('/register')}
          sx={{ bgcolor: 'white', color: 'primary.main', fontWeight: 700, '&:hover': { bgcolor: 'grey.100' } }}>
          Sign Up Free
        </Button>
        <Button variant="outlined" size="large" onClick={() => navigate('/login')}
          sx={{ borderColor: 'white', color: 'white', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}>
          Log In
        </Button>
      </Box>
    </Paper>
  );
}

// ─── Feature cards ────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: <SmartToyIcon color="error" sx={{ fontSize: 36 }} />, title: 'AI Detection', desc: 'Detect ChatGPT, Claude & other AI-generated content with sentence-level highlighting.' },
  { icon: <ContentCopyIcon color="warning" sx={{ fontSize: 36 }} />, title: 'Plagiarism Check', desc: 'Find copied passages and style shifts that suggest content was taken from other sources.' },
  { icon: <SchoolIcon color="primary" sx={{ fontSize: 36 }} />, title: 'Built for Students', desc: 'Check your essay before submission. See exactly which sentences are flagged and why.' },
];

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function AICheckerPage() {
  const navigate  = useNavigate();
  const loggedIn  = isLoggedIn();
  const [mode, setMode]         = useState(0);
  const [text, setText]         = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [aiResult, setAiResult] = useState(null);
  const [plagResult, setPlagResult] = useState(null);

  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
  const canSubmit = loggedIn && text.trim().length >= 50 && !loading;

  const handleCheck = async () => {
    setError(''); setAiResult(null); setPlagResult(null);
    setLoading(true);
    try {
      const tasks = [];
      if (mode === 0 || mode === 2) tasks.push(aiDetectorService.scanText(text.trim()).then(setAiResult).catch(() => {}));
      if (mode === 1 || mode === 2) tasks.push(plagiarismService.scanText(text.trim()).then(setPlagResult).catch(() => {}));
      await Promise.all(tasks);
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#fafbfc' }}>
      <SEO
        title="Free AI & Plagiarism Checker – Detect AI Content"
        description="Check your work for AI-generated content and plagiarism — free for students and educators. Sentence-level highlighting shows exactly what's flagged."
        path="/ai-checker"
        keywords="AI detector, plagiarism checker, detect ChatGPT, AI content checker free, essay checker UK"
      />

      {/* Navbar */}
      <AppBar position="sticky" color="inherit" elevation={1}>
        <Toolbar>
          <Typography variant="h6" fontWeight={700} color="primary"
            sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
            SignSimple
          </Typography>
          {loggedIn ? (
            <Button variant="outlined" size="small" onClick={() => navigate('/dashboard')}>Dashboard</Button>
          ) : (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" onClick={() => navigate('/login')}>Log in</Button>
              <Button variant="contained" size="small" onClick={() => navigate('/register')}>Sign up free</Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ py: 6 }}>
        <Box sx={{ textAlign: 'center', mb: 5 }}>
          <Chip label="Free for students" color="primary" size="small" sx={{ mb: 2 }} />
          <Typography variant="h3" fontWeight={800} gutterBottom sx={{ lineHeight: 1.2 }}>
            AI & Plagiarism Checker
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 560, mx: 'auto' }}>
            Check your work for AI-generated content AND plagiarism — in one place.
            Submit with confidence.
          </Typography>
        </Box>

        <Grid container spacing={2} sx={{ mb: 5 }}>
          {FEATURES.map((f) => (
            <Grid item xs={12} sm={4} key={f.title}>
              <Paper variant="outlined" sx={{ p: 2.5, textAlign: 'center', height: '100%', borderRadius: 2 }}>
                {f.icon}
                <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 1 }}>{f.title}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{f.desc}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Paper elevation={2} sx={{ borderRadius: 3, overflow: 'hidden' }}>
          <Tabs
            value={mode}
            onChange={(_, v) => { setMode(v); setAiResult(null); setPlagResult(null); setError(''); }}
            sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.50', minHeight: 48 }}
            centered
          >
            <Tab icon={<SmartToyIcon fontSize="small" />} iconPosition="start" label="AI Detector" sx={{ minHeight: 48, fontSize: '0.9rem' }} />
            <Tab icon={<ContentCopyIcon fontSize="small" />} iconPosition="start" label="Plagiarism" sx={{ minHeight: 48, fontSize: '0.9rem' }} />
            <Tab icon={<CheckCircleOutlineIcon fontSize="small" />} iconPosition="start" label="Both" sx={{ minHeight: 48, fontSize: '0.9rem' }} />
          </Tabs>

          <Box sx={{ p: 3 }}>
            <TextField
              multiline rows={7} fullWidth
              placeholder={
                mode === 0 ? 'Paste your text here to check if it was written by AI…' :
                mode === 1 ? 'Paste your essay or article to check for plagiarism…' :
                'Paste your text here to run both AI detection and plagiarism check…'
              }
              value={text}
              onChange={(e) => { setText(e.target.value); setAiResult(null); setPlagResult(null); }}
              disabled={loading}
              sx={{ mb: 2, '& .MuiOutlinedInput-root': { fontSize: '0.92rem', lineHeight: 1.7 } }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {text.length.toLocaleString()} characters · {wordCount} words
                {text.length > 0 && text.length < 50 && (
                  <span style={{ color: '#d32f2f' }}> · minimum 50 characters</span>
                )}
              </Typography>

              {loggedIn ? (
                <Button variant="contained" size="large" disabled={!canSubmit} onClick={handleCheck}
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : (
                    mode === 0 ? <SmartToyIcon /> : mode === 1 ? <ContentCopyIcon /> : <CheckCircleOutlineIcon />
                  )}>
                  {loading ? 'Checking…' : mode === 0 ? 'Detect AI' : mode === 1 ? 'Check Plagiarism' : 'Check Both'}
                </Button>
              ) : (
                <Button variant="contained" size="large" onClick={() => navigate('/register')} startIcon={<LockIcon />}>
                  Sign up free to check
                </Button>
              )}
            </Box>
          </Box>
        </Paper>

        {loading && <LinearProgress sx={{ mt: 1, borderRadius: 1 }} />}
        {error   && <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>{error}</Alert>}

        <ResultPanel aiResult={aiResult} plagResult={plagResult} />

        {!loggedIn && (
          <Box sx={{ mt: 5 }}>
            <SignUpPrompt navigate={navigate} />
          </Box>
        )}

        <Paper variant="outlined" sx={{ p: 2.5, mt: 4, bgcolor: 'grey.50', borderRadius: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <LightbulbIcon fontSize="small" color="warning" />
            <Typography variant="subtitle2" fontWeight={600}>How it works</Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8 }}>
            <strong>AI Detector</strong> — analyses writing patterns (perplexity, sentence structure, vocabulary uniformity)
            to determine if text was written by AI like ChatGPT or Claude. Sentence-level colour coding shows which
            parts are flagged. 🔴 Red = AI, 🟠 Orange = Mixed, 🟢 Green = Human.
            <br /><br />
            <strong>Plagiarism Checker</strong> — detects copied passages, sudden style shifts, and encyclopaedic language
            patterns. 🔴 Red = likely copied, 🟠 Orange = similar, 🟢 Green = original.
            Pattern analysis — not a live web search.
          </Typography>
        </Paper>

        <Box sx={{ textAlign: 'center', mt: 6, pb: 3 }}>
          <Typography variant="caption" color="text.secondary">
            SignSimple · AI & Plagiarism Checker · UK document storage · GDPR compliant
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}
