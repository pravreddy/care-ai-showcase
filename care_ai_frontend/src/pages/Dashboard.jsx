import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getUser, listNotes, getCacheStats } from '../services/api';
import { Brain, Mic, FileText, ArrowRight, Activity } from 'lucide-react';

export default function Dashboard() {
  const user = getUser();
  const [recentNotes, setRecentNotes] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    listNotes(5, 0).then(d => setRecentNotes(d.notes)).catch(() => {});
    getCacheStats().then(setStats).catch(() => {});
  }, []);

  return (
    <main className="main-content">
      <div className="container">
        <div className="disclaimer-bar" style={{ borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-xl)' }}>
          ⚕️ Care AI provides information based on NHS sources. Always consult a qualified healthcare professional for clinical decisions.
        </div>

        <h1 style={{ marginBottom: 'var(--space-xs)' }}>Welcome back, {user?.full_name || 'there'}</h1>
        <p style={{ color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xl)' }}>
          What would you like to do?
        </p>

        {/* Quick actions */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xxl)' }}>
          <Link to="/ask" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'start', gap: 'var(--space-md)', transition: 'box-shadow 0.15s' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#e3f2fd', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Brain size={24} color="var(--nhs-blue)" />
            </div>
            <div>
              <h4 style={{ marginBottom: 4 }}>Ask the AI Agent</h4>
              <p style={{ color: 'var(--nhs-dark-grey)', fontSize: '0.9rem', margin: 0 }}>
                Ask a medical question with live NHS data
              </p>
            </div>
          </Link>

          <Link to="/notes" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'start', gap: 'var(--space-md)' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#e8f5e9', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Mic size={24} color="var(--nhs-green)" />
            </div>
            <div>
              <h4 style={{ marginBottom: 4 }}>Record a Note</h4>
              <p style={{ color: 'var(--nhs-dark-grey)', fontSize: '0.9rem', margin: 0 }}>
                Voice, video, or text — AI creates clinical notes
              </p>
            </div>
          </Link>

          <Link to="/notes" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'start', gap: 'var(--space-md)' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#fff3e0', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <FileText size={24} color="var(--nhs-orange)" />
            </div>
            <div>
              <h4 style={{ marginBottom: 4 }}>Shift Handover</h4>
              <p style={{ color: 'var(--nhs-dark-grey)', fontSize: '0.9rem', margin: 0 }}>
                Generate handover from today's notes
              </p>
            </div>
          </Link>
        </div>

        {/* Recent notes */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 'var(--space-xl)' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
              <h3>Recent Notes</h3>
              <Link to="/notes" style={{ fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                View all <ArrowRight size={14} />
              </Link>
            </div>
            {recentNotes.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: 'var(--space-xxl)', color: 'var(--nhs-mid-grey)' }}>
                <Mic size={32} style={{ opacity: 0.4, marginBottom: 'var(--space-md)' }} />
                <p>No notes yet. Record your first voice note to get started.</p>
                <Link to="/notes" className="btn btn-primary btn-sm" style={{ marginTop: 'var(--space-md)' }}>
                  Record a note
                </Link>
              </div>
            ) : (
              <div className="notes-grid">
                {recentNotes.map(note => (
                  <div key={note.id} className="note-card">
                    <div className="note-card-header">
                      <span className="note-card-type">
                        {note.input_type === 'audio' && <Mic size={14} />}
                        {note.input_type}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--nhs-mid-grey)' }}>
                        {new Date(note.created_at).toLocaleString('en-GB')}
                      </span>
                    </div>
                    <p className="note-card-summary">
                      {note.clinical_note?.summary || note.transcript?.slice(0, 150) || 'No summary'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar stats */}
          <div>
            <h3 style={{ marginBottom: 'var(--space-md)' }}>System Status</h3>
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-md)' }}>
                <Activity size={16} color="var(--nhs-green)" />
                <span style={{ fontWeight: 600, color: 'var(--nhs-green)' }}>All systems operational</span>
              </div>
              {stats && (
                <div style={{ fontSize: '0.85rem', color: 'var(--nhs-dark-grey)' }}>
                  <p>Cache hit rate: {stats.hit_rate_percent}%</p>
                  <p>Cached entries: {stats.cached_entries}</p>
                  <p>Redis: {stats.redis_connected ? '✓ Connected' : '✗ Disconnected'}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
