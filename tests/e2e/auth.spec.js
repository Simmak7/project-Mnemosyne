/**
 * E2E tests for authentication flow
 * Tests login, logout, token persistence, and protected routes
 */

const { test, expect } = require('@playwright/test');

// Test user credentials (should exist in test database)
const TEST_USER = {
  username: 'test',
  password: 'test123',
};

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should display login page on initial load', async ({ page }) => {
    await page.goto('/');

    // Wait for login form to be visible
    await expect(page.locator('h1:has-text("AI Notes Notetaker")')).toBeVisible();
    await expect(page.locator('h2:has-text("Login")')).toBeVisible();
    await expect(page.locator('input#username')).toBeVisible();
    await expect(page.locator('input#password')).toBeVisible();
    await expect(page.locator('button:has-text("Login")')).toBeVisible();
  });

  test('should show validation error for empty credentials', async ({ page }) => {
    await page.goto('/');

    // Try to login without entering credentials
    await page.click('button:has-text("Login")');

    // Should still be on login page (form validation prevents submission)
    await expect(page.locator('h1:has-text("AI Notes Notetaker")')).toBeVisible();
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    await page.goto('/');

    // Fill in credentials
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);

    // Click login button
    await page.click('button:has-text("Login")');

    // Wait for navigation to main app (sidebar should appear)
    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Mnemosyne')).toBeVisible();

    // Verify localStorage has token
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();

    // Verify username is stored
    const username = await page.evaluate(() => localStorage.getItem('username'));
    expect(username).toBe(TEST_USER.username);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/');

    // Fill in invalid credentials
    await page.fill('input#username', 'invaliduser');
    await page.fill('input#password', 'wrongpassword');

    // Click login button
    await page.click('button:has-text("Login")');

    // Wait for error message or stay on login page
    await page.waitForTimeout(1000);

    // Should show error message or stay on login page
    await expect(page.locator('h1:has-text("AI Notes Notetaker")')).toBeVisible();
  });

  test('should persist authentication across page reloads', async ({ page }) => {
    await page.goto('/');

    // Login
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    // Wait for sidebar
    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Reload page
    await page.reload();

    // Should still be authenticated (no login page)
    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('h1:has-text("AI Notes Notetaker")')).not.toBeVisible();
  });

  test('should successfully logout', async ({ page }) => {
    await page.goto('/');

    // Login first
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    // Wait for sidebar
    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Click on user section to open dropdown
    await page.click('.user-section');

    // Wait for dropdown menu
    await expect(page.locator('.user-dropdown-menu')).toBeVisible();

    // Click logout button
    await page.click('button:has-text("Logout")');

    // Should redirect to login page
    await expect(page.locator('h1:has-text("AI Notes Notetaker")')).toBeVisible({ timeout: 5000 });

    // Verify localStorage is cleared
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeNull();
  });

  test('should open settings modal', async ({ page }) => {
    await page.goto('/');

    // Login first
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    // Wait for sidebar
    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Click on user section
    await page.click('.user-section');

    // Click settings button
    await page.click('button:has-text("Settings")');

    // Settings modal should appear (h2 in modal)
    await expect(page.locator('.settings-modal h2:has-text("Settings")')).toBeVisible();
  });

  test('should navigate between tabs after login', async ({ page }) => {
    await page.goto('/');

    // Login
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Click Notes tab
    await page.click('button:has-text("Notes")');
    await expect(page.locator('.page-title:has-text("Smart Notes")')).toBeVisible({ timeout: 5000 });

    // Click Gallery tab
    await page.click('button:has-text("Gallery")');
    await expect(page.locator('.page-title:has-text("Image Gallery")')).toBeVisible({ timeout: 5000 });

    // Click Brain tab (Knowledge Graph)
    await page.click('button:has-text("Brain")');
    await expect(page.locator('.page-title:has-text("Brain")')).toBeVisible({ timeout: 5000 });

    // Verify Workspace tab if enabled
    const workspaceButton = page.locator('button:has-text("Workspace")');
    if (await workspaceButton.isVisible()) {
      await workspaceButton.click();
      await expect(page.locator('.workspace-layout')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should open search with Ctrl+K shortcut', async ({ page }) => {
    await page.goto('/');

    // Login
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Press Ctrl+K (Cmd+K on Mac)
    await page.keyboard.press('Control+k');

    // Search modal should open
    await expect(page.locator('.unified-search-overlay')).toBeVisible({ timeout: 2000 });
  });

  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/');

    // Login
    await page.fill('input#username', TEST_USER.username);
    await page.fill('input#password', TEST_USER.password);
    await page.click('button:has-text("Login")');

    await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });

    // Get initial theme
    const initialTheme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    );

    // Click theme toggle
    await page.click('.theme-toggle');

    // Wait a bit for theme to change
    await page.waitForTimeout(500);

    // Verify theme changed
    const newTheme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    );

    expect(newTheme).not.toBe(initialTheme);

    // Verify localStorage was updated
    const darkMode = await page.evaluate(() =>
      localStorage.getItem('darkMode')
    );
    expect(darkMode).toBeTruthy();
  });
});
