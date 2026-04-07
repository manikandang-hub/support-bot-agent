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

// Simple markdown renderer: **bold**, *italic*, `code`, newlines → paragraphs
function parseInline(text, keyPrefix) {
  const result = [];
  const regex = /\*\*(.+?)\*\*|`([^`]+)`|\*(.+?)\*/g;
  let last = 0;
  let match;
  let i = 0;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) result.push(text.slice(last, match.index));
    if (match[1] !== undefined) result.push(<strong key={`${keyPrefix}-b${i++}`}>{match[1]}</strong>);
    else if (match[2] !== undefined) result.push(<code key={`${keyPrefix}-c${i++}`} className="inline-code">{match[2]}</code>);
    else if (match[3] !== undefined) result.push(<em key={`${keyPrefix}-e${i++}`}>{match[3]}</em>);
    last = match.index + match[0].length;
  }
  if (last < text.length) result.push(text.slice(last));
  return result;
}

function renderMarkdown(text) {
  if (!text) return null;
  const paragraphs = text.split(/\n{2,}/);
  return paragraphs.map((para, pi) => {
    const lines = para.split('\n');
    const content = lines.flatMap((line, li) => {
      const parts = parseInline(line, `${pi}-${li}`);
      return li < lines.length - 1 ? [...parts, <br key={`br-${pi}-${li}`} />] : parts;
    });
    return <p key={pi}>{content}</p>;
  });
}

export default function ChatMessage({ message, isUser, email }) {
  const initial = email ? email[0].toUpperCase() : 'U';
  const time = formatTime(message.timestamp);
  const isoTime = message.timestamp ? new Date(message.timestamp).toISOString() : undefined;

  if (isUser) {
    return (
      <li className="message-row user-row" aria-label={`You: ${message.text}`}>
        <div className="message-bubble">
          <div className="bubble-content">{message.text}</div>
          {time && (
            <time className="bubble-time" dateTime={isoTime} aria-label={`Sent at ${time}`}>
              {time}
            </time>
          )}
        </div>
      </li>
    );
  }

  return (
    <li className="message-row bot-row" aria-label="SupportBot response">
      <div className="avatar avatar-bot" aria-hidden="true">
        <img src={wtLogo} alt="" width="26" height="11" style={{ display: 'block' }} />
      </div>
      <div className="message-bubble">
        <div className="bubble-content">
          {message.explanation && renderMarkdown(message.explanation)}

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
        {time && (
          <time className="bubble-time" dateTime={isoTime} aria-label={`Received at ${time}`}>
            {time}
          </time>
        )}
      </div>
    </li>
  );
}
