# Quick Start Guide

Get up and running with Mnemosyne in 5 minutes.

---

## Step 1: Create Your Account

1. Open http://localhost:3000 in your browser
2. Click **Register** on the login page
3. Enter your details:
   - Username
   - Email address
   - Password (8+ characters with uppercase, lowercase, digit, special character)
4. Click **Create Account**

---

## Step 2: Create Your First Note

1. After logging in, you'll see the main workspace
2. Click the **+ New Note** button or press `Ctrl+N`
3. Enter a title for your note
4. Start typing in the editor
5. Your note saves automatically

### Editor Tips

| Action | How |
|--------|-----|
| Bold | `Ctrl+B` or **text** |
| Italic | `Ctrl+I` or *text* |
| Heading | `#` space for H1, `##` for H2 |
| Link note | `[[Note Title]]` |
| Add tag | `#tagname` |
| Slash commands | Type `/` for menu |

---

## Step 3: Upload an Image

1. Click the **Images** tab or navigate to Gallery
2. Click **Upload** or drag-and-drop an image
3. Wait for AI analysis (30-60 seconds)
4. The AI will:
   - Generate a description
   - Create a title
   - Suggest tags
   - Create a linked note

### Checking Upload Status

Look for the status indicator:
- **Queued** - Waiting to process
- **Processing** - AI analyzing
- **Completed** - Ready to view
- **Failed** - Click retry to try again

---

## Step 4: Connect Your Notes

### Using Wikilinks

Connect notes by typing `[[` followed by the note title:

```
This relates to my [[Project Ideas]] note.
```

The link becomes clickable and adds both notes to your knowledge graph.

### Using Hashtags

Add tags anywhere in your note:

```
This is a #meeting note about #project-alpha
```

Tags are case-insensitive and automatically indexed.

---

## Step 5: Search Your Knowledge

### Quick Search

Press `Ctrl+K` or click the search icon to open search.

### Search Types

| Type | What It Finds |
|------|---------------|
| **Keyword** | Exact text matches |
| **Semantic** | Conceptually similar content |
| **Tag** | Notes with specific tags |

### Search Syntax

```
meeting          # Find notes containing "meeting"
#project-alpha   # Find notes tagged with project-alpha
```

---

## Step 6: Ask Questions with RAG Chat

1. Click the **AI Chat** tab
2. Type a question about your notes
3. The AI will:
   - Search your knowledge base
   - Find relevant notes and images
   - Generate an answer with citations
   - Show source references

### Example Questions

- "What did I write about machine learning?"
- "Summarize my notes on the project meeting"
- "What images do I have related to architecture?"

---

## Step 7: Explore Smart Buckets

Smart Buckets help you organize automatically:

### AI Clusters
Notes grouped by similar content using AI.

### Inbox
Recent notes from the last 7 days.

### Orphans
Notes with no wikilink connections - good for review.

### Daily Notes
Automatic daily journal entries. Click **Today** to create today's note.

---

## Step 8: View the Knowledge Graph

1. Click the **Graph** tab or view button
2. See your notes as an interactive network
3. Click and drag to explore
4. Click a node to navigate to that note

### Graph Controls

| Action | How |
|--------|-----|
| Zoom | Scroll wheel |
| Pan | Click and drag background |
| Select | Click a node |
| Navigate | Double-click a node |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New note |
| `Ctrl+K` | Search |
| `Ctrl+S` | Save (auto-saves anyway) |
| `Ctrl+/` | Focus chat input |
| `Escape` | Close modal/panel |
| `/` | Slash command menu (in editor) |

---

## What's Next?

Now that you know the basics:

1. **Import existing notes** - Copy content from other apps
2. **Set up daily notes** - Build a journaling habit
3. **Explore AI features** - Try different prompts in chat
4. **Build your graph** - Connect ideas with wikilinks
5. **Customize settings** - Adjust preferences to your workflow

---

## Need Help?

- **In-app help** - Click the ? icon
- **API docs** - http://localhost:8000/docs
- **Full documentation** - [Documentation Index](../README.md)
