import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'auth', label: 'Authentication' },
  { id: 'ask', label: 'Ask Agent' },
  { id: 'mcp', label: 'MCP Tools' },
  { id: 'notes', label: 'Clinical Notes' },
  { id: 'handover', label: 'Shift Handover' },
  { id: 'partner', label: 'API Keys' },
  { id: 'errors', label: 'Error Handling' },
  { id: 'limits', label: 'Rate Limits' },
];

export default function APIDocs() {
  const [activeSection, setActiveSection] = useState('overview');

  return (
    <main className="main-content">
      <div className="container">
        <h2 style={{ marginBottom: 'var(--space-xs)' }}>API Documentation</h2>
        <p style={{ color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xl)' }}>
          Integrate Care AI into your care management application.
        </p>

        <div className="api-docs">
          {/* Sidebar */}
          <nav className="api-sidebar">
            {SECTIONS.map(s => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className={activeSection === s.id ? 'active' : ''}
                onClick={() => setActiveSection(s.id)}
              >
                {s.label}
              </a>
            ))}
          </nav>

          {/* Content */}
          <div>
            {/* Overview */}
            <section id="overview" className="endpoint-card">
              <h3>Overview</h3>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Care AI provides a REST API for integrating medical knowledge and clinical note 
                generation into your application. All responses include live NHS data, processed 
                by a local LLM that never sends data outside the UK.
              </p>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <strong>Base URL:</strong>
                <div className="code-block">https://api.yourdomain.co.uk/api/v1</div>
              </div>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <strong>Content Type:</strong> <code>application/json</code>
              </div>
            </section>

            {/* Authentication */}
            <section id="auth" className="endpoint-card">
              <h3>Authentication</h3>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Two authentication methods are supported:
              </p>
              <ul style={{ margin: 'var(--space-md) 0', paddingLeft: 'var(--space-lg)', lineHeight: 1.8 }}>
                <li><strong>JWT Bearer Token</strong> — For end-user authentication (login/register)</li>
                <li><strong>API Key</strong> — For partner integrations (machine-to-machine)</li>
              </ul>

              <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)' }}>JWT Authentication</h4>
              <div className="code-block">{`# Register a new user
POST /api/v1/auth/register
{
  "email": "carer@example.co.uk",
  "password": "securePassword123",
  "full_name": "Jane Smith"
}

# Login
POST /api/v1/auth/login
{
  "email": "carer@example.co.uk",
  "password": "securePassword123"
}

# Response
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer"
}`}</div>

              <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)' }}>API Key Authentication</h4>
              <div className="code-block">{`# Include your API key in the header
curl -H "X-API-Key: cai_live_abc123..." \\
     https://api.yourdomain.co.uk/api/v1/agent/ask`}</div>
            </section>

            {/* Ask Agent */}
            <section id="ask" className="endpoint-card">
              <h3>Ask the Medical Agent</h3>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Ask a medical question. The agent fetches live data from NHS.uk, processes it with 
                a local LLM, and returns an answer with source citations.
              </p>

              <div style={{ marginTop: 'var(--space-lg)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/agent/ask</span>
              </div>

              <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)' }}>Request</h4>
              <div className="code-block">{`{
  "question": "What are the side effects of Amlodipine?",
  "strategy": "auto",
  "include_sources": true
}`}</div>

              <h4 style={{ marginTop: 'var(--space-md)', marginBottom: 'var(--space-sm)' }}>Response</h4>
              <div className="code-block">{`{
  "answer": "Common side effects of Amlodipine include...",
  "sources": [
    {
      "source": "NHS Medicines",
      "name": "Amlodipine",
      "url": "https://www.nhs.uk/medicines/amlodipine/",
      "type": "live"
    }
  ],
  "confidence": "high",
  "model_used": "llama3.2:3b",
  "processing_time_ms": 2340.5,
  "tools_used": ["search_nhs"],
  "data_freshness": "live",
  "disclaimer": "This information is based on NHS..."
}`}</div>

              <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 'var(--space-md)' }}>
                <strong>strategy</strong> options: <code>auto</code> (recommended), <code>medicine</code>, <code>condition</code>, <code>search</code>
              </p>
            </section>

            {/* MCP Tools */}
            <section id="mcp" className="endpoint-card">
              <h3>MCP Tools (Direct Data Access)</h3>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Call MCP tools directly to get raw NHS data without AI processing. 
                Useful for building custom UIs or data pipelines.
              </p>

              <div style={{ marginTop: 'var(--space-lg)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/agent/mcp/call</span>
              </div>

              <div className="code-block">{`{
  "tool_name": "get_medicine_info",
  "arguments": {
    "medicine_name": "paracetamol"
  }
}`}</div>

              <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)' }}>Available Tools</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 'var(--space-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--nhs-pale-grey)' }}>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)', fontWeight: 600, fontSize: '0.9rem' }}>Tool</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)', fontWeight: 600, fontSize: '0.9rem' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['get_medicine_info', 'Live medicine details from NHS.uk (dosage, side effects, interactions)'],
                    ['get_condition_info', 'Live condition details from NHS.uk (symptoms, causes, treatment)'],
                    ['search_nhs', 'Search NHS.uk for any medical topic'],
                    ['get_bnf_info', 'Search British National Formulary prescribing data'],
                  ].map(([name, desc]) => (
                    <tr key={name} style={{ borderBottom: '1px solid var(--nhs-pale-grey)' }}>
                      <td style={{ padding: 'var(--space-sm)', fontFamily: 'monospace', fontSize: '0.85rem' }}>{name}</td>
                      <td style={{ padding: 'var(--space-sm)', color: 'var(--nhs-dark-grey)', fontSize: '0.9rem' }}>{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            {/* Clinical Notes */}
            <section id="notes" className="endpoint-card">
              <h3>Clinical Notes</h3>

              <div className="alert alert-success" style={{ marginTop: 'var(--space-md)' }}>
                <strong>🔒 Zero Data Retention (ZDR)</strong> — All audio and video files are 
                processed in memory and securely destroyed immediately after transcription. 
                Only the text transcript and AI-generated clinical note are stored. 
                Every response includes <code>"media_destroyed": true</code> as confirmation.
                Your client app should also delete local recordings after receiving the response.
              </div>

              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Upload voice, video, or text — get structured clinical notes with extracted 
                actions, concerns, vitals, and more. No media is ever permanently stored.
              </p>

              <div style={{ marginTop: 'var(--space-lg)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/notes/voice</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Upload audio → transcribe → generate clinical note</p>
              </div>

              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/notes/video</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Upload video → extract audio → transcribe → generate clinical note</p>
              </div>

              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/notes/text</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Submit text → generate clinical note</p>
              </div>

              <h4 style={{ marginTop: 'var(--space-lg)', marginBottom: 'var(--space-sm)' }}>Voice/Video Upload (multipart form)</h4>
              <div className="code-block">{`curl -X POST /api/v1/notes/voice \\
  -H "Authorization: Bearer TOKEN" \\
  -F "file=@recording.mp3" \\
  -F "client_name=Mrs Johnson" \\
  -F "note_type=full"`}</div>

              <h4 style={{ marginTop: 'var(--space-md)', marginBottom: 'var(--space-sm)' }}>Response (structured clinical note)</h4>
              <div className="code-block">{`{
  "id": "uuid",
  "input_type": "audio",
  "transcript": "Visited Mrs Johnson at 2pm...",
  "clinical_note": {
    "summary": "Routine visit. Client reported knee pain...",
    "actions": [
      {
        "action": "Administer paracetamol 500mg",
        "priority": "routine",
        "time": "8pm",
        "medication": "Paracetamol 500mg"
      }
    ],
    "concerns": ["Client reported feeling lonely"],
    "vitals_mentioned": {
      "blood_pressure": "140/90",
      "pain_level": "6/10"
    },
    "mood_and_behaviour": "Low mood, withdrawn",
    "food_and_fluid": "Ate half portion at lunch"
  },
  "media_destroyed": true,
  "duration_seconds": 45.2,
  "created_at": "2026-02-10T14:30:00Z"
}`}</div>
              <div className="alert alert-info" style={{ marginTop: 'var(--space-md)' }}>
                <strong>Partner responsibility:</strong> Once your app receives the response with 
                <code> "media_destroyed": true</code>, your client application should delete the 
                local recording from the device. Include a <code>server_deleted: true</code> flag 
                in your own app's state to confirm the full deletion chain.
              </div>
            </section>

            {/* Handover */}
            <section id="handover" className="endpoint-card">
              <h3>Shift Handover</h3>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/notes/handover?hours=12</span>
              </div>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                Generates a comprehensive shift handover note from all clinical notes 
                recorded in the past N hours. Includes outstanding actions, urgent concerns, 
                and medication records.
              </p>
            </section>

            {/* Partner API Keys */}
            <section id="partner" className="endpoint-card">
              <h3>Partner API Keys</h3>
              <div style={{ marginTop: 'var(--space-lg)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/partner/register</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Register as a partner</p>
              </div>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-post">POST</span>
                <span className="endpoint-path">/api/v1/partner/keys</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Create a new API key</p>
              </div>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-get">GET</span>
                <span className="endpoint-path">/api/v1/partner/keys</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>List your API keys</p>
              </div>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-delete">DELETE</span>
                <span className="endpoint-path">/api/v1/partner/keys/:id</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>Revoke an API key</p>
              </div>
              <div style={{ marginTop: 'var(--space-md)' }}>
                <span className="endpoint-method method-get">GET</span>
                <span className="endpoint-path">/api/v1/partner/usage</span>
                <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 4 }}>View usage and quota</p>
              </div>
            </section>

            {/* Errors */}
            <section id="errors" className="endpoint-card">
              <h3>Error Handling</h3>
              <p style={{ color: 'var(--nhs-dark-grey)', lineHeight: 1.7, marginTop: 'var(--space-md)' }}>
                All errors return a consistent JSON format:
              </p>
              <div className="code-block">{`{
  "detail": "Human-readable error message"
}`}</div>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 'var(--space-md)' }}>
                <tbody>
                  {[
                    ['400', 'Bad request — check your parameters'],
                    ['401', 'Unauthorized — invalid or expired token/key'],
                    ['404', 'Resource not found'],
                    ['413', 'File too large'],
                    ['422', 'Validation error (e.g., bad file format, empty transcript)'],
                    ['429', 'Rate limit exceeded — slow down'],
                    ['503', 'AI engine temporarily unavailable'],
                  ].map(([code, desc]) => (
                    <tr key={code} style={{ borderBottom: '1px solid var(--nhs-pale-grey)' }}>
                      <td style={{ padding: 'var(--space-sm)', fontWeight: 600, width: 60 }}>{code}</td>
                      <td style={{ padding: 'var(--space-sm)', color: 'var(--nhs-dark-grey)' }}>{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            {/* Rate Limits */}
            <section id="limits" className="endpoint-card">
              <h3>Rate Limits</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 'var(--space-md)' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--nhs-pale-grey)' }}>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)' }}>Tier</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)' }}>Rate</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)' }}>Monthly Quota</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-sm)' }}>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['Starter', '30 req/min', '10,000', '£80/mo'],
                    ['Professional', '100 req/min', '50,000', '£200/mo'],
                    ['Enterprise', '500 req/min', '500,000', 'Custom'],
                  ].map(([tier, rate, quota, price]) => (
                    <tr key={tier} style={{ borderBottom: '1px solid var(--nhs-pale-grey)' }}>
                      <td style={{ padding: 'var(--space-sm)', fontWeight: 500 }}>{tier}</td>
                      <td style={{ padding: 'var(--space-sm)', color: 'var(--nhs-dark-grey)' }}>{rate}</td>
                      <td style={{ padding: 'var(--space-sm)', color: 'var(--nhs-dark-grey)' }}>{quota}</td>
                      <td style={{ padding: 'var(--space-sm)', fontWeight: 500 }}>{price}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p style={{ fontSize: '0.85rem', color: 'var(--nhs-mid-grey)', marginTop: 'var(--space-md)' }}>
                When rate limited, the API returns <code>429 Too Many Requests</code> with a <code>Retry-After</code> header.
              </p>
            </section>

            {/* CTA */}
            <div style={{ textAlign: 'center', padding: 'var(--space-xxl) 0' }}>
              <h3 style={{ marginBottom: 'var(--space-md)' }}>Ready to integrate?</h3>
              <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
                <Link to="/partner" className="btn btn-primary">Get API keys</Link>
                <Link to="/register" className="btn btn-outline">Create an account</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
