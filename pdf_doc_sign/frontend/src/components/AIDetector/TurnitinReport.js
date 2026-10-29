/**
 * TurnitinReport.js — Turnitin-style AI Detection Report
 * 
 * Displays a professional report matching Turnitin's AI writing report layout:
 *  - Cover section with document details (pages, words, chars)
 *  - AI Writing Overview with percentage gauge and detection groups
 *  - Full document with sentence-level highlighting (cyan for AI)
 *  - Disclaimer and FAQ section
 *
 * Props:
 *   result    — the scan result object from the API
 *   onClose   — callback to close the report view
 */
import React, { useState, useRef } from 'react';
import {
  Box, Paper, Typography, Button, Chip, Divider, Tooltip,
  IconButton, Alert, LinearProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import PrintIcon from '@mui/icons-material/Print';
import DownloadIcon from '@mui/icons-material/Download';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

// ─── Turnitin colour scheme ──────────────────────────────────────────────────
const COLOURS = {
  aiHighlight: 'rgba(0, 188, 212, 0.18)',
  aiBorder: '#00bcd4',
  aiText: '#006064',
  humanHighlight: 'transparent',
  headerBg: '#3f51b5',
  headerText: '#ffffff',
  cautionBg: '#fff3e0',
  cautionBorder: '#ff9800',
  sectionBg: '#fafafa',
};

function countWords(text) {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function estimatePages(text) {
  const words = countWords(text);
  return Math.max(1, Math.ceil(words / 300));
}

function AiPercentageCircle({ percentage }) {
  const size = 120;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;
  const getColor = () => {
    if (percentage >= 70) return '#d32f2f';
    if (percentage >= 40) return '#ff9800';
    if (percentage >= 20) return '#ffc107';
    return '#4caf50';
  };
  return (
    <Box sx={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#e0e0e0" strokeWidth={strokeWidth} />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={getColor()} strokeWidth={strokeWidth}
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1.5s ease' }} />
      </svg>
      <Box sx={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight={800} sx={{ color: getColor(), lineHeight: 1 }}>{percentage}%</Typography>
        <Typography variant="caption" color="text.secondary" fontWeight={600}>AI</Typography>
      </Box>
    </Box>
  );
}

function DetectionGroups({ sentences }) {
  const aiCount = (sentences || []).filter(s => s.label === 'AI').length;
  const mixedCount = (sentences || []).filter(s => s.label === 'Mixed').length;
  const total = sentences?.length || 0;
  const aiPct = total > 0 ? Math.round((aiCount / total) * 100) : 0;
  const mixedPct = total > 0 ? Math.round((mixedCount / total) * 100) : 0;
  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1.5, color: '#333' }}>Detection Groups</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
        <Box sx={{ width: 28, height: 28, borderRadius: '50%', bgcolor: COLOURS.aiHighlight, border: `2px solid ${COLOURS.aiBorder}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700, color: COLOURS.aiText }}>{aiCount}</Box>
        <Box>
          <Typography variant="body2" fontWeight={600}>AI-generated only {aiPct}%</Typography>
          <Typography variant="caption" color="text.secondary">Likely AI-generated text from a large-language model.</Typography>
        </Box>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box sx={{ width: 28, height: 28, borderRadius: '50%', bgcolor: 'rgba(156,39,176,0.1)', border: '2px solid #9c27b0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700, color: '#6a1b9a' }}>{mixedCount}</Box>
        <Box>
          <Typography variant="body2" fontWeight={600}>AI-generated text that was AI-paraphrased {mixedPct}%</Typography>
          <Typography variant="caption" color="text.secondary">Likely AI-generated text that was likely revised using an AI-paraphrase tool.</Typography>
        </Box>
      </Box>
    </Box>
  );
}

function CautionBanner({ aiPct }) {
  if (aiPct < 20) return null;
  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: COLOURS.cautionBg, borderColor: COLOURS.cautionBorder, borderRadius: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
        <WarningAmberIcon sx={{ color: '#e65100', mt: 0.3 }} fontSize="small" />
        <Box>
          <Typography variant="subtitle2" fontWeight={700} sx={{ color: '#e65100' }}>Caution: Review required.</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.6 }}>
            It is essential to understand the limitations of AI detection before making decisions about a student's work. AI detection may produce false positive or false negative results and should not be used as the sole basis for adverse actions.
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
}

function HighlightedDocument({ sentences, extractedText }) {
  if (!sentences?.length && extractedText) {
    return (<Paper variant="outlined" sx={{ p: 3, bgcolor: 'white' }}><Typography variant="body2" sx={{ lineHeight: 2, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{extractedText}</Typography></Paper>);
  }
  if (!sentences?.length) return null;
  return (
    <Paper variant="outlined" sx={{ p: 3, bgcolor: 'white' }}>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, pb: 1.5, borderBottom: '1px solid #e0e0e0' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Box sx={{ width: 16, height: 16, borderRadius: 1, bgcolor: COLOURS.aiHighlight, border: `1px solid ${COLOURS.aiBorder}` }} /><Typography variant="caption" fontWeight={600}>AI-generated</Typography></Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Box sx={{ width: 16, height: 16, borderRadius: 1, bgcolor: 'rgba(156,39,176,0.12)', border: '1px solid #9c27b0' }} /><Typography variant="caption" fontWeight={600}>Mixed / Paraphrased</Typography></Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Box sx={{ width: 16, height: 16, borderRadius: 1, bgcolor: '#f5f5f5', border: '1px solid #ccc' }} /><Typography variant="caption" fontWeight={600}>Human</Typography></Box>
      </Box>
      <Box sx={{ lineHeight: 2.2, fontSize: '0.92rem', fontFamily: '"Georgia", "Times New Roman", serif' }}>
        {sentences.map((s, i) => {
          const isAI = s.label === 'AI';
          const isMixed = s.label === 'Mixed';
          const prob = Math.round((s.ai_probability || 0) * 100);
          return (
            <Tooltip key={i} title={`${s.label} — ${prob}% AI probability`} placement="top" arrow>
              <span style={{
                backgroundColor: isAI ? COLOURS.aiHighlight : isMixed ? 'rgba(156, 39, 176, 0.12)' : 'transparent',
                borderBottom: isAI ? `2px solid ${COLOURS.aiBorder}` : isMixed ? '2px solid #9c27b0' : 'none',
                padding: isAI || isMixed ? '2px 1px' : '0', borderRadius: 2, cursor: 'default', display: 'inline', transition: 'background-color 0.2s',
              }}>{s.text}{' '}</span>
            </Tooltip>
          );
        })}
      </Box>
    </Paper>
  );
}

function Disclaimer() {
  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 3, bgcolor: '#f5f5f5' }}>
      <Typography variant="caption" fontWeight={600} gutterBottom sx={{ display: 'block', color: '#555' }}>Disclaimer</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.7 }}>
        This AI writing assessment is designed to help identify text that might be prepared by a generative AI tool. It may not always be accurate (i.e., it may produce either false positive or false negative results), so it should not be used as the sole basis for adverse actions. It takes further scrutiny and human judgement in conjunction with an organisation's specific policies to determine whether any misconduct has occurred. Scores under 20% have a higher likelihood of false positives.
      </Typography>
    </Paper>
  );
}

function FAQSection() {
  const [expanded, setExpanded] = useState(false);
  const faqs = [
    { q: 'How should I interpret the AI writing percentage?', a: 'The percentage shown is the amount of qualifying text that our detection model determines was likely AI-generated. False positives are possible. Scores under 20% have a higher likelihood of false positives. The percentage should not be the sole basis to determine misconduct — use it to start a conversation with the student.' },
    { q: 'What does "qualifying text" mean?', a: 'Our model processes qualifying text in the form of long-form writing — sentences within paragraphs that form essays, articles, or reports. Non-qualifying text such as bullet points, tables, and bibliographies will not be analysed and can create differences between highlights and the percentage shown.' },
    { q: 'Why might a sentence be flagged incorrectly?', a: 'Professional, formal, or regulatory writing often shares patterns with AI-generated text — uniform structure, formal vocabulary, and careful phrasing. Healthcare, legal, and academic contexts naturally produce writing that AI detectors can misinterpret. Always review flagged content in context.' },
  ];
  return (
    <Paper variant="outlined" sx={{ mt: 3 }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
        <Typography variant="subtitle2" fontWeight={700}>Frequently Asked Questions</Typography>
        <IconButton size="small">{expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}</IconButton>
      </Box>
      {expanded && (<Box sx={{ px: 2, pb: 2 }}>{faqs.map((faq, i) => (<Box key={i} sx={{ mb: 2 }}><Typography variant="body2" fontWeight={700} sx={{ mb: 0.5 }}>{faq.q}</Typography><Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.7 }}>{faq.a}</Typography></Box>))}</Box>)}
    </Paper>
  );
}

export default function TurnitinReport({ result, onClose }) {
  const reportRef = useRef();
  if (!result) return null;
  const aiPct = result.ai_percentage ?? Math.round((result.ai_probability || 0) * 100);
  const sentences = result.sentence_analysis || [];
  const text = result.extracted_text || '';
  const words = countWords(text);
  const pages = estimatePages(text);
  const chars = text.length;
  const fileName = result.original_filename || 'Document';
  const scanDate = result.created_at
    ? new Date(result.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    : new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  const aiSentenceCount = sentences.filter(s => s.label === 'AI').length;
  const chunksAnalysed = result.chunks_analysed || 1;

  return (
    <Box ref={reportRef} sx={{ maxWidth: 900, mx: 'auto', py: 3, '@media print': { maxWidth: '100%', py: 0 } }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, '@media print': { display: 'none' } }}>
        <Button variant="outlined" size="small" startIcon={<CloseIcon />} onClick={onClose}>Back to Results</Button>
        <Button variant="outlined" size="small" startIcon={<PrintIcon />} onClick={() => window.print()}>Print Report</Button>
      </Box>

      {/* COVER SECTION */}
      <Paper elevation={2} sx={{ overflow: 'hidden', mb: 3 }}>
        <Box sx={{ bgcolor: COLOURS.headerBg, color: COLOURS.headerText, px: 3, py: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle2" fontWeight={600}>SignSimple AI Detection Report</Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>{scanDate}</Typography>
          </Box>
        </Box>
        <Box sx={{ p: 3 }}>
          <Typography variant="h5" fontWeight={800} sx={{ mb: 2, wordBreak: 'break-word' }}>{fileName}</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, p: 2, bgcolor: '#fafafa', borderRadius: 1, mb: 2 }}>
            <Box><Typography variant="caption" color="text.secondary" fontWeight={600}>Scan Date</Typography><Typography variant="body2">{scanDate}</Typography></Box>
            <Box sx={{ textAlign: 'right' }}><Paper variant="outlined" sx={{ p: 1.5, display: 'inline-block' }}><Typography variant="body2" fontWeight={600}>{pages} Pages</Typography><Typography variant="body2" fontWeight={600}>{words.toLocaleString()} Words</Typography><Typography variant="body2" fontWeight={600}>{chars.toLocaleString()} Characters</Typography></Paper></Box>
            <Box><Typography variant="caption" color="text.secondary" fontWeight={600}>File Type</Typography><Typography variant="body2">{(result.file_type || 'txt').toUpperCase()}</Typography></Box>
            <Box><Typography variant="caption" color="text.secondary" fontWeight={600}>Detection Engine</Typography><Typography variant="body2">{result.provider || 'groq'} · {chunksAnalysed} section{chunksAnalysed > 1 ? 's' : ''} analysed</Typography></Box>
          </Box>
        </Box>
      </Paper>

      {/* AI WRITING OVERVIEW */}
      <Paper elevation={2} sx={{ overflow: 'hidden', mb: 3 }}>
        <Box sx={{ bgcolor: COLOURS.headerBg, color: COLOURS.headerText, px: 3, py: 1 }}><Typography variant="subtitle2" fontWeight={600}>AI Writing Overview</Typography></Box>
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 4, flexWrap: 'wrap' }}>
            <Box>
              <AiPercentageCircle percentage={aiPct} />
              <Typography variant="h5" fontWeight={800} sx={{ mt: 1, textAlign: 'center' }}>{aiPct}% detected as AI</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', display: 'block', mt: 0.5, maxWidth: 200 }}>The combined amount of likely AI-generated text.</Typography>
            </Box>
            <Box sx={{ flex: 1, minWidth: 280 }}><CautionBanner aiPct={aiPct} /><DetectionGroups sentences={sentences} /></Box>
          </Box>
          {result.explanation && (
            <Box sx={{ mt: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1, borderLeft: `3px solid ${COLOURS.aiBorder}` }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}><InfoOutlinedIcon fontSize="small" color="primary" /><Typography variant="subtitle2" fontWeight={600}>Analysis Summary</Typography></Box>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8 }}>{result.explanation}</Typography>
            </Box>
          )}
          <Disclaimer />
        </Box>
      </Paper>

      {/* AI WRITING SUBMISSION */}
      <Paper elevation={2} sx={{ overflow: 'hidden', mb: 3 }}>
        <Box sx={{ bgcolor: COLOURS.headerBg, color: COLOURS.headerText, px: 3, py: 1 }}><Typography variant="subtitle2" fontWeight={600}>AI Writing Submission · {aiSentenceCount} of {sentences.length} sentences flagged</Typography></Box>
        <Box sx={{ p: 3 }}><HighlightedDocument sentences={sentences} extractedText={text} /></Box>
      </Paper>

      <FAQSection />
      <Box sx={{ textAlign: 'center', mt: 3, py: 2 }}><Typography variant="caption" color="text.secondary">SignSimple AI Detection Report · Generated {scanDate} · signsimple.co.uk</Typography></Box>
    </Box>
  );
}
