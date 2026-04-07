import { useState, useEffect, useRef } from 'react';
import { confirmTicket } from '../services/api';
import TicketEscalation from './TicketEscalation';

export default function TicketModal({ title, description, conversationId, pluginId, email, onClose, onCreated }) {
  const [ticketTitle, setTicketTitle] = useState(title);
  const [ticketDescription, setTicketDescription] = useState(description);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ticketData, setTicketData] = useState(null);
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  // Capture trigger element and set up focus trap
  useEffect(() => {
    previousFocusRef.current = document.activeElement;

    const modal = modalRef.current;
    if (!modal) return;

    const focusableSelectors =
      'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])';

    // Focus first input on open
    const focusable = modal.querySelectorAll(focusableSelectors);
    if (focusable.length) focusable[0].focus();

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !loading && !ticketData) {
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const all = Array.from(modal.querySelectorAll(focusableSelectors));
      if (!all.length) return;
      const first = all[0];
      const last = all[all.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
    } catch {
      setError('Failed to create ticket. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div
      className="modal-overlay"
      onClick={(e) => { if (e.target === e.currentTarget && !loading && !ticketData) onClose(); }}
    >
      <div
        ref={modalRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ticket-modal-title"
        aria-describedby="ticket-modal-subtitle"
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-left">
            <span className="modal-icon" aria-hidden="true">🎟️</span>
            <div>
              <h3 id="ticket-modal-title" className="modal-title">
                {ticketData ? 'Ticket Submitted' : 'Create Support Ticket'}
              </h3>
              <p id="ticket-modal-subtitle" className="modal-subtitle">
                {ticketData
                  ? 'Your ticket has been created successfully.'
                  : 'Review and edit before submitting to our support team.'}
              </p>
            </div>
          </div>
          {!loading && (
            <button
              className="modal-close"
              onClick={onClose}
              aria-label="Close ticket modal"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
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
              {error && (
                <div id="modal-error" className="modal-error" role="alert">
                  {error}
                </div>
              )}

              {/* Customer info strip */}
              <div className="modal-meta">
                <span className="modal-meta-item">
                  <span className="modal-meta-label">Customer</span>
                  <span className="modal-meta-value">{email}</span>
                </span>
                <span className="modal-meta-divider" aria-hidden="true" />
                <span className="modal-meta-item">
                  <span className="modal-meta-label">Plugin</span>
                  <span className="modal-meta-value">{pluginId}</span>
                </span>
              </div>

              {/* Title */}
              <div className="modal-field">
                <label htmlFor="ticket-title" className="modal-label">
                  Title <span className="modal-required" aria-hidden="true">*</span>
                  <span className="sr-only">(required)</span>
                </label>
                <input
                  id="ticket-title"
                  type="text"
                  value={ticketTitle}
                  onChange={(e) => { setTicketTitle(e.target.value); setError(''); }}
                  disabled={loading}
                  className="modal-input"
                  placeholder="Brief summary of the issue"
                  aria-required="true"
                  aria-describedby={error ? 'modal-error' : undefined}
                />
              </div>

              {/* Description */}
              <div className="modal-field">
                <label htmlFor="ticket-description" className="modal-label">
                  Description <span className="modal-required" aria-hidden="true">*</span>
                  <span className="sr-only">(required)</span>
                </label>
                <textarea
                  id="ticket-description"
                  value={ticketDescription}
                  onChange={(e) => { setTicketDescription(e.target.value); setError(''); }}
                  disabled={loading}
                  rows={10}
                  className="modal-textarea"
                  placeholder="Describe the issue in detail…"
                  aria-required="true"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="modal-btn-cancel" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button
                className="modal-btn-submit"
                onClick={handleSubmit}
                disabled={loading}
                aria-busy={loading}
              >
                {loading ? (
                  <span className="modal-btn-loading">
                    <span className="modal-spinner" aria-hidden="true" />
                    Submitting…
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
