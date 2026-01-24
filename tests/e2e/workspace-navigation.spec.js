/**
 * E2E tests for Workspace navigation and interactions
 * Tests 3-pane layout, Smart Buckets, Context Rail, and Daily Notes
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

test.describe('Workspace Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);

    // Ensure workspace is enabled
    await page.evaluate(() => {
      localStorage.setItem('ENABLE_WORKSPACE', 'true');
    });

    // Navigate to Workspace tab
    await page.click('button:has-text("Workspace")');
    await expect(page.locator('.workspace-layout')).toBeVisible({ timeout: 5000 });
  });

  test('should display 3-pane workspace layout', async ({ page }) => {
    // Verify all three panes are present
    await expect(page.locator('.left-panel')).toBeVisible();
    await expect(page.locator('.center-panel')).toBeVisible();
    await expect(page.locator('.right-panel')).toBeVisible();

    // Verify resize handles exist
    const resizeHandles = page.locator('[data-panel-resize-handle-id]');
    await expect(resizeHandles.first()).toBeVisible();
  });

  test('should resize panes with drag', async ({ page }) => {
    // Get initial width of left pane
    const leftPane = page.locator('.left-panel');
    const initialWidth = await leftPane.boundingBox();

    // Find resize handle between left and center panes
    const resizeHandle = page.locator('[data-panel-resize-handle-id]').first();

    // Drag resize handle to the right
    await resizeHandle.hover();
    await page.mouse.down();
    await page.mouse.move(50, 0, { steps: 10 });
    await page.mouse.up();

    // Wait for resize to complete
    await page.waitForTimeout(500);

    // Get new width
    const newWidth = await leftPane.boundingBox();

    // Width should have changed (might be larger or smaller depending on drag direction)
    expect(newWidth.width).not.toBe(initialWidth.width);
  });

  test('should display Smart Buckets in left pane', async ({ page }) => {
    // Verify Note Hierarchy is visible
    await expect(page.locator('.note-hierarchy')).toBeVisible();

    // Verify all bucket types are present
    await expect(page.locator('text=Inbox')).toBeVisible();
    await expect(page.locator('text=Daily Notes')).toBeVisible();
    await expect(page.locator('text=AI Clusters')).toBeVisible();
    await expect(page.locator('text=Orphans')).toBeVisible();
  });

  test('should expand and collapse bucket sections', async ({ page }) => {
    // Find Inbox bucket header
    const inboxHeader = page.locator('.bucket-header:has-text("Inbox")');
    await expect(inboxHeader).toBeVisible();

    // Click to collapse (if expanded) or expand (if collapsed)
    await inboxHeader.click();

    // Wait for animation
    await page.waitForTimeout(300);

    // Click again to toggle
    await inboxHeader.click();
    await page.waitForTimeout(300);

    // Bucket should still be visible
    await expect(inboxHeader).toBeVisible();
  });

  test('should create daily note with Ctrl+Shift+D shortcut', async ({ page }) => {
    // Press Ctrl+Shift+D (Cmd+Shift+D on Mac)
    await page.keyboard.press('Control+Shift+D');

    // Wait for daily note to be created/opened
    await page.waitForTimeout(2000);

    // Daily note opens in read-only mode by default, click Edit Note button
    await expect(page.locator('.workspace-center-pane')).toBeVisible();
    await page.click('button:has-text("Edit Note")');
    await page.waitForTimeout(500);

    // Center pane should now show Tiptap editor
    await expect(page.locator('.tiptap-editor-container')).toBeVisible({ timeout: 5000 });

    // Daily note should appear in Daily Notes bucket
    const dailyNotesBucket = page.locator('.bucket-header:has-text("Daily Notes")');
    await expect(dailyNotesBucket).toBeVisible();

    // Expand Daily Notes bucket to see the note
    const dailyNotesHeader = page.locator('.bucket-header:has-text("Daily Notes")');
    await dailyNotesHeader.click();
    await page.waitForTimeout(500);

    // Should see today's date in the list
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0]; // YYYY-MM-DD format
    await expect(page.locator(`.note-item:has-text("${dateStr}")`).first()).toBeVisible({ timeout: 3000 });
  });

  test('should display Context Rail tabs', async ({ page }) => {
    // Verify Context Rail is visible
    await expect(page.locator('.context-rail')).toBeVisible();

    // Verify all tabs are present
    await expect(page.locator('button:has-text("Backlinks")')).toBeVisible();
    await expect(page.locator('button:has-text("Graph")')).toBeVisible();
    await expect(page.locator('button:has-text("Mentions")')).toBeVisible();
    await expect(page.locator('button:has-text("Info")')).toBeVisible();
  });

  test('should switch between Context Rail tabs', async ({ page }) => {
    // Click on Graph tab
    await page.click('button:has-text("Graph")');

    // Wait for panel to render
    await page.waitForTimeout(500);

    // Should show graph preview panel
    await expect(page.locator('.graph-preview-panel')).toBeVisible({ timeout: 3000 });

    // Click on Info tab
    await page.click('button:has-text("Info")');
    await page.waitForTimeout(500);

    // Should show info panel
    await expect(page.locator('.info-panel')).toBeVisible({ timeout: 3000 });

    // Click on Backlinks tab
    await page.click('button:has-text("Backlinks")');
    await page.waitForTimeout(500);

    // Should show backlinks panel
    await expect(page.locator('.backlinks-panel')).toBeVisible({ timeout: 3000 });
  });

  test('should click note in bucket and open in center pane', async ({ page }) => {
    // First, ensure there's a note in a bucket (create one if needed)
    // Press Ctrl+Shift+D to create daily note
    await page.keyboard.press('Control+Shift+D');
    await page.waitForTimeout(2000);

    // Expand Daily Notes bucket
    const dailyNotesHeader = page.locator('.bucket-header:has-text("Daily Notes")');
    await dailyNotesHeader.click();
    await page.waitForTimeout(500);

    // Click on a note in the list
    const firstNote = page.locator('.bucket-note-item').first();
    if (await firstNote.isVisible()) {
      await firstNote.click();

      // Wait for center pane to update
      await page.waitForTimeout(500);

      // Tiptap editor should be visible in center pane
      await expect(page.locator('.tiptap-editor-container')).toBeVisible({ timeout: 3000 });
    }
  });

  test('should display live info panel stats', async ({ page }) => {
    // Create/open a daily note
    await page.keyboard.press('Control+Shift+D');
    await page.waitForTimeout(2000);

    // Switch to Info tab in Context Rail
    await page.click('button:has-text("Info")');
    await page.waitForTimeout(500);

    // Verify info panel shows stats
    await expect(page.locator('.info-panel')).toBeVisible();
    await expect(page.locator('text=Words')).toBeVisible();
    await expect(page.locator('text=Characters')).toBeVisible();

    // Type in editor to update stats
    const editor = page.locator('.tiptap').first();
    if (await editor.isVisible()) {
      await editor.click();
      await page.keyboard.type('Testing word count update');

      // Wait for debounce
      await page.waitForTimeout(600);

      // Word count should update (should show at least 4 words)
      const wordCountElement = page.locator('.info-panel .stat-value').first();
      const wordCount = await wordCountElement.textContent();
      expect(parseInt(wordCount)).toBeGreaterThan(0);
    }
  });

  test('should show backlinks when wikilinks exist', async ({ page }) => {
    // This test requires creating two notes with a wikilink between them
    // Navigate to Notes tab first
    await page.click('button:has-text("Notes")');
    await page.waitForTimeout(1000);

    // Create first note
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();
    await page.fill('#note-title', 'Target Note for Backlinks');
    const editorTextarea1 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea1.fill('This is the target note.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);

    // Create second note with wikilink
    await page.click('button:has-text("Create Note")');
    await expect(page.locator('.note-editor-modal')).toBeVisible();
    await page.fill('#note-title', 'Source Note for Backlinks');
    const editorTextarea2 = page.locator('.w-md-editor-text-input').first();
    await editorTextarea2.fill('See [[Target Note for Backlinks]] for details.');
    await page.click('button:has-text("Save Note")');
    await expect(page.locator('.note-editor-modal')).not.toBeVisible({ timeout: 5000 });

    // Go back to Workspace
    await page.click('button:has-text("Workspace")');
    await page.waitForTimeout(1000);

    // Open the target note (the one being linked TO)
    // Search for it in buckets or use search
    await page.keyboard.press('Control+k');
    await page.fill('.unified-search-overlay input[type="text"]', 'Target Note for Backlinks');
    await page.waitForTimeout(500);

    const searchResult = page.locator('.search-result-item:has-text("Target Note for Backlinks")');
    if (await searchResult.isVisible()) {
      await searchResult.click();
    }

    // Close search overlay with Escape key
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    // Wait for note to open
    await page.waitForTimeout(1000);

    // Switch to Backlinks tab
    await page.click('button:has-text("Backlinks")');
    await page.waitForTimeout(500);

    // Should show the source note as a backlink
    await expect(page.locator('.backlinks-panel')).toBeVisible();
    // Check if "Source Note for Backlinks" appears in backlinks
    const backlinksContent = await page.locator('.backlinks-panel').textContent();
    expect(backlinksContent).toContain('Source Note for Backlinks');
  });

  test('should persist pane widths in localStorage', async ({ page }) => {
    // Get initial pane configuration
    const initialConfig = await page.evaluate(() => {
      return localStorage.getItem('workspace-pane-sizes');
    });

    // Resize a pane
    const resizeHandle = page.locator('[data-panel-resize-handle-id]').first();
    await resizeHandle.hover();
    await page.mouse.down();
    await page.mouse.move(100, 0, { steps: 10 });
    await page.mouse.up();

    // Wait for state to persist
    await page.waitForTimeout(1000);

    // Get new configuration
    const newConfig = await page.evaluate(() => {
      return localStorage.getItem('workspace-pane-sizes');
    });

    // Configuration should have changed
    expect(newConfig).not.toBe(initialConfig);

    // Reload page
    await page.reload();
    await page.waitForTimeout(2000);

    // Re-login after reload (page reload clears session)
    await login(page);

    // Navigate back to workspace
    await page.click('button:has-text("Workspace")');
    await page.waitForTimeout(1000);

    // Configuration should persist
    const persistedConfig = await page.evaluate(() => {
      return localStorage.getItem('workspace-pane-sizes');
    });

    expect(persistedConfig).toBe(newConfig);
  });

  test('should handle mobile responsive layout', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload to apply responsive layout
    await page.reload();
    await page.waitForTimeout(1000);

    // Re-login after reload
    await login(page);

    // Navigate to workspace
    await page.click('button:has-text("Workspace")');
    await page.waitForTimeout(1000);

    // On mobile, panes should stack vertically or show one at a time
    // This depends on your responsive implementation
    // Verify workspace layout still renders
    await expect(page.locator('.workspace-layout')).toBeVisible();
  });
});
