import React, { useState } from 'react';
import { askQuestion } from '../services/api';
import { Send, ExternalLink, AlertTriangle } from 'lucide-react';

export default function AskAgent() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setError('');
    setLoading(true);

    try {
      const result = await askQuestion(question);
      const entry = { question, ...result };
      setAnswer(entry);
      setHistory(prev => [entry, ...prev]);
      setQuestion('');
    } catch (err) {
      setError(err.message || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const confidenceColour = (c) => {
    if (c === 'high') return 'badge-high';
    if (c === 'medium') return 'badge-medium';
    return 'badge-low';
  };

  return (
    <main className="main-content">
      <div className="ask-container">
        <h2 style={{ marginBottom: 'var(--space-sm)' }}>Ask the Care AI Agent</h2>
        <p style={{ color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xl)' }}>
          Ask any medical question. Answers are grounded in live NHS data.
        </p>

        {/* Input */}
        <form onSubmit={handleSubmit}>
          <div className="ask-input-wrapper">
            <input
              type="text"
              className="ask-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What are the side effects of Amlodipine?"
              disabled={loading}
              autoFocus
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
              {loading ? <div className="spinner" /> : <Send size={18} />}
            </button>
          </div>
        </form>

        {/* Quick suggestions */}
        {!answer && history.length === 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
            {[
              'What are the side effects of Amlodipine?',
              'How should I manage a client with type 2 diabetes?',
              'What is the recommended dosage for Paracetamol?',
              'Signs and symptoms of a UTI in elderly patients',
            ].map(q => (
              <button
                key={q}
                className="btn btn-outline btn-sm"
                onClick={() => { setQuestion(q); }}
                style={{ fontSize: '0.8rem' }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {error && <div className="alert alert-danger" style={{ marginTop: 'var(--space-md)' }}>{error}</div>}

        {/* Loading state */}
        {loading && (
          <div className="answer-card" style={{ borderLeftColor: 'var(--nhs-light-blue)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
              <div className="spinner-lg" />
              <div>
                <p style={{ fontWeight: 600 }}>Fetching live NHS data...</p>
                <p style={{ color: 'var(--nhs-mid-grey)', fontSize: '0.85rem' }}>
                  Searching NHS.uk and generating your answer
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Current answer */}
        {answer && !loading && (
          <div className="answer-card">
            <p style={{ fontWeight: 600, color: 'var(--nhs-blue)', marginBottom: 'var(--space-md)', fontSize: '0.9rem' }}>
              Q: {answer.question}
            </p>

            <div className="answer-text">{answer.answer}</div>

            {/* Sources */}
            {answer.sources && answer.sources.length > 0 && (
              <div style={{ marginTop: 'var(--space-md)' }}>
                <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--nhs-mid-grey)', marginBottom: 'var(--space-xs)' }}>
                  Sources:
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)' }}>
                  {answer.sources.map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener" className="source-pill">
                      {s.source}: {s.name} <ExternalLink size={12} />
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Meta */}
            <div className="answer-meta">
              <span className={`badge ${confidenceColour(answer.confidence)}`}>
                {answer.confidence} confidence
              </span>
              <span>
                {answer.data_freshness === 'live' ? '🟢 Live data' : '📦 Cached'}
              </span>
              <span>{Math.round(answer.processing_time_ms)}ms</span>
              <span>{answer.model_used}</span>
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="alert alert-warning" style={{ marginTop: 'var(--space-xl)' }}>
          <div style={{ display: 'flex', alignItems: 'start', gap: 'var(--space-sm)' }}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <p style={{ margin: 0, fontSize: '0.85rem' }}>
              This information is based on NHS sources and should not replace professional medical advice. 
              Always consult a qualified healthcare professional for clinical decisions.
            </p>
          </div>
        </div>

        {/* History */}
        {history.length > 1 && (
          <div style={{ marginTop: 'var(--space-xxl)' }}>
            <h3 style={{ marginBottom: 'var(--space-md)' }}>Previous Questions</h3>
            {history.slice(1).map((h, i) => (
              <div key={i} className="card" style={{ marginBottom: 'var(--space-md)', cursor: 'pointer' }} onClick={() => setAnswer(h)}>
                <p style={{ fontWeight: 600, color: 'var(--nhs-blue)', fontSize: '0.9rem', marginBottom: 4 }}>
                  {h.question}
                </p>
                <p style={{ color: 'var(--nhs-dark-grey)', fontSize: '0.9rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {h.answer}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
