import React, { useCallback } from 'react';
import { CaptureStream } from '../../../daily';
import { useCapture } from '../../../daily/hooks/useCapture';
import { useJournalContext } from '../../hooks/JournalContext';
import { extractHashtags } from '../../utils/hashtagExtractor';
import { tagsApi } from '../../../tags/api';

/**
 * CaptureSection - Wrapper around CaptureStream for the journal.
 * Handles tag extraction from captures and /tag command.
 * Only shows for today's date.
 */
function CaptureSection() {
  const { isToday, dailyNote, appendContent, isLoading } = useJournalContext();

  const handleCapture = useCallback(async (type, content) => {
    const noteId = dailyNote?.id;

    // /tag command: add tag directly, don't append to content
    if (type === 'tag' && noteId) {
      try {
        await tagsApi.addTagToNote(noteId, content);
      } catch (err) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Failed to add tag:', err);
        }
      }
      return;
    }

    // Append content as usual
    await appendContent(type, content);

    // After appending, extract inline #hashtags and add them as tags
    if (noteId && (type === 'text' || type === 'todo' || type === 'link')) {
      const hashtags = extractHashtags(content);
      for (const tag of hashtags) {
        try {
          await tagsApi.addTagToNote(noteId, tag);
        } catch (err) {
          // Silently fail - tag creation is best-effort
        }
      }
    }
  }, [appendContent, dailyNote]);

  const { capture } = useCapture(handleCapture);

  if (!isToday) return null;

  return (
    <div className="journal-capture-section">
      <CaptureStream
        onCapture={capture}
        disabled={isLoading}
        placeholder="Capture a thought... (/ for commands, #tag to tag)"
      />
    </div>
  );
}

export default CaptureSection;
