#!/usr/bin/env node
/**
 * seo-prerender.js — Creates per-route index.html files with unique
 * <title>, <meta description>, and <link rel="canonical">.
 *
 * Runs after `react-scripts build`. Replaces react-snap.
 * Each route gets its own directory + index.html so nginx
 * serves the correct meta tags before JS loads.
 */

const fs = require('fs');
const path = require('path');

const BUILD = path.join(__dirname, 'build');
const SITE = 'https://signsimple.co.uk';

// ── Route SEO config ───────────────────────────────────────────────────
const ROUTES = [
  {
    path: '/',
    title: 'SignSimple | Free PDF Signing, AI Detector & Plagiarism Checker | UK',
    description: 'Sign PDFs online free with UK data storage. Detect AI-generated content and check for plagiarism. GDPR compliant. Free to start — no credit card needed.',
  },
  {
    path: '/free-electronic-signature',
    title: 'Free Electronic Signature Tool – Sign PDFs Online | SignSimple',
    description: 'Sign PDF documents online free. Draw, type or upload your signature. No account needed. Supports PDF, DOC, DOCX, JPG and PNG. UK-based, GDPR compliant.',
  },
  {
    path: '/ai-checker',
    title: 'Free AI & Plagiarism Checker – Detect AI Content | SignSimple',
    description: 'Check your work for AI-generated content and plagiarism — free for students and educators. Sentence-level highlighting shows exactly what is flagged.',
  },
  {
    path: '/login',
    title: 'Sign In | SignSimple',
    description: 'Sign in to your SignSimple account to manage documents, send for signing, and track progress.',
  },
  {
    path: '/register',
    title: 'Create Free Account | SignSimple',
    description: 'Sign up free — 10 documents per month, no credit card required. PDF signing, AI detection, and plagiarism checking included.',
  },
  {
    path: '/help',
    title: 'Help Centre – How to Sign, Send & Use Templates | SignSimple',
    description: 'Learn how to sign documents, send for signing, use templates, and more with SignSimple. Step-by-step guides for UK e-signatures.',
  },
  {
    path: '/help/how-to-sign',
    title: 'How to Sign a Document | SignSimple',
    description: 'Step-by-step guide to signing documents with SignSimple. Draw, type or upload your signature — no account needed. Legally binding under UK law.',
  },
  {
    path: '/help/how-to-send',
    title: 'How to Send Documents for Signing | SignSimple',
    description: 'Learn how to upload PDFs, place signature fields, add signers, and send for e-signature with SignSimple. Complete step-by-step guide.',
  },
  {
    path: '/help/how-to-create-signatures',
    title: 'How to Create Your Electronic Signature | SignSimple',
    description: 'Three ways to create your e-signature with SignSimple: draw, type, or upload an image. All legally binding under UK law.',
  },
  {
    path: '/help/how-to-use-fields',
    title: 'How to Use Signature Fields in Documents | SignSimple',
    description: 'Learn how to place signature, date, name, initials and text fields on your PDF documents with SignSimple.',
  },
  {
    path: '/help/how-to-templates',
    title: 'How to Use Document Templates | SignSimple',
    description: 'Save time with reusable PDF templates. Pre-place signature fields once and reuse them for contracts, NDAs, and agreements.',
  },
  {
    path: '/help/sales-invoicing',
    title: 'Sales Tracking & Invoicing Guide | SignSimple',
    description: 'Track daily food deliveries, manage clients, and generate monthly invoices with GST support. Built for restaurants, caterers, and delivery businesses.',
  },
  {
    path: '/help/faq',
    title: 'FAQ – E-Signature Questions Answered | SignSimple',
    description: 'Common questions about SignSimple e-signatures: legal validity in the UK, security, pricing, features, templates, and more.',
  },
];

// ── Read the base index.html ───────────────────────────────────────────
const baseHtml = fs.readFileSync(path.join(BUILD, 'index.html'), 'utf-8');

let created = 0;

for (const route of ROUTES) {
  // Replace <title>
  let html = baseHtml.replace(
    /<title>.*?<\/title>/,
    `<title>${route.title}</title>`
  );

  // Replace <meta name="description">
  html = html.replace(
    /<meta name="description" content=".*?"\s*\/?>/,
    `<meta name="description" content="${route.description}" />`
  );

  // Replace OG tags
  html = html.replace(
    /<meta property="og:title" content=".*?"\s*\/?>/,
    `<meta property="og:title" content="${route.title}" />`
  );
  html = html.replace(
    /<meta property="og:description" content=".*?"\s*\/?>/,
    `<meta property="og:description" content="${route.description}" />`
  );

  // Add canonical link (before </head>)
  const canonical = `<link rel="canonical" href="${SITE}${route.path === '/' ? '' : route.path}" />`;
  if (!html.includes('rel="canonical"')) {
    html = html.replace('</head>', `  ${canonical}\n</head>`);
  }

  // Write to the correct path
  if (route.path === '/') {
    fs.writeFileSync(path.join(BUILD, 'index.html'), html);
  } else {
    const dir = path.join(BUILD, route.path);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, 'index.html'), html);
  }
  created++;
}

console.log(`✅ SEO prerender: ${created} route HTML files created`);
