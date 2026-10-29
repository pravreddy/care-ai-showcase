import React from 'react';
import { Link } from 'react-router-dom';
import { Mic, Brain, Shield, FileText, Zap, Users } from 'lucide-react';

export default function Landing() {
  return (
      <main>
        {/* Hero */}
        <section className="hero">
          <div className="container">
            <h1>Clinical Intelligence for UK Care Workers</h1>
            <p>
              Ask medical questions backed by live NHS data. Record voice notes that
              automatically become structured clinical notes. All processed locally —
              your data never leaves the UK.
            </p>
            <div className="hero-actions">
              <Link to="/register" className="btn btn-primary btn-lg">
                Start 3-month free trial
              </Link>
              <Link to="/try" className="btn btn-ghost btn-lg">
                Try AI without signing up
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="container">
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon"><Brain size={28} /></div>
              <h3>Ask the AI Agent</h3>
              <p>
                Ask any medical question. The AI fetches live data from NHS.uk,
                processes it with a local LLM, and gives you a sourced answer
                with confidence ratings.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"><Mic size={28} /></div>
              <h3>Voice & Video Notes</h3>
              <p>
                Record during your shift. The AI transcribes your voice, extracts
                medication actions, flags concerns, and produces a CQC-ready
                clinical note automatically.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"><FileText size={28} /></div>
              <h3>Shift Handovers</h3>
              <p>
                End-of-shift handover notes generated from all your clinical notes.
                Outstanding actions, urgent concerns, and medication records —
                summarised in seconds.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"><Shield size={28} /></div>
              <h3>Zero Data Retention</h3>
              <p>
                Audio and video recordings are processed in memory and securely
                destroyed immediately. Only the text survives. If our server is
                hacked, there are no recordings to steal. GDPR gold standard.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"><Zap size={28} /></div>
              <h3>Always Live Data</h3>
              <p>
                Unlike chatbots with stale training data, Care AI fetches from
                NHS.uk in real-time using MCP. Medication info is always current.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"><Users size={28} /></div>
              <h3>Partner API</h3>
              <p>
                Integrate Care AI into your existing care management app.
                Simple REST API with API keys, rate limits, and usage tracking.
              </p>
            </div>
          </div>
        </section>

        {/* Try AI CTA */}
        <section style={{ padding: 'var(--space-hero) 0', textAlign: 'center' }}>
          <div className="container">
            <h2 style={{ marginBottom: 'var(--space-md)' }}>See It in Action</h2>
            <p style={{ color: 'var(--nhs-dark-grey)', marginBottom: 'var(--space-xl)', maxWidth: '500px', margin: '0 auto var(--space-xl)' }}>
              Try 5 free queries right now — no sign-up, no email, no credit card.
              Just ask a medical question and see the AI fetch live NHS data.
            </p>
            <Link to="/try" className="btn btn-primary btn-lg">
              Try the AI now — it's free
            </Link>
          </div>
        </section>

        {/* Pricing */}
        <section style={{ background: 'var(--nhs-pale-grey)', padding: 'var(--space-hero) 0' }}>
          <div className="container">
            <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>Simple Pricing</h2>
            <p style={{ textAlign: 'center', color: 'var(--nhs-dark-grey)', marginBottom: 'var(--space-xl)', maxWidth: '500px', margin: '0 auto var(--space-xl)' }}>
              Start with a 3-month free trial. No credit card required.
            </p>

            <div className="pricing-grid">
              {/* Free Trial */}
              <div className="pricing-card">
                <h3>Free Trial</h3>
                <div className="price">£0 <span>/ 3 months</span></div>
                <ul className="pricing-features">
                  <li>Unlimited AI questions</li>
                  <li>Voice & video notes</li>
                  <li>Clinical note generation</li>
                  <li>Shift handovers</li>
                  <li>Single user</li>
                </ul>
                <Link to="/register" className="btn btn-outline" style={{ width: '100%', justifyContent: 'center' }}>
                  Start free trial
                </Link>
              </div>

              {/* Pro */}
              <div className="pricing-card featured">
                <h3>Pro</h3>
                <div className="price">£10 <span>/ month</span></div>
                <ul className="pricing-features">
                  <li>Everything in Free</li>
                  <li>Priority AI processing</li>
                  <li>Extended note history</li>
                  <li>Email support</li>
                  <li>Single user</li>
                </ul>
                <Link to="/register" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                  Start free trial
                </Link>
              </div>

              {/* Agency */}
              <div className="pricing-card">
                <h3>Agency</h3>
                <div className="price">£80 <span>/ month</span></div>
                <ul className="pricing-features">
                  <li>Everything in Pro</li>
                  <li>Up to 10 users</li>
                  <li>Team handover notes</li>
                  <li>API access (10k calls/mo)</li>
                  <li>Priority support</li>
                </ul>
                <Link to="/register" className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center' }}>
                  Contact sales
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section style={{ background: 'var(--nhs-dark-blue)', color: 'white', padding: 'var(--space-hero) 0', textAlign: 'center' }}>
          <div className="container">
            <h2 style={{ color: 'white', marginBottom: 'var(--space-md)' }}>
              Ready to transform your care documentation?
            </h2>
            <p style={{ opacity: 0.9, marginBottom: 'var(--space-xl)', maxWidth: '500px', margin: '0 auto var(--space-xl)' }}>
              Join care workers across the UK who are saving hours on documentation and
              delivering better care with AI.
            </p>
            <Link to="/register" className="btn btn-primary btn-lg">
              Start your free trial today
            </Link>
          </div>
        </section>
      </main>
  );
}
