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
                  {/* Zendesk Z logo */}
                  <svg width="14" height="14" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14.786 12.03v11.654H4L14.786 12.03zM16.113 8c0-3.314 2.733-6 6.108-6C25.596 2 28.33 4.686 28.33 8s-2.734 6-6.109 6c-3.375 0-6.108-2.686-6.108-6zM16.215 24c0 3.314 2.733 6 6.108 6 3.375 0 6.109-2.686 6.109-6s-2.734-6-6.109-6c-3.375 0-6.108 2.686-6.108 6zM15.214 8c0-3.314-2.733-6-6.108-6C5.731 2 2.997 4.686 2.997 8s2.734 6 6.109 6c3.375 0 6.108-2.686 6.108-6zM17.329 12.03L28.115 23.684H17.329V12.03z"/>
                  </svg>
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
