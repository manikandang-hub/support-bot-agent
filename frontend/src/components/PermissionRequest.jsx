import { useState } from 'react';
import { prepareTicket } from '../services/api';
import TicketModal from './TicketModal';
import TicketEscalation from './TicketEscalation';

export default function PermissionRequest({ reason, conversationId, pluginId, email, onTicketCreated }) {
  const [status, setStatus] = useState('pending'); // pending | loading | modal | created | declined
  const [ticketDraft, setTicketDraft] = useState(null);
  const [ticketData, setTicketData] = useState(null);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setStatus('loading');
    setError('');
    try {
      const response = await prepareTicket(conversationId, pluginId, email);
      setTicketDraft(response.data);
      setStatus('modal');
    } catch {
      setError('Failed to prepare ticket. Please try again.');
      setStatus('pending');
    }
  };

  const handleDecline = () => setStatus('declined');

  const handleModalClose = () => {
    if (!ticketData) setStatus('pending');
  };

  const handleTicketCreated = (data) => {
    setTicketData(data);
    setStatus('created');
    if (onTicketCreated) onTicketCreated(data);
  };

  if (status === 'created' && ticketData) {
    return (
      <TicketEscalation
        ticketId={ticketData.ticket_id}
        ticketUrl={ticketData.ticket_url}
        assignedAgent={email}
      />
    );
  }

  if (status === 'declined') {
    return (
      <div className="permission-card declined" role="status">
        <div className="permission-card-body">
          <p style={{ color: '#6b7280' }}>No problem! Feel free to rephrase your question and I'll try again.</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <section className="permission-card" aria-label="Create support ticket request">
        <div className="permission-card-header">
          <span className="permission-card-icon" aria-hidden="true">🎫</span>
          <span className="permission-card-title">Need human support?</span>
        </div>
        <div className="permission-card-body">
          <p>I couldn't find a solution in my knowledge base. Would you like me to create a support ticket for our team to assist you directly?</p>
          {error && <p role="alert" style={{ color: '#dc2626', fontSize: '13px' }}>{error}</p>}
          <div className="permission-actions">
            <button
              className="btn-yes"
              onClick={handleConfirm}
              disabled={status === 'loading'}
              aria-busy={status === 'loading'}
            >
              {status === 'loading' ? (
                <>
                  <span className="modal-spinner" style={{ width: 13, height: 13 }} aria-hidden="true" />
                  Preparing…
                </>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13.5 19.79 19.79 0 0 1 1.61 4.87 2 2 0 0 1 3.6 2.69h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  Yes, create a ticket
                </>
              )}
            </button>
            <button
              className="btn-no"
              onClick={handleDecline}
              disabled={status === 'loading'}
            >
              No, I'll rephrase
            </button>
          </div>
        </div>
      </section>

      {status === 'modal' && ticketDraft && (
        <TicketModal
          title={ticketDraft.title}
          description={ticketDraft.description}
          conversationId={conversationId}
          pluginId={pluginId}
          email={email}
          onClose={handleModalClose}
          onCreated={handleTicketCreated}
        />
      )}
    </>
  );
}
