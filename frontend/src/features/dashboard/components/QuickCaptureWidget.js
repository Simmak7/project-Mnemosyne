/**
 * QuickCaptureWidget - Fast journal note-taking from the dashboard
 *
 * Simplified inline input that appends to today's daily note.
 * Enter to submit, Shift+Enter for newline.
 * Shows last capture preview + "Captured!" flash on success.
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Sparkles, Send } from 'lucide-react';
import WidgetShell from './WidgetShell';
import { useDailyNote } from '../../daily/hooks/useDailyNote';
import { useCapture } from '../../daily/hooks/useCapture';
import './QuickCaptureWidget.css';

function QuickCaptureWidget({ onTabChange }) {
  const [text, setText] = useState('');
  const [lastCapture, setLastCapture] = useState(null);
  const [showFlash, setShowFlash] = useState(false);
  const textareaRef = useRef(null);
  const flashTimerRef = useRef(null);

  const { dailyNote, appendContent } = useDailyNote();
  const { capture, isCapturing } = useCapture(appendContent);

  const handleSubmit = useCallback(async () => {
    const trimmed = text.trim();
    if (!trimmed || isCapturing) return;

    try {
      await capture(trimmed);
      const preview = trimmed.length > 50 ? trimmed.slice(0, 50) + '...' : trimmed;
      setLastCapture({ text: preview, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
      setText('');
      setShowFlash(true);
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
      flashTimerRef.current = setTimeout(() => setShowFlash(false), 1500);
    } catch {
      // Error handled by useCapture
    }
  }, [text, capture, isCapturing]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  useEffect(() => {
    return () => { if (flashTimerRef.current) clearTimeout(flashTimerRef.current); };
  }, []);

  return (
    <WidgetShell
      icon={Sparkles}
      title="Quick Capture"
      action={() => onTabChange?.('journal')}
      actionLabel="Open Journal"
    >
      <div className="quick-capture-form">
        <textarea
          ref={textareaRef}
          className="quick-capture-textarea"
          placeholder={dailyNote ? "What's on your mind?" : 'Loading...'}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={!dailyNote || isCapturing}
        />
        <button
          className="quick-capture-send"
          onClick={handleSubmit}
          disabled={!text.trim() || isCapturing || !dailyNote}
          aria-label="Capture"
        >
          <Send size={14} />
        </button>
      </div>
      <div className="quick-capture-footer">
        {showFlash ? (
          <span className="quick-capture-flash">Captured!</span>
        ) : lastCapture ? (
          <span className="quick-capture-last" title={lastCapture.text}>
            Last: "{lastCapture.text}" at {lastCapture.time}
          </span>
        ) : (
          <span className="quick-capture-last">Enter to capture, Shift+Enter for newline</span>
        )}
      </div>
    </WidgetShell>
  );
}

export default QuickCaptureWidget;
