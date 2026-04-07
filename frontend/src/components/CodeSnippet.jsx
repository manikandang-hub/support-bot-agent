import { useState, useEffect } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-php';

export default function CodeSnippet({ code, hooks }) {
  const [copied, setCopied] = useState(false);
  const [highlightedCode, setHighlightedCode] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    try {
      if (code && Prism.languages.php) {
        const highlighted = Prism.highlight(code, Prism.languages.php, 'php');
        setHighlightedCode(highlighted);
        setError(null);
      }
    } catch (err) {
      console.error('Syntax highlighting error:', err);
      setHighlightedCode(code); // Fallback to non-highlighted code
      setError(null);
    }
  }, [code]);

  const handleCopy = () => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = code;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!code) {
    return <div className="code-snippet"><p>No code available</p></div>;
  }

  return (
    <div className="code-snippet">
      <div className="code-header">
        <span className="code-label">💻 PHP Solution</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? '✓ Copied!' : 'Copy Code'}
        </button>
      </div>
      <pre>
        <code
          className="language-php"
          dangerouslySetInnerHTML={{ __html: highlightedCode || code }}
        />
      </pre>
      {hooks && hooks.length > 0 && (
        <div className="hooks-info">
          <strong>Hooks Used:</strong> {hooks.join(', ')}
        </div>
      )}
    </div>
  );
}
