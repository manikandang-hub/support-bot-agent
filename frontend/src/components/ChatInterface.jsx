import { useState, useRef, useEffect, useCallback } from 'react';
import { sendQuery } from '../services/api';
import ChatMessage from './ChatMessage';
import wtLogo from '../assets/wt-logo-icon.svg';

const prefersReducedMotion = () =>
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export default function ChatInterface({ plugins, selectedPlugin, onPluginChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesAreaRef = useRef(null);
  const textareaRef = useRef(null);
  const liveRegionRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
    });
  }, [messages, loading]);

  // Reset conversation when plugin changes
  useEffect(() => {
    setConversationId(null);
    setMessages([]);
  }, [selectedPlugin]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }, [input]);

  // Track scroll position to show/hide scroll-to-bottom button
  const handleScroll = useCallback(() => {
    const el = messagesAreaRef.current;
    if (!el) return;
    const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distFromBottom > 120);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
    });
  };

  const announce = (text) => {
    if (liveRegionRef.current) liveRegionRef.current.textContent = text;
  };

  const submit = useCallback(async (query) => {
    if (!query.trim() || !email.trim() || !selectedPlugin) {
      setError('Please fill in your email and select a plugin before sending.');
      return;
    }

    setError('');
    setLoading(true);
    setMessages(prev => [...prev, { text: query, isUser: true }]);
    setInput('');

    try {
      const response = await sendQuery(selectedPlugin, query, email, conversationId);
      const botMessage = {
        ...response.data,
        isUser: false,
        plugin_id: selectedPlugin,
        email,
      };
      if (response.data.conversation_id) setConversationId(response.data.conversation_id);
      setMessages(prev => [...prev, botMessage]);
      announce('New response received from SupportBot.');
    } catch (err) {
      setError(err.message || 'Failed to get response. Please try again.');
      setMessages(prev => prev.slice(0, -1));
      announce('Error: failed to get response.');
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }, [email, selectedPlugin, conversationId]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  };

  const selectedPluginName = plugins.find(p => p.id === selectedPlugin)?.name || '';
  const charCount = input.length;

  return (
    <>
      <a href="#chat-messages" className="skip-link">Skip to messages</a>

      <main className="chat-shell" aria-label="SupportBot chat">

        {/* Accessible live region for screen readers */}
        <div
          ref={liveRegionRef}
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
          style={{ position: 'absolute', left: '-9999px', width: '1px', height: '1px', overflow: 'hidden' }}
        />

        {/* Top bar */}
        <header className="chat-topbar" role="banner">
          <div className="chat-brand">
            <div className="chat-brand-icon" aria-hidden="true">
              <img src={wtLogo} alt="" width="36" height="15" style={{ display: 'block' }} />
            </div>
            <div>
              <div className="chat-brand-name">SupportBot</div>
              <div className="chat-brand-tagline">Powered by WebToffee</div>
            </div>
          </div>
          <div className="topbar-controls" />
        </header>

        {/* Info bar: plugin + email */}
        <div className="info-bar" role="complementary" aria-label="Plugin and contact information">
          <div className="info-bar-row">
            <label htmlFor="plugin-select" className="info-bar-label">Plugin</label>
            <select
              id="plugin-select"
              className="info-bar-select"
              value={selectedPlugin}
              onChange={(e) => onPluginChange(e.target.value)}
              aria-label="Select plugin"
            >
              <option value="">Choose plugin…</option>
              {plugins.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="info-bar-divider" aria-hidden="true" />
          <div className="info-bar-row">
            <label htmlFor="email-input" className="info-bar-label">Email</label>
            <input
              id="email-input"
              type="email"
              className="info-bar-input"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(''); }}
              placeholder="you@example.com"
              autoComplete="email"
              aria-required="true"
              aria-describedby={error ? 'chat-error' : undefined}
            />
          </div>
        </div>

        {/* Messages */}
        <div className="messages-wrapper">
          <div
            id="chat-messages"
            ref={messagesAreaRef}
            className="messages-area"
            role="log"
            aria-label="Chat messages"
            aria-live="polite"
            aria-relevant="additions"
            onScroll={handleScroll}
            tabIndex={-1}
          >
            {messages.length === 0 ? (
              <div className="empty-state" aria-label="Welcome screen">
                <div className="empty-state-icon" aria-hidden="true">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <h2>How can I help you?</h2>
                <p>
                  {selectedPlugin
                    ? `Ask anything about ${selectedPluginName}`
                    : 'Select a plugin above, then ask your question'}
                </p>
              </div>
            ) : (
              <ul className="messages-list" aria-label="Message history">
                {messages.map((msg, idx) => (
                  <ChatMessage key={idx} message={msg} isUser={msg.isUser} email={email} />
                ))}
              </ul>
            )}

            {/* Thinking indicator */}
            {loading && (
              <div className="thinking-row" role="status" aria-label="SupportBot is thinking">
                <div className="avatar avatar-bot" aria-hidden="true">
                  <img src={wtLogo} alt="" width="28" height="12" style={{ display: 'block' }} />
                </div>
                <div className="thinking-dots" aria-hidden="true">
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          {/* Scroll-to-bottom button */}
          {showScrollBtn && (
            <button
              className="scroll-to-bottom"
              onClick={scrollToBottom}
              aria-label="Scroll to latest message"
              title="Jump to latest"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          )}
        </div>

        {/* Input area */}
        <div className="input-area" role="form" aria-label="Send a message">
          {error && (
            <div id="chat-error" className="input-error" role="alert" aria-live="assertive">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          <div className="input-row">
            <textarea
              id="chat-input"
              ref={textareaRef}
              className="input-textarea"
              value={input}
              onChange={(e) => { setInput(e.target.value); setError(''); }}
              onKeyDown={handleKeyDown}
              placeholder="Ask your question… (Enter to send, Shift+Enter for new line)"
              rows={1}
              disabled={loading}
              aria-label="Message input"
              aria-multiline="true"
              aria-disabled={loading}
            />
            <button
              className="send-btn"
              onClick={() => submit(input)}
              disabled={loading || !input.trim() || !selectedPlugin}
              aria-label="Send message"
              title="Send (Enter)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <div className="input-footer">
            <p className="input-hint" aria-hidden="true">Enter to send · Shift+Enter for new line</p>
            {charCount > 200 && (
              <span className={`char-count${charCount > 900 ? ' char-count--warn' : ''}`} aria-live="polite" aria-label={`${charCount} characters`}>
                {charCount}
              </span>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
