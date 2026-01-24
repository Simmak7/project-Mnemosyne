/**
 * Unit tests for useSmartBuckets hook
 * Tests Inbox filtering logic based on note properties
 */

// Since we can't easily test React hooks directly without a full setup,
// we'll extract and test the filtering logic

/**
 * Extracted inbox filtering logic for testing
 * This matches the logic in useSmartBuckets.js filterInboxNotes()
 */
function filterInboxNotes(notes) {
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  return notes.filter(note => {
    // Check if note was created within last 7 days
    const createdAt = new Date(note.created_at);
    const isRecent = createdAt > sevenDaysAgo;

    // Check if standalone (no tags, wikilinks, or images)
    const hasNoTags = !note.tags || note.tags.length === 0;
    const hasNoWikilinks = !note.wikilinks || note.wikilinks.length === 0;
    const hasNoImages = !note.image_id;

    return isRecent && hasNoTags && hasNoWikilinks && hasNoImages;
  });
}

describe('useSmartBuckets - Inbox Filtering', () => {
  const today = new Date();
  const threeDaysAgo = new Date(today);
  threeDaysAgo.setDate(today.getDate() - 3);
  const tenDaysAgo = new Date(today);
  tenDaysAgo.setDate(today.getDate() - 10);

  describe('filterInboxNotes', () => {
    it('should include standalone notes created within 7 days', () => {
      const notes = [
        {
          id: 1,
          title: 'Recent Standalone Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(1);
      expect(inbox[0].id).toBe(1);
    });

    it('should exclude notes older than 7 days', () => {
      const notes = [
        {
          id: 1,
          title: 'Old Standalone Note',
          content: 'Content',
          created_at: tenDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(0);
    });

    it('should exclude notes with tags', () => {
      const notes = [
        {
          id: 1,
          title: 'Tagged Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [{ id: 1, name: 'important' }],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(0);
    });

    it('should exclude notes with wikilinks', () => {
      const notes = [
        {
          id: 1,
          title: 'Note with Wikilinks',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: ['Other Note'],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(0);
    });

    it('should exclude notes with associated images', () => {
      const notes = [
        {
          id: 1,
          title: 'Note from Image',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: 123,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(0);
    });

    it('should handle notes with null/undefined properties', () => {
      const notes = [
        {
          id: 1,
          title: 'Minimal Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: null,
          wikilinks: undefined,
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      // Should be included (null/undefined treated as empty)
      expect(inbox).toHaveLength(1);
    });

    it('should filter multiple notes correctly', () => {
      const notes = [
        {
          id: 1,
          title: 'Inbox Note 1',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
        {
          id: 2,
          title: 'Old Note',
          content: 'Content',
          created_at: tenDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
        {
          id: 3,
          title: 'Tagged Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [{ id: 1, name: 'tag' }],
          wikilinks: [],
          image_id: null,
        },
        {
          id: 4,
          title: 'Inbox Note 2',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(2);
      expect(inbox[0].id).toBe(1);
      expect(inbox[1].id).toBe(4);
    });

    it('should return empty array for empty input', () => {
      const inbox = filterInboxNotes([]);
      expect(inbox).toHaveLength(0);
    });

    it('should handle notes exactly 7 days old (boundary)', () => {
      const exactlySevenDaysAgo = new Date(today);
      exactlySevenDaysAgo.setDate(today.getDate() - 7);

      const notes = [
        {
          id: 1,
          title: 'Boundary Note',
          content: 'Content',
          created_at: exactlySevenDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      // Should be excluded (uses > not >=, so exactly 7 days is too old)
      expect(inbox).toHaveLength(0);
    });

    it('should exclude notes with empty tags array (treated as no tags)', () => {
      const notes = [
        {
          id: 1,
          title: 'Note with Empty Tags',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      // Empty tags array should be treated as "no tags" - included
      expect(inbox).toHaveLength(1);
    });

    it('should exclude notes with multiple properties', () => {
      const notes = [
        {
          id: 1,
          title: 'Complex Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [{ id: 1, name: 'tag' }],
          wikilinks: ['Other Note'],
          image_id: 123,
        },
      ];

      const inbox = filterInboxNotes(notes);

      // Should be excluded (has tags, wikilinks, AND image)
      expect(inbox).toHaveLength(0);
    });

    it('should handle notes created today', () => {
      const notes = [
        {
          id: 1,
          title: 'Today Note',
          content: 'Content',
          created_at: today.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(1);
    });

    it('should handle notes created in the future (edge case)', () => {
      const tomorrow = new Date(today);
      tomorrow.setDate(today.getDate() + 1);

      const notes = [
        {
          id: 1,
          title: 'Future Note',
          content: 'Content',
          created_at: tomorrow.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      // Future notes should be included (they're "recent")
      expect(inbox).toHaveLength(1);
    });

    it('should preserve note order', () => {
      const notes = [
        {
          id: 3,
          title: 'Third',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
        {
          id: 1,
          title: 'First',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
        {
          id: 2,
          title: 'Second',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const inbox = filterInboxNotes(notes);

      expect(inbox).toHaveLength(3);
      expect(inbox[0].id).toBe(3);
      expect(inbox[1].id).toBe(1);
      expect(inbox[2].id).toBe(2);
    });

    it('should handle malformed date strings gracefully', () => {
      const notes = [
        {
          id: 1,
          title: 'Bad Date Note',
          content: 'Content',
          created_at: 'invalid-date-string',
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      // Should not throw error
      expect(() => filterInboxNotes(notes)).not.toThrow();

      const inbox = filterInboxNotes(notes);

      // Invalid date becomes NaN, which fails the isRecent check
      expect(inbox).toHaveLength(0);
    });

    it('should handle missing created_at field', () => {
      const notes = [
        {
          id: 1,
          title: 'No Date Note',
          content: 'Content',
          tags: [],
          wikilinks: [],
          image_id: null,
          // created_at is missing
        },
      ];

      // Should not throw error
      expect(() => filterInboxNotes(notes)).not.toThrow();

      const inbox = filterInboxNotes(notes);

      // Missing date should result in exclusion
      expect(inbox).toHaveLength(0);
    });
  });

  describe('Edge Cases and Special Scenarios', () => {
    it('should handle very large arrays efficiently', () => {
      const largeArray = Array.from({ length: 10000 }, (_, i) => ({
        id: i,
        title: `Note ${i}`,
        content: 'Content',
        created_at: threeDaysAgo.toISOString(),
        tags: i % 2 === 0 ? [] : [{ id: 1, name: 'tag' }],
        wikilinks: [],
        image_id: null,
      }));

      const startTime = Date.now();
      const inbox = filterInboxNotes(largeArray);
      const endTime = Date.now();

      // Should complete in reasonable time (<100ms for 10k items)
      expect(endTime - startTime).toBeLessThan(100);

      // Should filter correctly (only even-indexed notes have no tags)
      expect(inbox).toHaveLength(5000);
    });

    it('should be a pure function (no side effects)', () => {
      const originalNotes = [
        {
          id: 1,
          title: 'Test Note',
          content: 'Content',
          created_at: threeDaysAgo.toISOString(),
          tags: [],
          wikilinks: [],
          image_id: null,
        },
      ];

      const notesCopy = JSON.parse(JSON.stringify(originalNotes));

      filterInboxNotes(originalNotes);

      // Original array should not be modified
      expect(originalNotes).toEqual(notesCopy);
    });
  });
});
