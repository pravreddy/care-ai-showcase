import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import {
  Box, Container, Typography, Button, Grid, Paper, Chip, Stack, Divider,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Avatar,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import DescriptionIcon from '@mui/icons-material/Description';
import SecurityIcon from '@mui/icons-material/Security';
import SpeedIcon from '@mui/icons-material/Speed';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import DrawIcon from '@mui/icons-material/Draw';
import SendIcon from '@mui/icons-material/Send';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import FileCopyIcon from '@mui/icons-material/FileCopy';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import StarIcon from '@mui/icons-material/Star';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SchoolIcon from '@mui/icons-material/School';

// ─── Plan data ───
const PLANS = [
  {
    name: 'Free',
    price: '£0',
    period: '/month',
    highlight: false,
    features: [
      '10 document signatures/month',
      '3 AI detector scans/month',
      '3 plagiarism checks/month',
      'Draw, type, or upload signatures',
      'Email notifications',
      'Basic audit trail',
      'No credit card required',
    ],
    cta: 'Start Free',
  },
  {
    name: 'Starter',
    price: '£2.50',
    period: '/month',
    highlight: true,
    features: [
      '100 document signatures/month',
      '100 AI detector scans/month',
      '100 plagiarism checks/month',
      'All signature types',
      'Reusable templates',
      'Full audit trail certificate',
      'Priority email support',
    ],
    cta: 'Get Started',
  },
  {
    name: 'Professional',
    price: '£10',
    period: '/month',
    highlight: false,
    features: [
      '1,000 document signatures/month',
      '500 AI detector scans/month',
      '500 plagiarism checks/month',
      'Bulk send (up to 100)',
      'Custom branding',
      'Sales & invoicing module',
      'API access',
    ],
    cta: 'Go Professional',
  },
];

// ─── Feature comparison ───
const COMPARE_FEATURES = [
  { name: 'Documents per month', free: '10', starter: '100', pro: '1,000' },
  { name: 'AI detector scans/month', free: '3', starter: '100', pro: '500' },
  { name: 'Plagiarism checks/month', free: '3', starter: '100', pro: '500' },
  { name: 'Signature types (draw/type/upload)', free: true, starter: true, pro: true },
  { name: 'Email notifications', free: true, starter: true, pro: true },
  { name: 'Reusable templates', free: false, starter: true, pro: true },
  { name: 'Full audit trail certificate', free: false, starter: true, pro: true },
  { name: 'Bulk send', free: false, starter: false, pro: true },
  { name: 'Custom branding', free: false, starter: false, pro: true },
  { name: 'Sales & invoicing', free: false, starter: false, pro: true },
  { name: 'API access', free: false, starter: false, pro: true },
];

// ─── Testimonials ───
const TESTIMONIALS = [
  {
    name: 'Sarah Thompson',
    role: 'Freelance Consultant, London',
    text: 'SignSimple replaced our printing and scanning completely. Clients sign contracts on their phone in under a minute.',
    initials: 'ST', color: '#1565c0',
  },
  {
    name: 'James Okafor',
    role: 'Student, University of Birmingham',
    text: 'The AI detector caught AI-generated content in my assignment before I submitted it. The plagiarism checker is brilliant too.',
    initials: 'JO', color: '#7b1fa2',
  },
  {
    name: 'Raj Patel',
    role: 'Restaurant Owner, Leicester',
    text: 'The daily sales tracking and invoice generation saves us hours every month. No more Excel spreadsheets.',
    initials: 'RP', color: '#2e7d32',
  },
];

// ─── Services ───
const SERVICES = [
  {
    icon: <DrawIcon sx={{ fontSize: 40 }} />,
    color: '#1565c0',
    bg: '#e3f2fd',
    title: 'PDF Document Signing',
    subtitle: 'Sign & store documents securely in the UK',
    desc: 'Legally binding e-signatures with full audit trail. GDPR compliant, UK data storage.',
    cta: 'Sign a PDF Free',
    path: '/free-electronic-signature',
    badge: 'Free to try',
    points: ['Legally binding under UK law', 'UK-based document storage', 'GDPR compliant', 'No login to try'],
  },
  {
    icon: <SmartToyIcon sx={{ fontSize: 40 }} />,
    color: '#7b1fa2',
    bg: '#f3e5f5',
    title: 'AI Content Detector',
    subtitle: 'Detect ChatGPT & AI-written content',
    desc: 'Sentence-level AI detection. See exactly which parts of your text were written by AI.',
    cta: 'Check for AI',
    path: '/ai-checker',
    badge: 'Free first check',
    points: ['Detects ChatGPT, Claude & more', 'Sentence-level highlighting', 'Works on PDFs & text', 'Used by students & educators'],
  },
  {
    icon: <ContentCopyIcon sx={{ fontSize: 40 }} />,
    color: '#e65100',
    bg: '#fff3e0',
    title: 'Plagiarism Checker',
    subtitle: 'Detect copied content before submission',
    desc: 'Check your essay or article for plagiarism with sentence-level colour coding.',
    cta: 'Check for Plagiarism',
    path: '/ai-checker',
    badge: 'Free first check',
    points: ['Colour-coded sentence analysis', 'Identifies copied passages', 'Style-shift detection', 'Perfect for students'],
  },
];

export default function Landing() {
  const navigate = useNavigate();

  const Check = () => <CheckCircleIcon sx={{ fontSize: 18, color: 'success.main' }} />;
  const Cross = () => <CloseIcon sx={{ fontSize: 18, color: 'text.disabled' }} />;

  return (
    <Box>
      {/* ─── SEO ─── */}
      <Helmet>
        <title>SignSimple | Free PDF Signing, AI Detector & Plagiarism Checker | UK</title>
        <meta name="description" content="Sign PDFs online free with UK data storage. Detect AI-generated content and check for plagiarism. GDPR compliant. Free to start — no credit card needed." />
        <meta name="keywords" content="free pdf signing uk, ai detector, plagiarism checker, sign documents online, GDPR compliant document signing, detect ChatGPT, AI content detector uk" />
        <meta property="og:title" content="SignSimple — PDF Signing, AI Detector & Plagiarism Checker" />
        <meta property="og:description" content="Sign PDFs, detect AI content, and check plagiarism. All in one platform. Free to start." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://signsimple.co.uk" />
        <link rel="canonical" href="https://signsimple.co.uk" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "SignSimple",
          "applicationCategory": "BusinessApplication",
          "offers": { "@type": "Offer", "price": "0", "priceCurrency": "GBP" },
          "operatingSystem": "Web",
          "description": "Free PDF document signing with UK data storage, AI content detector, and plagiarism checker."
        })}</script>
      </Helmet>

      {/* ─── Sticky Nav ─── */}
      <Box sx={{
        px: 3, py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        position: 'sticky', top: 0, zIndex: 1100, bgcolor: 'white', borderBottom: '1px solid #e0e0e0',
      }}>
        <Typography variant="h6" fontWeight={700} color="primary" sx={{ cursor: 'pointer' }}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          SignSimple
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ display: { xs: 'none', md: 'flex' } }}>
          <Button size="small" onClick={() => navigate('/free-electronic-signature')}
            sx={{ textTransform: 'none', fontWeight: 600, color: '#2e7d32' }}>Free Sign Tool</Button>
          <Button size="small" onClick={() => navigate('/ai-checker')}
            sx={{ textTransform: 'none', fontWeight: 600, color: '#7b1fa2' }}>AI & Plagiarism</Button>
          <Button size="small" onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
            sx={{ textTransform: 'none' }}>Pricing</Button>
          <Button size="small" onClick={() => navigate('/help')}
            sx={{ textTransform: 'none' }}>Help</Button>
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button variant="text" onClick={() => navigate('/login')} sx={{ textTransform: 'none' }}>Sign In</Button>
          <Button variant="contained" onClick={() => navigate('/register')} sx={{ textTransform: 'none' }}>Start Free</Button>
        </Stack>
      </Box>

      {/* ─── Hero ─── */}
      <Box sx={{ bgcolor: 'primary.main', color: 'white', py: { xs: 8, md: 12 }, textAlign: 'center' }}>
        <Container maxWidth="md">
          <Chip
            label="Free to start — no credit card needed"
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600, mb: 3, fontSize: '0.95rem', py: 2.5 }}
          />
          <Typography component="h1" sx={{ fontSize: { xs: '2rem', md: '3rem' }, fontWeight: 800, mb: 2, lineHeight: 1.2 }}>
            Sign PDFs · Detect AI · Check Plagiarism{' '}
            <Box component="span" sx={{ color: '#ffcc02' }}>— All Free</Box>
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, fontWeight: 400, maxWidth: 650, mx: 'auto' }}>
            Three powerful tools in one platform. Legally binding e-signatures with UK data storage,
            AI content detection, and plagiarism checking — free to start.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button variant="contained" size="large"
              onClick={() => navigate('/free-electronic-signature')}
              sx={{ bgcolor: '#ffcc02', color: '#333', fontWeight: 700, px: 5, py: 1.5, fontSize: '1.1rem', textTransform: 'none', '&:hover': { bgcolor: '#ffd633' } }}>
              Sign a PDF Free
            </Button>
            <Button variant="outlined" size="large"
              onClick={() => navigate('/ai-checker')}
              sx={{ borderColor: 'white', color: 'white', textTransform: 'none', fontWeight: 600, px: 4 }}>
              Check AI & Plagiarism Free
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* ─── 3 Services ─── */}
      <Box id="services" sx={{ py: 10, bgcolor: '#f8f9fb' }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            Three Tools in One Platform
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6, maxWidth: 550, mx: 'auto' }}>
            Everything you need — from signing documents to checking AI content and plagiarism.
          </Typography>

          <Grid container spacing={4}>
            {SERVICES.map((s, i) => (
              <Grid item xs={12} md={4} key={i}>
                <Paper elevation={3} sx={{ p: 4, height: '100%', borderRadius: 3, borderTop: `4px solid ${s.color}`, display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ width: 72, height: 72, borderRadius: 3, bgcolor: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: s.color, mb: 2 }}>
                    {s.icon}
                  </Box>
                  <Chip label={s.badge} size="small" sx={{ bgcolor: s.bg, color: s.color, fontWeight: 700, mb: 1.5, alignSelf: 'flex-start' }} />
                  <Typography variant="h6" fontWeight={700} gutterBottom>{s.title}</Typography>
                  <Typography variant="body2" color="text.secondary" fontWeight={600} sx={{ mb: 1 }}>{s.subtitle}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{s.desc}</Typography>
                  <Stack spacing={0.8} sx={{ mb: 3, flex: 1 }}>
                    {s.points.map((p, j) => (
                      <Box key={j} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CheckCircleIcon sx={{ fontSize: 16, color: s.color }} />
                        <Typography variant="body2">{p}</Typography>
                      </Box>
                    ))}
                  </Stack>
                  <Button fullWidth variant="contained"
                    onClick={() => navigate(s.path)}
                    sx={{ bgcolor: s.color, textTransform: 'none', fontWeight: 700, py: 1.2, '&:hover': { bgcolor: s.color, opacity: 0.9 } }}>
                    {s.cta}
                  </Button>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      <Divider />

      {/* ─── Student Banner ─── */}
      <Box sx={{ py: 8, bgcolor: '#f3e5f5', textAlign: 'center' }}>
        <Container maxWidth="md">
          <SchoolIcon sx={{ fontSize: 56, color: '#7b1fa2', mb: 2 }} />
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Built for Students & Educators
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 550, mx: 'auto' }}>
            Check your essay for AI-generated content AND plagiarism before submitting.
            Free first check — no account needed.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button variant="contained" size="large"
              onClick={() => navigate('/ai-checker')}
              sx={{ bgcolor: '#7b1fa2', textTransform: 'none', fontWeight: 700, px: 5, py: 1.5, '&:hover': { bgcolor: '#6a1b9a' } }}>
              Check My Essay Free
            </Button>
            <Button variant="outlined" size="large"
              onClick={() => navigate('/register')}
              sx={{ borderColor: '#7b1fa2', color: '#7b1fa2', textTransform: 'none', fontWeight: 600 }}>
              Create Free Account
            </Button>
          </Stack>
        </Container>
      </Box>

      <Divider />

      {/* ─── How It Works ─── */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          How PDF Signing Works
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6, maxWidth: 500, mx: 'auto' }}>
          Send your first document for signing in under 5 minutes.
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          {[
            { icon: <UploadFileIcon sx={{ fontSize: 48 }} />, step: '1', title: 'Upload Your PDF', desc: 'Drag and drop your document or click to upload. Any PDF up to 10MB.' },
            { icon: <DrawIcon sx={{ fontSize: 48 }} />, step: '2', title: 'Place Signature Fields', desc: 'Drag signature, date, and name fields to where signers need to sign.' },
            { icon: <SendIcon sx={{ fontSize: 48 }} />, step: '3', title: 'Send & Track', desc: 'Add signer emails and send. Track who signed and send reminders.' },
          ].map((s, i) => (
            <Grid item xs={12} sm={4} key={i}>
              <Paper elevation={0} sx={{ p: 4, textAlign: 'center', bgcolor: 'transparent' }}>
                <Box sx={{ width: 80, height: 80, borderRadius: '50%', bgcolor: 'primary.main', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', mx: 'auto', mb: 2 }}>
                  {s.icon}
                </Box>
                <Chip label={`Step ${s.step}`} size="small" color="primary" variant="outlined" sx={{ mb: 1 }} />
                <Typography variant="h6" fontWeight={600} gutterBottom>{s.title}</Typography>
                <Typography variant="body2" color="text.secondary">{s.desc}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Divider />

      {/* ─── Features ─── */}
      <Box id="features" sx={{ py: 10, bgcolor: '#f8f9fb' }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            Everything Included
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6, maxWidth: 600, mx: 'auto' }}>
            From simple signatures to AI detection, plagiarism checking, and sales invoicing — all in one platform.
          </Typography>
          <Grid container spacing={3}>
            {[
              { icon: <DrawIcon />, title: 'Draw, Type, or Upload', desc: 'Three ways to sign: draw with your finger or mouse, type your name, or upload a signature image.', color: '#1565c0' },
              { icon: <SecurityIcon />, title: 'Legally Binding', desc: 'Valid under UK law (Electronic Communications Act 2000), EU (eIDAS), and international frameworks.', color: '#2e7d32' },
              { icon: <VerifiedUserIcon />, title: 'Audit Trail Certificate', desc: 'Every document gets a SHA-256 hash, signer IPs, timestamps, and a downloadable audit certificate PDF.', color: '#7b1fa2' },
              { icon: <SmartToyIcon />, title: 'AI Content Detector', desc: 'Detect ChatGPT, Claude, and other AI-written content with sentence-level highlighting.', color: '#e65100' },
              { icon: <ContentCopyIcon />, title: 'Plagiarism Checker', desc: 'Check essays and articles for copied content. Sentence-level colour coding shows exactly what is flagged.', color: '#c62828' },
              { icon: <CloudDoneIcon />, title: 'UK Data Storage', desc: 'Documents stored on UK-based servers. GDPR compliant. Your data never leaves the UK.', color: '#37474f' },
              { icon: <FileCopyIcon />, title: 'Reusable Templates', desc: 'Save documents as templates with pre-placed fields. Use them again with one click.', color: '#f57c00' },
              { icon: <GroupAddIcon />, title: 'Bulk Send', desc: 'Send the same document to up to 100 people at once. Each gets their own copy to sign.', color: '#00838f' },
              { icon: <ReceiptLongIcon />, title: 'Sales & Invoicing', desc: 'Built-in daily sales tracking and invoice generation for restaurants, caterers, and delivery businesses.', color: '#ad1457' },
            ].map((f, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Paper sx={{ p: 3, height: '100%', transition: '0.2s', '&:hover': { boxShadow: 6 } }}>
                  <Box sx={{ color: f.color, mb: 1.5 }}>{f.icon}</Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>{f.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{f.desc}</Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      <Divider />

      {/* ─── Testimonials ─── */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          Trusted by UK Users
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6 }}>
          From students to businesses to freelancers.
        </Typography>
        <Grid container spacing={4}>
          {TESTIMONIALS.map((t, i) => (
            <Grid item xs={12} md={4} key={i}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Stack direction="row" spacing={0.5} sx={{ mb: 2 }}>
                  {[1, 2, 3, 4, 5].map((s) => <StarIcon key={s} sx={{ fontSize: 18, color: '#ffc107' }} />)}
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, fontStyle: 'italic' }}>
                  "{t.text}"
                </Typography>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Avatar sx={{ bgcolor: t.color, width: 36, height: 36, fontSize: 14 }}>{t.initials}</Avatar>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>{t.name}</Typography>
                    <Typography variant="caption" color="text.secondary">{t.role}</Typography>
                  </Box>
                </Stack>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Divider />

      {/* ─── Pricing ─── */}
      <Box id="pricing" sx={{ py: 10, bgcolor: '#f8f9fb' }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            Simple, Transparent Pricing
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 6 }}>
            All plans include PDF signing, AI detection, and plagiarism checking. No hidden fees.
          </Typography>
          <Grid container spacing={4} justifyContent="center">
            {PLANS.map((plan, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Paper elevation={plan.highlight ? 8 : 2} sx={{
                  p: 4, textAlign: 'center', position: 'relative',
                  border: plan.highlight ? '2px solid' : 'none', borderColor: 'primary.main',
                }}>
                  {plan.highlight && (
                    <Chip label="MOST POPULAR" color="primary" size="small"
                      sx={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', fontWeight: 700 }} />
                  )}
                  <Typography variant="h5" fontWeight={700} sx={{ mt: plan.highlight ? 1 : 0 }}>{plan.name}</Typography>
                  <Box sx={{ my: 2 }}>
                    <Typography component="span" sx={{ fontSize: '2.5rem', fontWeight: 800 }}>{plan.price}</Typography>
                    <Typography component="span" variant="body1" color="text.secondary">{plan.period}</Typography>
                  </Box>
                  <Stack spacing={1} sx={{ mb: 3, textAlign: 'left' }}>
                    {plan.features.map((f, j) => (
                      <Box key={j} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CheckCircleIcon sx={{ fontSize: 18, color: 'success.main' }} />
                        <Typography variant="body2">{f}</Typography>
                      </Box>
                    ))}
                  </Stack>
                  <Button fullWidth variant={plan.highlight ? 'contained' : 'outlined'}
                    onClick={() => navigate('/register')}
                    sx={{ py: 1.2, fontWeight: 600, textTransform: 'none' }}>
                    {plan.cta}
                  </Button>
                </Paper>
              </Grid>
            ))}
          </Grid>
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 4 }}>
            Need more? Add extra documents or AI scans anytime — just £1 per 100.
          </Typography>
        </Container>
      </Box>

      <Divider />

      {/* ─── Compare Plans ─── */}
      <Container maxWidth="md" sx={{ py: 10 }}>
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          Compare Plans
        </Typography>
        <TableContainer component={Paper} elevation={2}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main' }}>
                <TableCell sx={{ color: 'white', fontWeight: 700, width: '40%' }}>Feature</TableCell>
                <TableCell align="center" sx={{ color: 'white', fontWeight: 700 }}>Free</TableCell>
                <TableCell align="center" sx={{ color: 'white', fontWeight: 700 }}>Starter</TableCell>
                <TableCell align="center" sx={{ color: 'white', fontWeight: 700 }}>Professional</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {COMPARE_FEATURES.map((f, i) => (
                <TableRow key={i} sx={{ bgcolor: i % 2 === 0 ? '#fafbfc' : 'white' }}>
                  <TableCell><Typography variant="body2">{f.name}</Typography></TableCell>
                  <TableCell align="center">
                    {typeof f.free === 'boolean' ? (f.free ? <Check /> : <Cross />) : <Typography variant="body2" fontWeight={600}>{f.free}</Typography>}
                  </TableCell>
                  <TableCell align="center">
                    {typeof f.starter === 'boolean' ? (f.starter ? <Check /> : <Cross />) : <Typography variant="body2" fontWeight={600}>{f.starter}</Typography>}
                  </TableCell>
                  <TableCell align="center">
                    {typeof f.pro === 'boolean' ? (f.pro ? <Check /> : <Cross />) : <Typography variant="body2" fontWeight={600}>{f.pro}</Typography>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Container>

      <Divider />

      {/* ─── Industries ─── */}
      <Box sx={{ py: 10, bgcolor: '#f8f9fb' }}>
        <Container maxWidth="lg">
          <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
            Built for Everyone
          </Typography>
          <Grid container spacing={3} sx={{ mt: 2 }}>
            {[
              { icon: <SchoolIcon />, title: 'Students & Educators', desc: 'Check assignments for AI content and plagiarism before submission. Free checks every month.' },
              { icon: <DescriptionIcon />, title: 'Freelancers & Startups', desc: 'Send contracts for signing. 10 free documents every month is enough for most freelancers.' },
              { icon: <PointOfSaleIcon />, title: 'Restaurants & Caterers', desc: 'Track daily food deliveries, log sales, generate monthly invoices — all built in.' },
              { icon: <SecurityIcon />, title: 'Property & Legal', desc: 'Tenancy agreements, NDAs, settlement letters. Full audit trail for legal compliance.' },
            ].map((ind, i) => (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
                  <Box sx={{ color: 'primary.main', mb: 1.5 }}>{ind.icon}</Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>{ind.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{ind.desc}</Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ─── Final CTA ─── */}
      <Box sx={{ py: 8, bgcolor: 'primary.main', color: 'white', textAlign: 'center' }}>
        <Container maxWidth="sm">
          <Typography variant="h4" fontWeight={700} gutterBottom>Ready to get started?</Typography>
          <Typography variant="body1" sx={{ mb: 4, opacity: 0.9 }}>
            Sign documents, detect AI content, and check plagiarism — all free to start.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button variant="contained" size="large" onClick={() => navigate('/register')}
              sx={{ bgcolor: '#ffcc02', color: '#333', fontWeight: 700, textTransform: 'none', px: 5, '&:hover': { bgcolor: '#ffd633' } }}>
              Start Free — No Credit Card
            </Button>
            <Button variant="outlined" size="large" onClick={() => navigate('/ai-checker')}
              sx={{ borderColor: 'white', color: 'white', textTransform: 'none', fontWeight: 600 }}>
              Try AI & Plagiarism Checker
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* ─── Footer ─── */}
      <Box sx={{ py: 5, bgcolor: '#1a1a2e', color: 'white' }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={3}>
              <Typography variant="h6" fontWeight={700} gutterBottom>SignSimple</Typography>
              <Typography variant="body2" sx={{ opacity: 0.7 }}>
                Free PDF signing, AI detector & plagiarism checker. UK data storage. GDPR compliant.
                A product of Avyangah Technologies Limited.
              </Typography>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>Tools</Typography>
              <Stack spacing={0.5}>
                {[
                  { label: 'Free PDF Signing', path: '/free-electronic-signature' },
                  { label: 'AI Detector', path: '/ai-checker' },
                  { label: 'Plagiarism Checker', path: '/ai-checker' },
                ].map((l) => (
                  <Typography key={l.label} variant="body2" sx={{ opacity: 0.7, cursor: 'pointer', '&:hover': { opacity: 1 } }}
                    onClick={() => navigate(l.path)}>{l.label}</Typography>
                ))}
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>Resources</Typography>
              <Stack spacing={0.5}>
                {[
                  { label: 'Help Centre', path: '/help' },
                  { label: 'How to Sign', path: '/help/how-to-sign' },
                  { label: 'FAQ', path: '/help/faq' },
                ].map((l) => (
                  <Typography key={l.label} variant="body2" sx={{ opacity: 0.7, cursor: 'pointer', '&:hover': { opacity: 1 } }}
                    onClick={() => navigate(l.path)}>{l.label}</Typography>
                ))}
              </Stack>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>Pricing</Typography>
              <Stack spacing={0.5}>
                {['Free', 'Starter — £2.50/mo', 'Professional — £10/mo'].map((l) => (
                  <Typography key={l} variant="body2" sx={{ opacity: 0.7, cursor: 'pointer', '&:hover': { opacity: 1 } }}
                    onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}>{l}</Typography>
                ))}
              </Stack>
            </Grid>
            <Grid item xs={6} md={3}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>Legal</Typography>
              <Typography variant="body2" sx={{ opacity: 0.7 }}>
                E-signatures valid under UK law (Electronic Communications Act 2000) and EU (eIDAS).
                UK data storage — GDPR compliant.
              </Typography>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3, borderColor: 'rgba(255,255,255,0.1)' }} />

          <Typography variant="body2" align="center" sx={{ opacity: 0.5 }}>
            © {new Date().getFullYear()} Avyangah Technologies Limited. All rights reserved. UK Company #08235853.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}
