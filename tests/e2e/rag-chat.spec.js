/**
 * E2E tests for RAG Chat functionality
 * Tests the citation-aware AI chat system with source attribution
 */

const { test, expect } = require('@playwright/test');

// Test user credentials (should exist in test database)
const TEST_USER = {
  username: 'test',
  password: 'test123',
};

/**
 * Helper function to login
 */
async function login(page) {
  await page.goto('/');
  await page.evaluate(() => localStorage.clear());
  await page.fill('input#username', TEST_USER.username);
  await page.fill('input#password', TEST_USER.password);
  await page.click('button:has-text("Login")');
  await expect(page.locator('.sidebar')).toBeVisible({ timeout: 10000 });
}

test.describe('RAG Chat', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should navigate to Ask Your Notes tab', async ({ page }) => {
    // Click on Ask Your Notes tab
    await page.click('button:has-text("Ask")');

    // Verify page title
    await expect(page.locator('.page-title:has-text("Ask Your Notes")')).toBeVisible({ timeout: 5000 });

    // Verify RAG Chat component is displayed
    await expect(page.locator('.rag-chat')).toBeVisible();
  });

  test('should display empty state when no messages', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Empty state should show
    await expect(page.locator('.rag-empty-state')).toBeVisible();
    await expect(page.locator('text=Ask about your notes')).toBeVisible();
    await expect(page.locator('text=Try asking:')).toBeVisible();
  });

  test('should have input area with placeholder', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Input should be visible
    const textarea = page.locator('.rag-input-area textarea');
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveAttribute('placeholder', 'Ask a question about your notes...');
  });

  test('should have disabled send button when input is empty', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Send button should be disabled when empty
    const sendBtn = page.locator('.send-btn');
    await expect(sendBtn).toBeDisabled();
  });

  test('should enable send button when text is entered', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Type in the input
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('What are my notes about?');

    // Send button should be enabled
    const sendBtn = page.locator('.send-btn');
    await expect(sendBtn).toBeEnabled();
  });

  test('should send message and show loading state', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Type a question
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('What are my notes about?');

    // Click send
    await page.click('.send-btn');

    // User message should appear
    await expect(page.locator('.rag-message.user')).toBeVisible({ timeout: 5000 });

    // Loading indicator or streaming should start
    const loadingOrStreaming = page.locator('.spinning, .streaming-cursor');
    await expect(loadingOrStreaming.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show assistant response after query', async ({ page }) => {
    test.setTimeout(120000); // 2 minute timeout for AI response

    await page.click('button:has-text("Ask")');

    // Type a question
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('What are my notes about?');

    // Click send
    await page.click('.send-btn');

    // Wait for assistant message to appear
    await expect(page.locator('.rag-message.assistant')).toBeVisible({ timeout: 90000 });

    // Message should have content
    const messageContent = page.locator('.rag-message.assistant .message-content');
    await expect(messageContent).not.toBeEmpty();
  });

  test('should clear input after sending message', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Type a question
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('What are my notes about?');

    // Click send
    await page.click('.send-btn');

    // Input should be cleared
    await expect(textarea).toHaveValue('');
  });

  test('should send message on Enter key', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Type a question
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('Test question');

    // Press Enter
    await textarea.press('Enter');

    // User message should appear
    await expect(page.locator('.rag-message.user')).toBeVisible({ timeout: 5000 });
  });

  test('should allow new line on Shift+Enter', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Type and add new line
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('Line 1');
    await textarea.press('Shift+Enter');
    await textarea.type('Line 2');

    // Should have both lines in textarea (not sent)
    await expect(textarea).toHaveValue('Line 1\nLine 2');
    await expect(page.locator('.rag-message.user')).not.toBeVisible();
  });

  test('should show header with title and buttons', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Header should have title
    await expect(page.locator('.rag-chat-header')).toBeVisible();
    await expect(page.locator('.header-title h3:has-text("Ask Your Notes")')).toBeVisible();
  });

  test('should show clear button after messages exist', async ({ page }) => {
    test.setTimeout(120000);

    await page.click('button:has-text("Ask")');

    // Send a message first
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('Hello');
    await page.click('.send-btn');

    // Wait for response
    await expect(page.locator('.rag-message.assistant')).toBeVisible({ timeout: 90000 });

    // Clear button (trash icon) should be visible
    const clearBtn = page.locator('.header-btn:has(svg.lucide-trash-2), .header-btn[title="Clear conversation"]');
    await expect(clearBtn).toBeVisible();
  });

  test('should show info button after messages exist', async ({ page }) => {
    test.setTimeout(120000);

    await page.click('button:has-text("Ask")');

    // Send a message first
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('Hello');
    await page.click('.send-btn');

    // Wait for response
    await expect(page.locator('.rag-message.assistant')).toBeVisible({ timeout: 90000 });

    // Info button should be visible
    const infoBtn = page.locator('.header-btn:has(svg.lucide-info), .header-btn[title="Show how answers are generated"]');
    await expect(infoBtn).toBeVisible();
  });

  test('should clear messages when clear button clicked', async ({ page }) => {
    test.setTimeout(120000);

    await page.click('button:has-text("Ask")');

    // Send a message
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('Hello');
    await page.click('.send-btn');

    // Wait for response
    await expect(page.locator('.rag-message.assistant')).toBeVisible({ timeout: 90000 });

    // Click clear button
    const clearBtn = page.locator('.header-btn:has(svg.lucide-trash-2), .header-btn[title="Clear conversation"]');
    await clearBtn.click();

    // Messages should be cleared, empty state should show
    await expect(page.locator('.rag-message')).not.toBeVisible();
    await expect(page.locator('.rag-empty-state')).toBeVisible();
  });

  test('should display timestamp on messages', async ({ page }) => {
    test.setTimeout(120000);

    await page.click('button:has-text("Ask")');

    // Send a message
    const textarea = page.locator('.rag-input-area textarea');
    await textarea.fill('What are my notes about?');
    await page.click('.send-btn');

    // Wait for user message to appear
    await expect(page.locator('.rag-message.user')).toBeVisible({ timeout: 5000 });

    // Timestamp should be visible on user message
    const userTimestamp = page.locator('.rag-message.user .message-time');
    await expect(userTimestamp).toBeVisible();
  });

  test('should show input hint text', async ({ page }) => {
    await page.click('button:has-text("Ask")');

    // Input hint should be visible
    await expect(page.locator('.input-hint')).toBeVisible();
    await expect(page.locator('text=Press Enter to send')).toBeVisible();
  });
});

test.describe('RAG Chat API Endpoints', () => {
  let token;

  test.beforeAll(async ({ request }) => {
    // Get auth token
    const loginResponse = await request.post('http://localhost:8000/login', {
      form: {
        username: TEST_USER.username,
        password: TEST_USER.password,
      },
    });
    const loginData = await loginResponse.json();
    token = loginData.access_token;
  });

  test('should have healthy RAG endpoint', async ({ request }) => {
    const response = await request.get('http://localhost:8000/rag/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.ollama.connected).toBeTruthy();
    expect(data.ollama.rag_model_available).toBeTruthy();
    expect(data.ollama.embedding_model_available).toBeTruthy();
  });

  test('should create conversation', async ({ request }) => {
    const response = await request.post('http://localhost:8000/rag/conversations', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      data: {
        title: 'Test Conversation',
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.id).toBeDefined();
    expect(data.title).toBe('Test Conversation');
    expect(data.message_count).toBe(0);
  });

  test('should list conversations', async ({ request }) => {
    const response = await request.get('http://localhost:8000/rag/conversations', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('should query RAG endpoint', async ({ request }) => {
    test.setTimeout(120000);

    const response = await request.post('http://localhost:8000/rag/query', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      data: {
        query: 'What are my notes about?',
        max_sources: 5,
        include_images: true,
        include_graph: true,
      },
    });

    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.answer).toBeDefined();
    expect(data.citations).toBeDefined();
    expect(Array.isArray(data.citations)).toBeTruthy();
    expect(data.retrieval_metadata).toBeDefined();
    expect(data.confidence_score).toBeDefined();
    expect(data.confidence_level).toBeDefined();
  });

  test('should reject unauthenticated RAG query', async ({ request }) => {
    const response = await request.post('http://localhost:8000/rag/query', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: {
        query: 'Test query',
      },
    });

    expect(response.status()).toBe(401);
  });

  test('should delete conversation', async ({ request }) => {
    // First create a conversation
    const createResponse = await request.post('http://localhost:8000/rag/conversations', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      data: {
        title: 'To Delete',
      },
    });

    const createData = await createResponse.json();
    const conversationId = createData.id;

    // Then delete it
    const deleteResponse = await request.delete(
      `http://localhost:8000/rag/conversations/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    expect(deleteResponse.ok()).toBeTruthy();

    const deleteData = await deleteResponse.json();
    expect(deleteData.message).toContain('deleted');
  });
});

test.describe('RAG Chat Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.click('button:has-text("Ask")');
  });

  test('should have accessible input', async ({ page }) => {
    const textarea = page.locator('.rag-input-area textarea');
    await expect(textarea).toBeVisible();

    // Should have placeholder for hint
    await expect(textarea).toHaveAttribute('placeholder');
  });

  test('should have accessible send button', async ({ page }) => {
    const sendBtn = page.locator('.send-btn');
    await expect(sendBtn).toHaveAttribute('aria-label', 'Send message');
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab to input
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Type something
    await page.keyboard.type('Test');

    // Tab to send button
    await page.keyboard.press('Tab');

    // Press Enter to send (button should be focused)
    await page.keyboard.press('Enter');

    // Message should be sent
    await expect(page.locator('.rag-message.user')).toBeVisible({ timeout: 5000 });
  });
});
