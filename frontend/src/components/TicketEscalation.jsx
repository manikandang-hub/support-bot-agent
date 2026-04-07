export default function TicketEscalation({ ticketId, ticketUrl, assignedAgent }) {
  return (
    <section className="ticket-card" aria-label="Support ticket created">
      <div className="ticket-card-header">
        <span className="ticket-card-icon" aria-hidden="true">🎟️</span>
        <span className="ticket-card-title">Support Ticket Created</span>
      </div>
      <div className="ticket-card-body">
        <p>A support ticket has been created and assigned to our team. We'll get back to you shortly.</p>

        {ticketId && (
          <div className="ticket-meta" role="list" aria-label="Ticket details">
            <div className="ticket-meta-row" role="listitem">
              <span className="ticket-meta-key">Ticket ID</span>
              <span className="ticket-meta-val">#{ticketId}</span>
            </div>
            {assignedAgent && (
              <div className="ticket-meta-row" role="listitem">
                <span className="ticket-meta-key">Assigned to</span>
                <span className="ticket-meta-val">{assignedAgent}</span>
              </div>
            )}
          </div>
        )}

        {ticketUrl && (
          <a
            href={ticketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="ticket-view-link"
            aria-label={`View ticket #${ticketId} in Zendesk (opens in new tab)`}
          >
            View in Zendesk
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </a>
        )}

        <p className="ticket-note">Our team will respond within 24 hours with next steps.</p>
      </div>
    </section>
  );
}
