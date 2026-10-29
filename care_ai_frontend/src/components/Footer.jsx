import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div>
          <h4>Care AI</h4>
          <p style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
            AI-powered clinical intelligence for UK care workers. 
            Live NHS data. Local AI processing. GDPR compliant.
          </p>
        </div>
        <div>
          <h4>Product</h4>
          <Link to="/docs">API Documentation</Link>
          <Link to="/register">Start Free Trial</Link>
          <Link to="/login">Sign In</Link>
        </div>
        <div>
          <h4>Resources</h4>
          <a href="https://www.nhs.uk" target="_blank" rel="noopener">NHS.uk</a>
          <a href="https://www.cqc.org.uk" target="_blank" rel="noopener">CQC</a>
          <a href="https://www.nice.org.uk" target="_blank" rel="noopener">NICE Guidelines</a>
        </div>
        <div>
          <h4>Legal</h4>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">Data Processing Agreement</a>
        </div>
      </div>
      <div className="footer-bottom">
        <p>© {new Date().getFullYear()} Care AI Ltd. All rights reserved. Registered in England & Wales.</p>
        <p style={{ marginTop: '4px', fontSize: '0.8rem', opacity: 0.7 }}>
          Care AI does not provide medical advice. Always consult a qualified healthcare professional.
        </p>
      </div>
    </footer>
  );
}
