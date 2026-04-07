import CodeSnippet from './CodeSnippet';
import TicketEscalation from './TicketEscalation';
import PermissionRequest from './PermissionRequest';
import ErrorBoundary from './ErrorBoundary';
import wtLogo from '../assets/wt-logo-icon.svg';

function formatTime(ts) {
  if (!ts) return '';
  try { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
  catch { return ''; }
}

export default function ChatMessage({ message, isUser, email }) {
  const initial = email ? email[0].toUpperCase() : 'U';
  const time = formatTime(message.timestamp);

  if (isUser) {
    return (
      <div className="message-row user-row" role="listitem" aria-label={`You: ${message.text}`}>
        <div className="message-bubble">
          <div className="bubble-content" role="text">{message.text}</div>
          {time && <span className="bubble-time">{time}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="message-row bot-row" role="listitem" aria-label="SupportBot response">
      <div className="avatar avatar-bot" aria-hidden="true">
        <img src={wtLogo} alt="" width="26" height="11" style={{ display: 'block' }} />
      </div>
      <div className="message-bubble">
        <div className="bubble-content">
          {message.explanation && <p role="text">{message.explanation}</p>}

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
                assignedAgent={message.email}
              />
            </ErrorBoundary>
          )}

          {message.action === 'ask_permission' && (
            <ErrorBoundary>
              <PermissionRequest
                reason={message.reason}
                conversationId={message.conversation_id}
                pluginId={message.plugin_id}
                email={message.email}
              />
            </ErrorBoundary>
          )}
        </div>
        {time && <span className="bubble-time">{time}</span>}
      </div>
    </div>
  );
}
