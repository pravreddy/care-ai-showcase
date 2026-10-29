import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { trialAsk, trialStatus } from '../services/api';
import { Send, ExternalLink, AlertTriangle, Sparkles, Lock } from 'lucide-react';

export default function TryAI() {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [history, setHistory] = useState([]);
    const [remaining, setRemaining] = useState(5);
    const [limitReached, setLimitReached] = useState(false);

    // Check remaining queries on mount
    useEffect(() => {
        trialStatus()
            .then(data => {
                setRemaining(data.queries_remaining);
                if (data.queries_remaining <= 0) setLimitReached(true);
            })
            .catch(() => {}); // Fail silently
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!question.trim() || loading || limitReached) return;

        setError('');
        setLoading(true);

        try {
            const result = await trialAsk(question);
            const entry = { question, ...result };
            setAnswer(entry);
            setHistory(prev => [entry, ...prev]);
            setRemaining(result.queries_remaining);
            setQuestion('');
            if (result.queries_remaining <= 0) setLimitReached(true);
        } catch (err) {
            if (err.limitReached) {
                setLimitReached(true);
                setRemaining(0);
            } else {
                setError(err.message || 'Failed to get answer');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestion = (q) => {
        if (!limitReached) setQuestion(q);
    };

    const confidenceColour = (c) => {
        if (c === 'high') return 'badge-high';
        if (c === 'medium') return 'badge-medium';
        return 'badge-low';
    };

    const suggestions = [
        'What are the side effects of Amlodipine?',
        'How should I manage a client with type 2 diabetes?',
        'What is the recommended dosage for Paracetamol?',
        'Signs and symptoms of a UTI in elderly patients',
    ];

    return (
        <main className="main-content">
            <div className="ask-container">
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'var(--nhs-pale-grey)', borderRadius: '20px', padding: '6px 16px', fontSize: '0.85rem', color: 'var(--nhs-blue)', marginBottom: 'var(--space-md)' }}>
                        <Sparkles size={14} />
                        No sign-up required — try it now
                    </div>
                    <h2 style={{ marginBottom: 'var(--space-sm)' }}>Test the Care AI Agent</h2>
                    <p style={{ color: 'var(--nhs-mid-grey)', maxWidth: '500px', margin: '0 auto' }}>
                        Ask any medical question. The AI fetches live data from NHS.uk and gives you a sourced answer.
                        You have <strong>{remaining}</strong> free {remaining === 1 ? 'query' : 'queries'} remaining.
                    </p>
                </div>

                {/* Remaining counter */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginBottom: 'var(--space-lg)' }}>
                    {[...Array(5)].map((_, i) => (
                        <div
                            key={i}
                            style={{
                                width: '40px',
                                height: '6px',
                                borderRadius: '3px',
                                background: i < (5 - remaining) ? 'var(--nhs-mid-grey)' : 'var(--nhs-blue)',
                                opacity: i < (5 - remaining) ? 0.3 : 1,
                                transition: 'all 0.3s ease',
                            }}
                        />
                    ))}
                </div>

                {/* Limit reached banner */}
                {limitReached && (
                    <div style={{
                        background: 'linear-gradient(135deg, var(--nhs-blue), var(--nhs-dark-blue))',
                        color: 'white',
                        borderRadius: '12px',
                        padding: 'var(--space-xl)',
                        textAlign: 'center',
                        marginBottom: 'var(--space-xl)',
                    }}>
                        <Lock size={32} style={{ marginBottom: 'var(--space-sm)', opacity: 0.9 }} />
                        <h3 style={{ color: 'white', marginBottom: 'var(--space-sm)' }}>
                            You've used all 5 free queries
                        </h3>
                        <p style={{ opacity: 0.9, marginBottom: 'var(--space-lg)', maxWidth: '400px', margin: '0 auto var(--space-lg)' }}>
                            Sign up for a free 3-month trial to get unlimited AI queries, voice notes, and clinical documentation.
                        </p>
                        <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-md)' }}>
                            <Link to="/register" className="btn btn-lg" style={{ background: 'white', color: 'var(--nhs-blue)' }}>
                                Start free trial
                            </Link>
                            <Link to="/login" className="btn btn-lg" style={{ border: '1px solid rgba(255,255,255,0.4)', color: 'white' }}>
                                Sign in
                            </Link>
                        </div>
                    </div>
                )}

                {/* Input */}
                {!limitReached && (
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
                )}

                {/* Quick suggestions */}
                {!answer && history.length === 0 && !limitReached && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
                        {suggestions.map(q => (
                            <button
                                key={q}
                                className="btn btn-outline btn-sm"
                                onClick={() => handleSuggestion(q)}
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

                        {/* CTA after answer */}
                        {remaining <= 2 && remaining > 0 && (
                            <div style={{
                                marginTop: 'var(--space-lg)',
                                padding: 'var(--space-md)',
                                background: 'var(--nhs-pale-grey)',
                                borderRadius: '8px',
                                textAlign: 'center',
                                fontSize: '0.9rem',
                            }}>
                <span style={{ color: 'var(--nhs-dark-grey)' }}>
                  {remaining} {remaining === 1 ? 'query' : 'queries'} left —
                </span>
                                <Link to="/register" style={{ fontWeight: 600 }}>
                                    Sign up for unlimited access
                                </Link>
                            </div>
                        )}
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
