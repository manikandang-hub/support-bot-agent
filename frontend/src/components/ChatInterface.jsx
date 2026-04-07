import { useState, useRef, useEffect, useCallback } from 'react';
import { sendQuery } from '../services/api';
import ChatMessage from './ChatMessage';
import wtLogo from '../assets/wt-logo-icon.svg';


export default function ChatInterface({ plugins, selectedPlugin, onPluginChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const liveRegionRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  return (
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
        <div className="topbar-controls">
          <label htmlFor="plugin-select" className="sr-only" style={{ position: 'absolute', left: '-9999px' }}>
            Select plugin
          </label>
          <select
            id="plugin-select"
            className="topbar-select"
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
      </header>

      {/* Email bar */}
      <div className="email-bar" role="complementary" aria-label="Contact information">
        <span className="email-bar-label" id="email-label">Your email</span>
        <input
          type="email"
          className="email-bar-input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          aria-labelledby="email-label"
          autoComplete="email"
        />
      </div>

      {/* Messages */}
      <div
        className="messages-area"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        aria-relevant="additions"
      >
        {messages.length === 0 ? (
          <div className="empty-state" aria-label="Welcome screen">
            <div className="empty-state-icon" aria-hidden="true">💬</div>
            <h2>How can I help you?</h2>
            <p>
              {selectedPlugin
                ? `Ask anything about ${selectedPluginName}`
                : 'Select a plugin above, then ask your question'}
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} isUser={msg.isUser} email={email} />
          ))
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

      {/* Input area */}
      <div className="input-area" role="form" aria-label="Send a message">
        {error && (
          <div className="input-error" role="alert" aria-live="assertive">
            <span aria-hidden="true">⚠</span> {error}
          </div>
        )}

        <div className="input-row">
          <textarea
            id="chat-input"
            ref={textareaRef}
            className="input-textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
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
        <p className="input-hint" aria-hidden="true">Enter to send · Shift+Enter for new line</p>
      </div>
    </main>
  );
}
