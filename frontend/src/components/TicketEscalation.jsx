export default function TicketEscalation({ ticketId, ticketUrl, assignedAgent }) {
  return (
    <div className="ticket-escalation">
      <div className="ticket-header">
        <span className="ticket-badge">🎟️ Support Ticket Created</span>
      </div>
      <div className="ticket-content">
        <p>
          This issue requires custom plugin development. A support ticket has been created and assigned to our team.
        </p>
        {ticketId && (
          <div className="ticket-info">
            <p>
              <strong>Ticket ID:</strong> #{ticketId}
            </p>
            {assignedAgent && (
              <p>
                <strong>Assigned to:</strong> {assignedAgent}
              </p>
            )}
            {ticketUrl && (
              <a href={ticketUrl} target="_blank" rel="noopener noreferrer" className="ticket-link">
                View Ticket in Zendesk →
              </a>
            )}
          </div>
        )}
        <p className="ticket-note">
          Our team will respond within 24 hours with next steps.
        </p>
      </div>
    </div>
  );
}
