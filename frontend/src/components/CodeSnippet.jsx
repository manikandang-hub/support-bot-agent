import { useState, useEffect } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-php';

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export default function CodeSnippet({ code, hooks }) {
  const [copied, setCopied] = useState(false);
  const [highlighted, setHighlighted] = useState('');

  useEffect(() => {
    try {
      if (code && Prism.languages.php) {
        setHighlighted(Prism.highlight(code, Prism.languages.php, 'php'));
      }
    } catch {
      setHighlighted('');
    }
  }, [code]);

  const handleCopy = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(code);
      } else {
        const el = document.createElement('textarea');
        el.value = code;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // silent fail
    }
  };

  if (!code) return null;

  return (
    <section className="code-block" aria-label="PHP code solution">
      {/* Header bar */}
      <div className="code-block-header">
        <div className="code-block-lang" aria-hidden="true">
          <span className="lang-dot" />
          PHP
        </div>
        <button
          className={`code-copy-btn${copied ? ' copied' : ''}`}
          onClick={handleCopy}
          aria-label={copied ? 'Copied to clipboard' : 'Copy code to clipboard'}
          aria-pressed={copied}
        >
          {copied ? (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="9" y="9" width="13" height="13" rx="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy
            </>
          )}
        </button>
      </div>

      {/* Scrollable code — horizontal + vertical */}
      <div
        className="code-scroll-area"
        tabIndex={0}
        role="region"
        aria-label="Code, scrollable"
      >
        <pre>
          <code
            className="language-php"
            dangerouslySetInnerHTML={{ __html: highlighted || escapeHtml(code) }}
          />
        </pre>
      </div>

      {/* Hook tags */}
      {hooks && hooks.length > 0 && (
        <div className="hooks-used" aria-label={`Hooks used: ${hooks.join(', ')}`} role="list">
          {hooks.map(h => (
            <span key={h} className="hook-tag" role="listitem" title={h}>{h}</span>
          ))}
        </div>
      )}
    </section>
  );
}
