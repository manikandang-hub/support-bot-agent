import { useState, useRef, useEffect } from 'react';
import { sendQuery } from '../services/api';
import ChatMessage from './ChatMessage';

export default function ChatInterface({ plugins, selectedPlugin, onPluginChange }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState(null); // Track conversation for follow-ups
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset conversation when plugin changes
  useEffect(() => {
    setConversationId(null);
    setMessages([]);
  }, [selectedPlugin]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!input.trim() || !email.trim() || !selectedPlugin) {
      setError('Please fill in all fields and select a plugin');
      return;
    }

    setError('');
    setLoading(true);

    // Add user message to chat
    const userMessage = {
      text: input,
      isUser: true,
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      // Pass conversation_id for follow-up questions
      const response = await sendQuery(selectedPlugin, input, email, conversationId);
      const botMessage = {
        ...response.data,
        isUser: false,
      };

      // Store conversation_id from response for subsequent queries
      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError(err.message || 'Failed to get response. Please try again.');
      setMessages(prev => prev.slice(0, -1)); // Remove user message on error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h1>🤖 SupportBot</h1>
        <p>Ask questions about WordPress plugins and get instant solutions</p>
      </div>

      <div className="chat-container">
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>Welcome to SupportBot</h2>
              <p>Select a plugin and ask your question below</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} isUser={msg.isUser} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label>Select Plugin</label>
            <select value={selectedPlugin} onChange={(e) => onPluginChange(e.target.value)}>
              <option value="">Choose a plugin...</option>
              {plugins.map(plugin => (
                <option key={plugin.id} value={plugin.id}>
                  {plugin.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Your Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Your Question</label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask your question about the plugin..."
              rows="4"
              disabled={loading}
            />
          </div>

          <button type="submit" disabled={loading || !selectedPlugin} className="submit-btn">
            {loading ? 'Thinking...' : 'Send Question'}
          </button>
        </form>
      </div>
    </div>
  );
}
