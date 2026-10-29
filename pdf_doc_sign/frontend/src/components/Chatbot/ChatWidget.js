/**
 * ChatWidget.js — Floating AI chatbot for lead capture.
 * 
 * Drop this component into any page:
 *   <ChatWidget />
 * 
 * It renders a floating button bottom-right. On click, opens a chat panel.
 * Conversations are powered by Groq AI via the /api/chatbot/ endpoints.
 * When the visitor shares their name + email, a coupon is auto-generated.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { chatbotService } from '../../services/api';

const BRAND_COLOR = '#1565c0';

const styles = {
  // Floating button
  fab: {
    position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
    width: 60, height: 60, borderRadius: '50%',
    background: BRAND_COLOR, border: 'none', cursor: 'pointer',
    boxShadow: '0 4px 16px rgba(21,101,192,0.4)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  fabHover: {
    transform: 'scale(1.08)',
    boxShadow: '0 6px 24px rgba(21,101,192,0.5)',
  },
  // Chat panel
  panel: {
    position: 'fixed', bottom: 96, right: 24, zIndex: 9998,
    width: 370, maxHeight: 520,
    borderRadius: 16, overflow: 'hidden',
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
    display: 'flex', flexDirection: 'column',
    background: '#fff',
    fontFamily: '"Inter", "Roboto", "Helvetica", sans-serif',
  },
  // Header
  header: {
    padding: '16px 20px', background: BRAND_COLOR, color: '#fff',
    display: 'flex', alignItems: 'center', gap: 12,
  },
  avatar: {
    width: 40, height: 40, borderRadius: '50%', background: '#fff',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 16, fontWeight: 600, color: BRAND_COLOR,
  },
  headerText: { flex: 1 },
  headerName: { fontSize: 15, fontWeight: 600 },
  headerStatus: { fontSize: 12, opacity: 0.85 },
  closeBtn: {
    background: 'none', border: 'none', color: '#fff',
    fontSize: 22, cursor: 'pointer', padding: 4, lineHeight: 1,
  },
  // Messages area
  messages: {
    flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
    minHeight: 280, maxHeight: 360, background: '#f5f7fa',
  },
  // Message bubbles
  msgRow: (isUser) => ({
    display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: 10,
  }),
  bubble: (isUser) => ({
    maxWidth: '80%', padding: '10px 14px',
    borderRadius: isUser ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
    background: isUser ? BRAND_COLOR : '#fff',
    color: isUser ? '#fff' : '#333',
    fontSize: 14, lineHeight: 1.5,
    boxShadow: isUser ? 'none' : '0 1px 3px rgba(0,0,0,0.08)',
  }),
  // Typing indicator
  typing: {
    display: 'flex', gap: 4, padding: '10px 14px',
    background: '#fff', borderRadius: 14, width: 'fit-content',
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  dot: (delay) => ({
    width: 8, height: 8, borderRadius: '50%', background: '#bbb',
    animation: `chatDotPulse 1.2s ease-in-out ${delay}s infinite`,
  }),
  // Input area
  inputArea: {
    display: 'flex', gap: 8, padding: '12px 16px',
    borderTop: '1px solid #eee', background: '#fff',
  },
  input: {
    flex: 1, border: '1px solid #ddd', borderRadius: 24,
    padding: '10px 16px', fontSize: 14, outline: 'none',
    transition: 'border-color 0.2s',
    fontFamily: 'inherit',
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: '50%',
    background: BRAND_COLOR, border: 'none', cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  sendBtnDisabled: {
    background: '#ccc', cursor: 'not-allowed',
  },
  // Coupon card
  couponCard: {
    margin: '8px 0', padding: '12px 16px',
    background: '#e8f5e9', borderRadius: 12,
    border: '1px dashed #4caf50',
  },
  couponCode: {
    fontSize: 18, fontWeight: 700, color: '#2e7d32',
    letterSpacing: 1, margin: '6px 0',
  },
  couponText: {
    fontSize: 12, color: '#558b2f', margin: '2px 0',
  },
};

// Keyframes for typing dots (inject once)
const injectKeyframes = () => {
  if (document.getElementById('chat-dot-keyframes')) return;
  const style = document.createElement('style');
  style.id = 'chat-dot-keyframes';
  style.textContent = `
    @keyframes chatDotPulse {
      0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
      40% { opacity: 1; transform: scale(1); }
    }
  `;
  document.head.appendChild(style);
};

// SVG icons
const ChatIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" />
  </svg>
);

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 6L6 18" /><path d="M6 6l12 12" />
  </svg>
);

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [coupon, setCoupon] = useState(null);
  const [fabHover, setFabHover] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { injectKeyframes(); }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  // Focus input when panel opens
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open]);

  // Start chat session
  const startChat = useCallback(async () => {
    if (sessionId) return; // Already started
    try {
      const res = await chatbotService.start(window.location.href, document.referrer);
      setSessionId(res.session_id);
      setMessages([{ role: 'assistant', content: res.message.content }]);
    } catch (err) {
      setMessages([{
        role: 'assistant',
        content: "Hi! Welcome to SignSimple. How can I help you today?",
      }]);
    }
  }, [sessionId]);

  // Open panel
  const handleOpen = () => {
    setOpen(true);
    if (!sessionId) startChat();
  };

  // Send message
  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setSending(true);

    try {
      const res = await chatbotService.sendMessage(sessionId, text);
      setMessages(prev => [...prev, { role: 'assistant', content: res.message.content }]);
      if (res.coupon) {
        setCoupon(res.coupon);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I'm having a moment. Could you try again?",
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Don't show on dashboard pages (user is already logged in)
  if (window.location.pathname.startsWith('/dashboard') ||
      window.location.pathname.startsWith('/documents') ||
      window.location.pathname.startsWith('/profile') ||
      window.location.pathname.startsWith('/admin')) {
    return null;
  }

  return (
    <>
      {/* Chat Panel */}
      {open && (
        <div style={styles.panel}>
          {/* Header */}
          <div style={styles.header}>
            <div style={styles.avatar}>SS</div>
            <div style={styles.headerText}>
              <div style={styles.headerName}>SignSimple</div>
              <div style={styles.headerStatus}>Online — replies instantly</div>
            </div>
            <button style={styles.closeBtn} onClick={() => setOpen(false)} aria-label="Close chat">
              <CloseIcon />
            </button>
          </div>

          {/* Messages */}
          <div style={styles.messages}>
            {messages.map((msg, i) => (
              <div key={i} style={styles.msgRow(msg.role === 'user')}>
                <div style={styles.bubble(msg.role === 'user')}>
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Coupon card */}
            {coupon && (
              <div style={styles.couponCard}>
                <div style={styles.couponText}>Your personal discount code:</div>
                <div style={styles.couponCode}>{coupon.code}</div>
                <div style={styles.couponText}>
                  {coupon.plan} plan for {coupon.duration_days <= 90 ? '3 months' : coupon.duration_days <= 180 ? '6 months' : '1 year'} — just £{coupon.price_gbp}
                </div>
                <div style={styles.couponText}>Valid for 7 days. Use at signup!</div>
              </div>
            )}

            {/* Typing indicator */}
            {sending && (
              <div style={styles.msgRow(false)}>
                <div style={styles.typing}>
                  <div style={styles.dot(0)} />
                  <div style={styles.dot(0.2)} />
                  <div style={styles.dot(0.4)} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={styles.inputArea}>
            <input
              ref={inputRef}
              style={styles.input}
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
            />
            <button
              style={{ ...styles.sendBtn, ...(sending || !input.trim() ? styles.sendBtnDisabled : {}) }}
              onClick={handleSend}
              disabled={sending || !input.trim()}
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      )}

      {/* Floating Action Button */}
      <button
        style={{ ...styles.fab, ...(fabHover ? styles.fabHover : {}) }}
        onClick={open ? () => setOpen(false) : handleOpen}
        onMouseEnter={() => setFabHover(true)}
        onMouseLeave={() => setFabHover(false)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? <CloseIcon /> : <ChatIcon />}
      </button>
    </>
  );
}
