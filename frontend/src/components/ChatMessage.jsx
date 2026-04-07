import CodeSnippet from './CodeSnippet';
import TicketEscalation from './TicketEscalation';
import ErrorBoundary from './ErrorBoundary';

export default function ChatMessage({ message, isUser }) {
  if (isUser) {
    return (
      <div className="message user-message">
        <div className="message-content">
          <p>{message.text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message bot-message">
      <div className="message-content">
        <p>{message.explanation}</p>

        {message.action === 'snippet' && message.code && (
          <ErrorBoundary>
            <CodeSnippet code={message.code} hooks={message.hook_names} />
          </ErrorBoundary>
        )}

        {message.action === 'escalate' && (
          <ErrorBoundary>
            <TicketEscalation
              ticketId={message.ticket_id}
              ticketUrl={message.ticket_url}
            />
          </ErrorBoundary>
        )}
      </div>
    </div>
  );
}
