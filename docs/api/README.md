# API Reference

Complete REST API documentation for Mnemosyne v1.1.0.

**Base URL:** `http://localhost:8000`
**Interactive Docs:** `http://localhost:8000/docs`

---

## Authentication

All endpoints (except `/register` and `/login`) require a valid JWT token.

### Header Format

```
Authorization: Bearer <token>
```

### Token Expiration

Tokens expire after 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

## Response Format

### Success Response

```json
{
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse.

| Endpoint Category | Default Limit |
|-------------------|---------------|
| Registration | 5/hour |
| Login | 10/minute |
| Create/Update/Delete | 20-30/minute |
| Read/List | 30/minute |
| AI Operations | 10-20/minute |

Exceeded limits return `429 Too Many Requests`.

---

## Endpoint Index

### Authentication (`/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create account |
| POST | `/login` | Get JWT token |
| GET | `/me` | Current user info |
| POST | `/change-password` | Update password |
| POST | `/forgot-password` | Request reset |
| POST | `/reset-password` | Complete reset |

### Notes (`/notes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notes/` | List all notes |
| GET | `/notes/{id}` | Get single note |
| POST | `/notes/` | Create note |
| PUT | `/notes/{id}` | Update note |
| DELETE | `/notes/{id}` | Delete note |
| GET | `/notes-enhanced/` | Notes with relations |
| GET | `/notes/{id}/enhanced` | Single note enhanced |
| GET | `/notes/{id}/graph` | Note graph data |
| GET | `/notes/{id}/backlinks` | Incoming links |
| GET | `/notes/orphaned/list` | Unlinked notes |
| GET | `/notes/most-linked/` | Popular notes |
| POST | `/notes/{id}/tags/{name}` | Add tag |
| DELETE | `/notes/{id}/tags/{id}` | Remove tag |

### Images (`/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-image/` | Upload image |
| GET | `/images/` | List images |
| GET | `/image/{id}` | Get image file |
| DELETE | `/images/{id}` | Delete image |
| POST | `/retry-image/{id}` | Retry analysis |
| GET | `/task-status/{id}` | Check task |
| POST | `/images/{id}/tags/{name}` | Add tag |
| DELETE | `/images/{id}/tags/{id}` | Remove tag |

### Tags (`/tags`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tags/` | List user tags |
| POST | `/tags/` | Create/get tag |

### Search (`/search`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/fulltext` | Full-text search |
| GET | `/search/notes` | Search notes |
| GET | `/search/images` | Search images |
| GET | `/search/tags` | Fuzzy tag search |
| GET | `/search/semantic` | Semantic search |
| GET | `/search/notes/{id}/similar` | Similar notes |
| GET | `/search/notes/{id}/unlinked-mentions` | Potential links |
| GET | `/search/embeddings/coverage` | Embedding stats |
| POST | `/search/notes/{id}/regenerate-embedding` | Regenerate |

### Smart Buckets (`/buckets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/buckets/clusters` | AI clusters |
| GET | `/buckets/clusters/{id}/notes` | Cluster notes |
| POST | `/buckets/clusters/invalidate-cache` | Clear cache |
| GET | `/buckets/orphans` | Orphaned notes |
| GET | `/buckets/inbox` | Recent notes |
| GET | `/buckets/daily` | Daily notes list |
| POST | `/buckets/daily/today` | Get/create today |
| GET | `/buckets/daily/{date}` | By date |

### RAG Chat (`/rag`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/query` | Execute query |
| POST | `/rag/query/stream` | Streaming query |
| POST | `/rag/conversations` | Create conversation |
| GET | `/rag/conversations` | List conversations |
| GET | `/rag/conversations/{id}` | Get with messages |
| PUT | `/rag/conversations/{id}` | Update |
| DELETE | `/rag/conversations/{id}` | Delete |
| GET | `/rag/health` | Health check |

### Graph (`/graph`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph/data` | Full graph |
| GET | `/graph/local` | Local neighborhood |
| GET | `/graph/map` | Clustered view |
| GET | `/graph/path` | Path finder |
| GET | `/graph/search` | Node autocomplete |
| GET | `/graph/stats` | Statistics |
| POST | `/wikilinks/resolve` | Resolve links |
| POST | `/wikilinks/create-stub` | Create stub |

### System (`/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI docs |
| GET | `/redoc` | ReDoc docs |

---

## Detailed Endpoints

### POST /register

Create a new user account.

**Request:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:**
- `400` - Invalid input
- `409` - Username/email exists
- `422` - Validation error
- `429` - Rate limit exceeded

---

### POST /login

Authenticate and get JWT token.

**Request:** (form data)
```
username=johndoe&password=SecurePass123!
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` - Invalid credentials
- `403` - Account locked
- `429` - Rate limit exceeded

---

### POST /notes/

Create a new note.

**Request:**
```json
{
  "title": "My Note",
  "content": "<p>Note content with [[wikilinks]] and #tags</p>"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "title": "My Note",
  "content": "<p>Note content with [[wikilinks]] and #tags</p>",
  "slug": "my-note",
  "tags": [{"id": 1, "name": "tags"}],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

### POST /upload-image/

Upload an image for AI analysis.

**Request:** (multipart/form-data)
```
file: <binary image data>
```

**Response:** `202 Accepted`
```json
{
  "id": 1,
  "task_id": "abc-123",
  "status": "queued",
  "filename": "photo.jpg",
  "message": "Image queued for AI analysis"
}
```

---

### GET /task-status/{task_id}

Check Celery task status.

**Response:** `200 OK`
```json
{
  "status": "completed",
  "result": {
    "image_id": 1,
    "note_id": 5,
    "title": "Generated Title",
    "description": "AI description...",
    "tags": ["tag1", "tag2"]
  }
}
```

**Status Values:** `queued`, `processing`, `completed`, `failed`

---

### POST /rag/query

Execute a RAG query.

**Request:**
```json
{
  "conversation_id": "conv-123",
  "query": "What have I written about machine learning?"
}
```

**Response:** `200 OK`
```json
{
  "id": "msg-456",
  "role": "assistant",
  "content": "Based on your notes...[1][2]",
  "citations": [
    {
      "index": 1,
      "note_id": 45,
      "title": "ML Basics",
      "excerpt": "...",
      "relevance": 0.92
    }
  ]
}
```

---

### GET /search/semantic

Semantic similarity search.

**Parameters:**
- `query` (required) - Search query
- `threshold` (optional) - Similarity threshold (default: 0.7)
- `limit` (optional) - Max results (default: 20)

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": 45,
      "title": "Machine Learning",
      "similarity": 0.89
    }
  ],
  "query": "artificial intelligence",
  "threshold": 0.7
}
```

---

### GET /graph/data

Get full knowledge graph.

**Response:** `200 OK`
```json
{
  "nodes": [
    {"id": "note-1", "type": "note", "label": "My Note"}
  ],
  "edges": [
    {"source": "note-1", "target": "note-2", "type": "wikilink"}
  ],
  "stats": {
    "node_count": 150,
    "edge_count": 320
  }
}
```

---

## WebSocket Endpoints

### /rag/query/stream (SSE)

Server-Sent Events for streaming responses.

**Events:**
```
event: token
data: {"content": "word"}

event: done
data: {"citations": [...]}
```

---

## Common Parameters

### Pagination

| Parameter | Description | Default |
|-----------|-------------|---------|
| `limit` | Items per page | 20 |
| `offset` | Skip items | 0 |

### Filtering

| Parameter | Description |
|-----------|-------------|
| `tag` | Filter by tag name |
| `after` | Created after date |
| `before` | Created before date |

### Sorting

| Parameter | Description |
|-----------|-------------|
| `sort` | Field to sort by |
| `order` | `asc` or `desc` |

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |
