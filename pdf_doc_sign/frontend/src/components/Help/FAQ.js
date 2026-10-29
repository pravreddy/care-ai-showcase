import React from 'react';
import {
  Typography, Accordion, AccordionSummary, AccordionDetails, Box,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpLayout from './HelpLayout';
import SEO from '../Common/SEO';

const FAQ_SECTIONS = [
  {
    title: 'Getting Started',
    items: [
      {
        q: 'Is SignSimple really free?',
        a: 'Yes — the Free plan gives you 10 documents per month at no cost, with no credit card required. You can upgrade to Starter (£2.50/month for 100 documents) or Professional (£10/month for 1,000 documents) at any time.',
      },
      {
        q: 'Do signers need an account?',
        a: 'No. Signers receive a secure email link and can sign directly in their browser — no account, no download, no app required.',
      },
      {
        q: 'What file types can I upload?',
        a: 'Currently, SignSimple supports PDF files up to 10 MB. Documents are automatically compressed on upload to optimise storage and loading speed.',
      },
    ],
  },
  {
    title: 'Legal & Security',
    items: [
      {
        q: 'Are electronic signatures legally valid?',
        a: 'Yes. Electronic signatures are legally valid in the UK under the Electronic Communications Act 2000, in the EU under eIDAS Regulation, and in most countries worldwide. SignSimple provides an audit trail certificate with timestamps, IP addresses, and a SHA-256 document hash for evidential support.',
      },
      {
        q: 'How are my documents secured?',
        a: 'Documents are stored on encrypted NVMe storage in a UK-based data centre (Vultr London). Each signing link is a unique 48-character cryptographic token that expires after 90 days. We use HTTPS everywhere and follow OWASP security best practices.',
      },
      {
        q: 'What is the audit trail certificate?',
        a: 'When all signers complete, SignSimple generates a PDF certificate containing: the document\'s SHA-256 hash (fingerprint), who signed, when they signed, their IP addresses, and a full activity log. This provides tamper-evident proof of the signing process.',
      },
      {
        q: 'Can I verify that a signed document hasn\'t been tampered with?',
        a: 'Yes. The audit trail certificate includes the SHA-256 hash of the original document. You can compute the hash of the PDF and compare it to the certificate — if they match, the document is unaltered.',
      },
    ],
  },
  {
    title: 'Features',
    items: [
      {
        q: 'Can I place signatures at specific positions on the PDF?',
        a: 'Yes. Use the "Place Fields" editor to drag signature, date, name, and initials fields onto any position on any page. Signers will see green highlights showing exactly where to sign.',
      },
      {
        q: 'Can I send a document to multiple people?',
        a: 'Yes, in two ways. "Send for Signing" lets you add multiple signers who all sign the same document. "Bulk Send" creates independent copies — each recipient gets their own document to sign separately (useful for NDAs, offer letters, etc.).',
      },
      {
        q: 'What are templates?',
        a: 'Templates let you save a document with its pre-placed signature fields for reuse. Next time, click "Use Template" and a new document is created instantly with all fields already positioned. Great for contracts you send repeatedly.',
      },
      {
        q: 'Can I send reminders to signers?',
        a: 'Yes. On the document detail page, click "Remind All" to nudge all pending signers, or click the bell icon next to a specific signer to remind just that person.',
      },
      {
        q: 'Do I get notified when someone signs?',
        a: 'Yes. You receive an email notification each time a signer completes, showing the signing progress. When all signers finish, everyone (sender and all signers) receives a completion email.',
      },
    ],
  },
  {
    title: 'Industry Use Cases',
    items: [
      {
        q: 'Can I use SignSimple for real estate documents?',
        a: 'Absolutely. SignSimple is ideal for tenancy agreements, property contracts, offer acceptances, and landlord-tenant forms. Upload your document, place signature fields for all parties, and send — no printing, scanning, or posting required.',
      },
      {
        q: 'Is SignSimple suitable for HR and recruitment?',
        a: 'Yes. Use Bulk Send to send offer letters, contracts, or onboarding forms to multiple new hires at once. Each person gets their own independent copy to sign. Templates are especially useful for documents you send repeatedly.',
      },
      {
        q: 'Can legal firms use SignSimple?',
        a: 'Yes. SignSimple provides legally binding electronic signatures with a full audit trail (SHA-256 hash, timestamps, IP addresses). This is suitable for client engagement letters, consent forms, settlement agreements, and more. For documents requiring qualified electronic signatures or wet-ink signatures (e.g., deeds, wills), consult your legal advisor.',
      },
      {
        q: 'Can I use it for food delivery or catering businesses?',
        a: 'Yes — SignSimple includes a built-in daily sales tracking and invoicing module designed for food delivery and catering operations, with support for line items, packing charges, courier charges, and GST invoicing.',
      },
    ],
  },
  {
    title: 'Account & Billing',
    items: [
      {
        q: 'How do I upgrade my plan?',
        a: 'Go to Subscription in the sidebar and choose a plan. We accept payments via Stripe (credit/debit cards) and TrueLayer (bank transfers).',
      },
      {
        q: 'What happens if I exceed my monthly document limit?',
        a: 'You can purchase extra document bundles (100 documents for £1). Your existing documents remain accessible — you just can\'t upload new ones until you upgrade or buy more.',
      },
      {
        q: 'Can I cancel at any time?',
        a: 'Yes. You can downgrade to the Free plan at any time. Your documents remain accessible, but you\'ll be limited to 10 uploads per month.',
      },
    ],
  },
  {
    title: 'Technical',
    items: [
      {
        q: 'What browsers are supported?',
        a: 'SignSimple works in all modern browsers: Chrome, Firefox, Safari, Edge, and Brave. Both desktop and mobile browsers are supported — signers can sign on their phone without downloading any app.',
      },
      {
        q: 'Is there an API for developers?',
        a: 'API access is available on the Professional plan. Contact us at support@signsimple.co.uk for API documentation and integration guidance.',
      },
      {
        q: 'What happens to expired documents?',
        a: 'Signing links expire after 90 days. The document remains in your account, but pending signers can no longer access their links. You can resend the document to create new signing links.',
      },
      {
        q: 'Can I download a signed document after it expires?',
        a: 'Yes. Signed documents and their audit trail certificates are available for download indefinitely — expiry only affects pending signing links, not completed documents.',
      },
    ],
  },
];

export default function FAQ() {
  return (
    <HelpLayout>
      <SEO
        title="FAQ – E-Signature Questions Answered"
        description="Common questions about SignSimple e-signatures: legal validity in the UK, security, pricing, features, templates, and more."
        path="/help/faq"
        keywords="e-signature FAQ, electronic signature UK legal, signsimple pricing, is e-signature legally binding"
      />

      <Typography variant="h4" fontWeight={700} gutterBottom>
        Frequently Asked Questions
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Everything you need to know about SignSimple.
      </Typography>

      {FAQ_SECTIONS.map((section) => (
        <Box key={section.title} sx={{ mb: 4 }}>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            {section.title}
          </Typography>
          {section.items.map((item, index) => (
            <Accordion key={index} variant="outlined" sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography fontWeight={500}>{item.q}</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary">
                  {item.a}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      ))}

      <Box sx={{ mt: 4, p: 3, bgcolor: '#e3f2fd', borderRadius: 2, textAlign: 'center' }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Still have questions?
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Email us at <strong>support@signsimple.co.uk</strong> — we're happy to help.
        </Typography>
      </Box>
    </HelpLayout>
  );
}
