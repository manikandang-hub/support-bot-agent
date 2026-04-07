import { useState, useEffect, useRef } from 'react';
import ChatInterface from './ChatInterface';
import wtLogo from '../assets/wt-logo-icon.svg';

export default function ChatWidget({ plugins, selectedPlugin, onPluginChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef(null);
  const triggerRef = useRef(null);

  // Trap focus inside panel when open; return focus to trigger on close
  useEffect(() => {
    if (isOpen) {
      const firstFocusable = panelRef.current?.querySelector(
        'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    } else {
      triggerRef.current?.focus();
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape' && isOpen) setIsOpen(false);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  return (
    <>
      {/* Chat panel */}
      <div
        ref={panelRef}
        className={`widget-panel ${isOpen ? 'widget-panel--open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="SupportBot chat"
        aria-hidden={!isOpen}
      >
        <ChatInterface
          plugins={plugins}
          selectedPlugin={selectedPlugin}
          onPluginChange={onPluginChange}
          onClose={() => setIsOpen(false)}
        />
      </div>

      {/* Floating trigger button */}
      <button
        ref={triggerRef}
        className={`widget-trigger ${isOpen ? 'widget-trigger--open' : ''}`}
        onClick={() => setIsOpen(prev => !prev)}
        aria-label={isOpen ? 'Close SupportBot chat' : 'Open SupportBot chat'}
        aria-expanded={isOpen}
        aria-controls="widget-panel"
      >
        {/* WebToffee logo when closed */}
        <span className={`widget-trigger-logo ${isOpen ? 'widget-trigger-logo--hidden' : ''}`} aria-hidden="true">
          <img src={wtLogo} alt="" width="34" height="14" />
        </span>
        {/* Close X when open */}
        <span className={`widget-trigger-close ${isOpen ? '' : 'widget-trigger-logo--hidden'}`} aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </span>
      </button>
    </>
  );
}
