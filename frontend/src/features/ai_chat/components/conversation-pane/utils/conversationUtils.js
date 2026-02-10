/**
 * Utility functions for conversation management
 */

// Module-level tracking to prevent multiple fetches across component remounts
export let globalFetchInProgress = false;
export let globalLastFetchTime = 0;
export const FETCH_COOLDOWN_MS = 5000; // Minimum 5 seconds between fetches

export function setGlobalFetchInProgress(value) {
  globalFetchInProgress = value;
}

export function setGlobalLastFetchTime(value) {
  globalLastFetchTime = value;
}

/**
 * Group conversations by relative date
 */
export function groupConversationsByDate(conversations) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);

  const groups = {
    today: [],
    yesterday: [],
    lastWeek: [],
    older: [],
  };

  conversations.forEach(conv => {
    const convDate = new Date(conv.updated_at || conv.created_at);
    const convDay = new Date(convDate.getFullYear(), convDate.getMonth(), convDate.getDate());

    if (convDay >= today) {
      groups.today.push(conv);
    } else if (convDay >= yesterday) {
      groups.yesterday.push(conv);
    } else if (convDay >= lastWeek) {
      groups.lastWeek.push(conv);
    } else {
      groups.older.push(conv);
    }
  });

  return groups;
}
