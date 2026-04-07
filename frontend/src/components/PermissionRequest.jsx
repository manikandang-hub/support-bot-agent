import { useState } from 'react';
import { prepareTicket } from '../services/api';
import TicketModal from './TicketModal';
import TicketEscalation from './TicketEscalation';

export default function PermissionRequest({ reason, conversationId, pluginId, email, onTicketCreated }) {
  const [status, setStatus] = useState('pending'); // 'pending' | 'loading' | 'modal' | 'created' | 'declined'
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
    } catch (err) {
      setError('Failed to prepare ticket. Please try again.');
      setStatus('pending');
    }
  };

  const handleDecline = () => {
    setStatus('declined');
  };

  const handleModalClose = () => {
    // If ticket was created, keep showing the result; else go back to pending
    if (ticketData) return;
    setStatus('pending');
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
      <div className="permission-request declined">
        <p>No problem! Feel free to rephrase your question and I'll try again.</p>
      </div>
    );
  }

  return (
    <>
      <div className="permission-request">
        <p className="permission-notice">
          I wasn't able to find a solution in my knowledge base for this query. Would you like me to create a support ticket so our team can assist you?
        </p>
        {error && <p className="error-message">{error}</p>}
        <div className="permission-actions">
          <button
            className="btn-confirm"
            onClick={handleConfirm}
            disabled={status === 'loading'}
          >
            {status === 'loading' ? 'Preparing...' : 'Yes, create a ticket'}
          </button>
          <button
            className="btn-decline"
            onClick={handleDecline}
            disabled={status === 'loading'}
          >
            No, I'll rephrase
          </button>
        </div>
      </div>

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
