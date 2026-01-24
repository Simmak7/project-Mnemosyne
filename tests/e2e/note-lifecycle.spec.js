/**
 * E2E tests for note lifecycle
 * Tests creating, editing, deleting notes with wikilinks and hashtags
 */

const { test, expect } = require('@playwright/test');

const TEST_USER = {
  username: 'test',
  password: 'test123',
};

// Helper function to login
async function login(page) {
  await page.goto('/');
  await page.fill('input#username', TEST_USER.username);
  await page.fill('input#password', TEST_USER.password);
  await page.click('button:has-text("Login")');
  await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });
}

test.describe('Note Lifecycle', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);

    // Navigate to Notes tab
    await page.click('button:has-text("Notes")');
    await expect(page.locator('.page-title:has-text("Smart Notes")')).toBeVisible({ timeout: 5000 });
  });

  test('should create a new note', async ({ page }) => {
    // Click Create Note button
    await page.click('button:has-text("Create Note")');

    // Wait for editor modal to open
    await expect(page.locator('.note-editor-modal')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('h2:has-text("Create New Note")')).toBeVisible();

    // Fill in title and content
    await page.fill('#note-title', 'Test Note Title');

    // Fill MDEditor content (find the textarea)
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This is my test note content.');

    // Save the note
    await page.click('button:has-text("Save Note")');

    // Wait for modal to close
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Verify note appears in the list (use .first() to handle virtual list duplicates)
    await expect(page.locator('.note-card h3.note-title:has-text("Test Note Title")').first()).toBeVisible({ timeout: 5000 });
  });

  test('should create note with wikilinks', async ({ page }) => {
    // Create first note (to link to)
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Target Note');
    const editorTextarea1 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea1.fill('This is the target note.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 5000 });

    // Wait a bit for the note to be saved
    await page.waitForTimeout(1000);

    // Create second note with wikilink to first
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Note with Wikilink');
    const editorTextarea2 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea2.fill('See [[Target Note]] for more information.');

    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Verify note with wikilink appears
    await expect(page.locator('.note-card h3.note-title:has-text("Note with Wikilink")').first()).toBeVisible({ timeout: 5000 });
  });

  test('should create note with hashtags', async ({ page }) => {
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Note with Tags');
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This note is tagged with #important and #testing tags.');

    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Verify note appears
    await expect(page.locator('.note-card h3.note-title:has-text("Note with Tags")').first()).toBeVisible({ timeout: 5000 });

    // Click on the note to view details
    await page.click('text=Note with Tags');

    // Wait for detail panel
    await expect(page.locator('.note-detail-panel')).toBeVisible({ timeout: 3000 });

    // Verify tags are displayed (if tag display is implemented)
    // This depends on your UI implementation
  });

  test('should edit an existing note', async ({ page }) => {
    // First create a note
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Original Title');
    const editorTextarea1 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea1.fill('Original content.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Wait for note to appear
    await expect(page.locator('.note-card h3.note-title:has-text("Original Title")').first()).toBeVisible({ timeout: 5000 });

    // Click the edit button on the note card
    const editButton = page.locator('.note-card:has-text("Original Title") .edit-note-btn').first();
    await editButton.click();

    // Wait for editor to open
    await expect(page.locator('.note-editor-modal')).toBeVisible();
    await expect(page.locator('h2:has-text("Edit Note")')).toBeVisible();

    // Modify title and content
    await page.fill('#note-title', 'Updated Title');
    const editorTextarea2 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea2.clear();
    await editorTextarea2.fill('Updated content with changes.');

    // Save changes
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Verify updated title appears
    await expect(page.locator('.note-card h3.note-title:has-text("Updated Title")').first()).toBeVisible({ timeout: 5000 });
  });

  test('should delete a note with confirmation', async ({ page }) => {
    // Create a note to delete
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Note to Delete');
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This note will be deleted.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Wait for note to appear
    await expect(page.locator('.note-card h3.note-title:has-text("Note to Delete")').first()).toBeVisible({ timeout: 5000 });

    // Click edit to open modal
    const editButton = page.locator('.note-card:has-text("Note to Delete") .edit-note-btn').first();
    await editButton.click();
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    // Click delete button
    await page.click('button:has-text("Delete")');

    // Confirm deletion
    await expect(page.locator('.delete-confirm')).toBeVisible();
    await page.click('button:has-text("Yes, Delete")');

    // Wait for modal to close
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Wait a bit for deletion to process
    await page.waitForTimeout(2000);

    // Verify note is removed from list (checking that at least one instance is gone)
    const deletedNotes = page.locator('.note-card h3.note-title:has-text("Note to Delete")');
    await expect(deletedNotes.first()).not.toBeVisible();
  });

  test('should cancel note deletion', async ({ page }) => {
    // Create a note
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Note to Keep');
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This note will not be deleted.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Open for editing
    const editButton = page.locator('.note-card:has-text("Note to Keep") .edit-note-btn').first();
    await editButton.click();
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    // Click delete
    await page.click('button:has-text("Delete")');
    await expect(page.locator('.delete-confirm')).toBeVisible();

    // Cancel deletion
    await page.click('button:has-text("Cancel")');

    // Confirmation should disappear
    await expect(page.locator('.delete-confirm')).not.toBeVisible();

    // Close modal
    await page.locator('.note-editor-modal button:has-text("Cancel")').first().click();

    // Verify note still exists
    await expect(page.locator('.note-card h3.note-title:has-text("Note to Keep")').first()).toBeVisible();
  });

  test('should view note details', async ({ page }) => {
    // Create a note
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Detailed Note');
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This note has detailed content that we will view.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });

    // Click on note to view details
    await page.click('.note-card:has-text("Detailed Note")');

    // Wait for detail panel to appear
    await expect(page.locator('.note-detail-panel')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('.note-detail-panel h2:has-text("Detailed Note")')).toBeVisible();

    // Verify content is displayed
    await expect(page.locator('.note-detail-content')).toBeVisible();

    // Close detail panel
    await page.click('.note-detail-panel .close-button');
    await expect(page.locator('.note-detail-panel')).not.toBeVisible();
  });

  test('should filter notes by search query', async ({ page }) => {
    // Create multiple notes
    const noteData = [
      { title: 'JavaScript Tutorial', content: 'Learn JavaScript' },
      { title: 'Python Guide', content: 'Learn Python' },
      { title: 'React Components', content: 'Building with React' },
    ];

    for (const note of noteData) {
      await page.click('button:has-text("Create Note")');
      await expect(page.locator('.note-editor-modal')).toBeVisible();
      await page.fill('#note-title', note.title);
      const editorTextarea = page.locator('.w-md-editor-text-input').first();
      await editorTextarea.fill(note.content);
      await page.click('button:has-text("Save Note")');
      await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 10000 });
      await page.waitForTimeout(500);
    }

    // Open search with Ctrl+K
    await page.keyboard.press('Control+k');
    await expect(page.locator('.unified-search-overlay')).toBeVisible({ timeout: 2000 });

    // Search for "JavaScript"
    await page.fill('.unified-search-overlay input[type="text"]', 'JavaScript');

    // Wait for search results (search might be debounced)
    await page.waitForTimeout(1500);

    // Verify JavaScript result appears
    const searchResults = page.locator('.search-result-item');
    await expect(searchResults.filter({ hasText: 'JavaScript' }).first()).toBeVisible({ timeout: 10000 });

    // Click on result to navigate
    await searchResults.filter({ hasText: 'JavaScript' }).first().click();

    // Search should close and note should be selected
    await expect(page.locator('.unified-search-overlay')).not.toBeVisible();
  });

  test('should handle empty note list gracefully', async ({ page }) => {
    // If notes exist, this test might need cleanup first
    // For now, just verify the UI handles the state

    // Check if empty state message exists (when no notes)
    const emptyState = page.locator('.empty-state');

    // If there are notes, we won't see empty state
    // Just verify the list renders without errors
    await expect(page.locator('.virtualized-note-list-container')).toBeVisible();
  });

  test('should navigate from note to graph', async ({ page }) => {
    // Create a note with tags
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();

    await page.fill('#note-title', 'Graph Navigation Test');
    const editorTextarea = page.locator('.w-md-editor-text-input').first();
    await editorTextarea.fill('This note has #graphtest tag.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 5000 });

    // Wait for note to be saved
    await page.waitForTimeout(1000);

    // Click on Brain/Graph tab to see the note in the graph
    await page.click('button:has-text("Brain")');

    // Wait for graph to load
    await expect(page.locator('.knowledge-graph-container')).toBeVisible({ timeout: 10000 });

    // Graph should render (verify canvas or SVG element exists)
    const graphElement = page.locator('canvas, svg').first();
    await expect(graphElement).toBeVisible({ timeout: 5000 });
  });
});
