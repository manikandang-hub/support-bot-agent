import { useState } from 'react';
import { confirmTicket } from '../services/api';
import TicketEscalation from './TicketEscalation';

export default function TicketModal({ title, description, conversationId, pluginId, email, onClose, onCreated }) {
  const [ticketTitle, setTicketTitle] = useState(title);
  const [ticketDescription, setTicketDescription] = useState(description);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ticketData, setTicketData] = useState(null);

  const handleSubmit = async () => {
    if (!ticketTitle.trim() || !ticketDescription.trim()) {
      setError('Title and description are required.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await confirmTicket(conversationId, pluginId, email, ticketTitle, ticketDescription);
      setTicketData(response.data);
      if (onCreated) onCreated(response.data);
    } catch (err) {
      setError('Failed to create ticket. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget && !loading && !ticketData) onClose(); }}>
      <div className="modal">

        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-left">
            <span className="modal-icon">🎟️</span>
            <div>
              <h3 className="modal-title">{ticketData ? 'Ticket Submitted' : 'Create Support Ticket'}</h3>
              <p className="modal-subtitle">{ticketData ? 'Your ticket has been created successfully.' : 'Review and edit before submitting to our support team.'}</p>
            </div>
          </div>
          {!loading && (
            <button className="modal-close" onClick={onClose} title="Close">✕</button>
          )}
        </div>

        {ticketData ? (
          <div className="modal-body">
            <TicketEscalation
              ticketId={ticketData.ticket_id}
              ticketUrl={ticketData.ticket_url}
              assignedAgent={email}
            />
          </div>
        ) : (
          <>
            <div className="modal-body">
              {error && <div className="modal-error">{error}</div>}

              {/* Customer info strip */}
              <div className="modal-meta">
                <span className="modal-meta-item">
                  <span className="modal-meta-label">Customer</span>
                  <span className="modal-meta-value">{email}</span>
                </span>
                <span className="modal-meta-divider" />
                <span className="modal-meta-item">
                  <span className="modal-meta-label">Plugin</span>
                  <span className="modal-meta-value">{pluginId}</span>
                </span>
              </div>

              {/* Title */}
              <div className="modal-field">
                <label className="modal-label">
                  Title <span className="modal-required">*</span>
                </label>
                <input
                  type="text"
                  value={ticketTitle}
                  onChange={(e) => setTicketTitle(e.target.value)}
                  disabled={loading}
                  className="modal-input"
                  placeholder="Brief summary of the issue"
                />
              </div>

              {/* Description */}
              <div className="modal-field">
                <label className="modal-label">
                  Description <span className="modal-required">*</span>
                </label>
                <textarea
                  value={ticketDescription}
                  onChange={(e) => setTicketDescription(e.target.value)}
                  disabled={loading}
                  rows={10}
                  className="modal-textarea"
                  placeholder="Describe the issue in detail..."
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-btn-cancel" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button className="modal-btn-submit" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <span className="modal-btn-loading">
                    <span className="modal-spinner" /> Submitting...
                  </span>
                ) : (
                  'Submit Ticket'
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
