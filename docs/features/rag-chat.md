# RAG Chat Feature

RAG (Retrieval-Augmented Generation) Chat enables intelligent conversations with your knowledge base, providing answers with source citations.

---

## Overview

RAG Chat combines:
1. **Retrieval** - Find relevant notes, images, and content
2. **Augmentation** - Build context from retrieved sources
3. **Generation** - AI generates answers using context

Every response includes citations to source material.

---

## How It Works

### Query Processing Flow

```
User Question
    ↓
Generate query embedding (nomic-embed-text)
    ↓
Multi-source retrieval
├── Semantic search (pgvector)
├── Full-text search (tsvector)
├── Graph traversal (wikilinks)
└── Image retrieval (tags)
    ↓
Reciprocal Rank Fusion (ranking)
    ↓
Context building with citations [1], [2]...
    ↓
LLM generation (Ollama)
    ↓
Response with source references
```

---

## Retrieval Methods

### Semantic Search

Uses vector similarity to find conceptually related content:

- **Model:** nomic-embed-text (768 dimensions)
- **Index:** pgvector with IVFFlat
- **Threshold:** Configurable (default 0.7)

### Full-Text Search

PostgreSQL tsvector for keyword matching:

- **Language:** English stemming
- **Ranking:** ts_rank with normalization
- **Fuzzy:** Trigram similarity fallback

### Graph Traversal

BFS through wikilinks:

- **Depth:** 2 hops from seed notes
- **Decay:** 0.5x relevance per hop
- **Seed:** Top semantic matches

### Image Retrieval

Tag and content-based image search:

- **Tag matching:** Query terms → image tags
- **Description search:** AI-generated descriptions
- **Linked notes:** Through image-note relations

---

## Ranking System

### Reciprocal Rank Fusion (RRF)

Combines results from multiple sources:

```
score = Σ 1/(k + rank_i) × weight_i
```

### Default Weights

| Source | Weight |
|--------|--------|
| Semantic | 0.40 |
| Chunk (semantic) | 0.25 |
| Wikilink | 0.20 |
| Full-text | 0.10 |
| Image | 0.05 |

---

## Conversations

### Creating a Conversation

```http
POST /rag/conversations
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Project Research"
}
```

Response:
```json
{
  "id": "conv-123",
  "title": "Project Research",
  "created_at": "2024-01-15T10:00:00Z",
  "message_count": 0
}
```

### Auto-Title Generation

If no title provided, the first query becomes the title:
- "What is machine learning?" → "What is machine learning?"
- Truncated to 100 characters

---

## Querying

### Standard Query

```http
POST /rag/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": "conv-123",
  "query": "What have I written about neural networks?"
}
```

Response:
```json
{
  "id": "msg-456",
  "role": "assistant",
  "content": "Based on your notes, you have written about neural networks in several contexts...[1][2]",
  "citations": [
    {
      "index": 1,
      "note_id": 45,
      "title": "Neural Network Basics",
      "excerpt": "Neural networks are computing systems...",
      "relevance": 0.92,
      "source_type": "note"
    },
    {
      "index": 2,
      "note_id": 78,
      "title": "Deep Learning Notes",
      "excerpt": "Deep learning uses multiple layers...",
      "relevance": 0.87,
      "source_type": "note"
    }
  ],
  "metadata": {
    "retrieval_time_ms": 150,
    "generation_time_ms": 2500,
    "sources_used": 5
  }
}
```

### Streaming Query

For real-time responses:

```http
POST /rag/query/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": "conv-123",
  "query": "Summarize my machine learning notes"
}
```

Returns Server-Sent Events (SSE):

```
event: token
data: {"content": "Based"}

event: token
data: {"content": " on"}

event: token
data: {"content": " your"}

...

event: done
data: {"citations": [...], "metadata": {...}}
```

---

## Citations

### Citation Format

In responses, citations appear as `[1]`, `[2]`, etc.

Each citation includes:

| Field | Description |
|-------|-------------|
| `index` | Citation number |
| `note_id` | Source note ID |
| `title` | Note title |
| `excerpt` | Relevant snippet |
| `relevance` | Similarity score (0-1) |
| `source_type` | "note", "image", "chunk" |

### Viewing Citations

Citations link to source material:
- Click citation to preview
- Click preview to open full note
- Images show thumbnail and description

---

## Conversation Management

### List Conversations

```http
GET /rag/conversations?limit=20&offset=0
Authorization: Bearer <token>
```

Response:
```json
{
  "conversations": [
    {
      "id": "conv-123",
      "title": "Project Research",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T11:30:00Z",
      "message_count": 12
    }
  ],
  "total": 45
}
```

### Get Conversation with Messages

```http
GET /rag/conversations/{id}
Authorization: Bearer <token>
```

Response includes full message history with citations.

### Update Conversation

```http
PUT /rag/conversations/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Title"
}
```

### Delete Conversation

```http
DELETE /rag/conversations/{id}
Authorization: Bearer <token>
```

---

## Context Building

### Maximum Context Size

- **Default:** 4000 tokens
- **Configurable:** Per model limits

### Context Priority

1. Most relevant semantic matches
2. Wikilinked content (graph neighbors)
3. Full-text matches
4. Image descriptions

### Citation Markers

Context includes citation markers:

```
[1] Neural networks are computing systems inspired by biological neural networks...

[2] Deep learning is a subset of machine learning using multiple layers...

Based on the above context, answer: {user_query}
```

---

## API Endpoints

### Conversations

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/rag/conversations` | Create | 20/min |
| GET | `/rag/conversations` | List | 30/min |
| GET | `/rag/conversations/{id}` | Get with messages | 30/min |
| PUT | `/rag/conversations/{id}` | Update | 20/min |
| DELETE | `/rag/conversations/{id}` | Delete | 20/min |

### Queries

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/rag/query` | Execute query | 20/min |
| POST | `/rag/query/stream` | Streaming query | 20/min |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rag/health` | Health check |

---

## Frontend Integration

### AIChatLayout Component

Three-pane design:

| Pane | Content |
|------|---------|
| Left | Conversation history, Brain status |
| Center | Messages, input area |
| Right | Citation preview, settings |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New conversation |
| `Ctrl+/` | Focus input |
| `Ctrl+K` | Search conversations |
| `Escape` | Close preview |

### Message Actions

Each message supports:
- **Copy** - Copy text to clipboard
- **Regenerate** - Re-run query
- **Delete** - Remove message

---

## Query Tips

### Effective Queries

| Good | Why |
|------|-----|
| "What did I write about X?" | Searches your notes specifically |
| "Summarize my notes on Y" | Aggregates information |
| "How do A and B relate?" | Uses graph connections |

### Less Effective Queries

| Less Optimal | Why |
|--------------|-----|
| "What is X?" | May not reference your notes |
| "Tell me about Y" | Too general |
| Single words | Insufficient context |

### Query Patterns

1. **Research:** "What have I learned about [topic]?"
2. **Connections:** "How does [A] relate to [B] in my notes?"
3. **Summary:** "Summarize my notes on [topic]"
4. **Recall:** "What did I write about [topic] last month?"

---

## Performance

### Response Times

| Phase | Typical Time |
|-------|--------------|
| Embedding | 100ms |
| Retrieval | 200-500ms |
| Ranking | 50ms |
| Generation | 2-10s |

### Optimization Tips

1. **Keep queries focused** - Specific questions retrieve better
2. **Review citations** - Check source relevance
3. **Use streaming** - Better UX for long responses
4. **Rate limit aware** - 20 queries/minute

---

## Best Practices

### For Better Answers

1. **Write descriptive notes** - More context for retrieval
2. **Use consistent terminology** - Improves semantic matching
3. **Add wikilinks** - Enables graph traversal
4. **Tag content** - Improves categorization

### Conversation Organization

1. **Topic-focused chats** - One subject per conversation
2. **Meaningful titles** - Easy to find later
3. **Clean up old chats** - Delete irrelevant conversations
4. **Review citations** - Verify source accuracy
