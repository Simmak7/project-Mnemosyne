# System Architecture

Technical architecture documentation for Mnemosyne v1.1.0.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (React + TanStack)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   Auth   │ │  Notes   │ │  Images  │ │   RAG    │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       └────────────┴────────────┴────────────┘              │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────┐ ┌───────────────┐
│   PostgreSQL    │ │   Redis   │ │    Ollama     │
│   (pgvector)    │ │           │ │   (LLM/AI)    │
└─────────────────┘ └─────┬─────┘ └───────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Celery Worker │
                  │  (Async AI)   │
                  └───────────────┘
```

---

## Component Overview

### Frontend

| Technology | Purpose |
|------------|---------|
| React 18+ | UI framework |
| TanStack Query | Data fetching, caching |
| Tiptap | Rich text editor |
| Neural Glass | Design system |

### Backend

| Technology | Purpose |
|------------|---------|
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| Pydantic | Validation |
| Celery | Task queue |
| SlowAPI | Rate limiting |

### Data Layer

| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Primary database |
| pgvector | Vector similarity |
| Redis | Cache + queue |

### AI Layer

| Technology | Purpose |
|------------|---------|
| Ollama | LLM inference |
| llama3.2-vision | Image analysis |
| nomic-embed-text | Text embeddings |

---

## Fractal Feature Architecture

Each feature is self-contained with consistent structure:

### Backend Feature Structure

```
features/feature-name/
├── __init__.py         # Public exports
├── router.py           # FastAPI endpoints
├── service.py          # Business logic
├── schemas.py          # Pydantic models
├── models.py           # SQLAlchemy (re-exports)
├── tasks.py            # Celery tasks
├── claude.md           # Documentation
└── logic/              # Complex submodules
    ├── __init__.py
    └── specific.py
```

### Frontend Feature Structure

```
features/feature-name/
├── index.js            # Public exports
├── claude.md           # Documentation
├── components/         # React components
│   ├── Component.js
│   └── Component.css
├── hooks/              # Custom hooks
│   └── useFeature.js
└── utils/              # Helpers
    └── helpers.js
```

---

## Request Flow

### Synchronous Request

```
1. Client sends HTTP request
2. FastAPI router receives request
3. Dependencies resolved (auth, db session)
4. Service layer processes business logic
5. Database queried/updated
6. Response serialized via Pydantic
7. JSON response returned
```

### Asynchronous Request (AI)

```
1. Client sends upload request
2. Router saves file, creates DB record
3. Celery task queued (returns task_id)
4. Response returned immediately (202 Accepted)
5. Client polls task status
6. Celery worker processes task
   a. Calls Ollama API
   b. Processes AI response
   c. Updates database
7. Client receives completed status
```

---

## Database Architecture

### Schema Overview

```sql
-- Users and Auth
users (id, username, email, hashed_password, ...)
user_2fa (user_id, secret, backup_codes, ...)
user_sessions (id, user_id, token, ip, device, ...)

-- Content
notes (id, title, content, slug, embedding, owner_id, ...)
images (id, filename, file_path, blur_hash, owner_id, ...)
image_note_relations (image_id, note_id)

-- Organization
tags (id, name)
note_tags (note_id, tag_id)
image_tags (image_id, tag_id)
note_collections (id, name, owner_id, ...)

-- Graph
semantic_edges (id, source_id, target_id, similarity, ...)
graph_positions (node_id, x, y, ...)
community_metadata (id, label, note_ids, ...)

-- Chat
conversations (id, title, owner_id, ...)
chat_messages (id, conversation_id, role, content, ...)
message_citations (id, message_id, note_id, excerpt, ...)
```

### Key Indexes

```sql
-- Full-text search
CREATE INDEX notes_content_fts ON notes
USING GIN (to_tsvector('english', content));

-- Vector similarity
CREATE INDEX notes_embedding_idx ON notes
USING ivfflat (embedding vector_cosine_ops);

-- Fuzzy tags
CREATE INDEX tags_name_trgm ON tags
USING GIN (name gin_trgm_ops);
```

---

## Security Architecture

### Authentication Flow

```
1. User submits credentials
2. Password verified against bcrypt hash
3. If 2FA enabled, verify TOTP code
4. JWT token generated with user claims
5. Token returned to client
6. Client includes token in Authorization header
7. Backend validates token on each request
```

### Authorization Model

- **Resource ownership** - Users access only their data
- **owner_id filtering** - All queries filtered by owner
- **Exception: Tags** - Tags are global, associations are per-user

### Rate Limiting

```python
# Example rate limiter
@router.post("/", dependencies=[Depends(RateLimiter(times=30, seconds=60))])
async def create_note(...):
    ...
```

---

## Async Processing

### Celery Task Flow

```
┌───────────┐     ┌───────┐     ┌────────┐     ┌───────┐
│  Backend  │────▶│ Redis │────▶│ Celery │────▶│ Ollama│
│ (enqueue) │     │(queue)│     │(worker)│     │ (AI)  │
└───────────┘     └───────┘     └────────┘     └───────┘
                                     │
                                     ▼
                              ┌───────────┐
                              │ PostgreSQL│
                              │ (update)  │
                              └───────────┘
```

### Task Example

```python
@celery_app.task(bind=True)
def analyze_image_task(self, image_id: int, user_id: int):
    # Long-running AI operation
    result = call_ollama(image_id)
    update_database(image_id, result)
    return {"status": "completed", "result": result}
```

---

## AI Architecture

### Embedding Pipeline

```
Note Content
    ↓
Preprocess (strip HTML, normalize)
    ↓
Ollama API (nomic-embed-text)
    ↓
768-dimensional vector
    ↓
Store in pgvector column
    ↓
Index for similarity search
```

### RAG Pipeline

```
Query
    ↓
Generate query embedding
    ↓
Multi-source retrieval
├── Semantic (pgvector)
├── Full-text (tsvector)
├── Graph (wikilinks BFS)
└── Images (tags)
    ↓
Rank results (RRF)
    ↓
Build context with citations
    ↓
LLM generation
    ↓
Response with sources
```

---

## Caching Strategy

### Redis Usage

| Purpose | Key Pattern | TTL |
|---------|-------------|-----|
| Session cache | `session:{token}` | 24h |
| Task results | `celery-task-meta-{id}` | 1d |
| Cluster cache | `clusters:{user}:{k}` | 1h |
| Rate limits | `ratelimit:{ip}:{endpoint}` | varies |

### Cache Invalidation

- **Write-through** - Cache updated on writes
- **TTL-based** - Automatic expiration
- **Manual** - Explicit invalidation endpoints

---

## Scalability Considerations

### Horizontal Scaling

```
                    ┌─────────────┐
                    │ Load Balancer│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │ Backend 1│    │ Backend 2│    │ Backend 3│
     └────┬─────┘    └────┬─────┘    └────┬─────┘
          └───────────────┼───────────────┘
                          ▼
                  ┌───────────────┐
                  │   Database    │
                  │   (Primary)   │
                  └───────────────┘
```

### Scaling Points

| Component | Scale Method |
|-----------|--------------|
| Frontend | CDN + static hosting |
| Backend | Multiple containers |
| Celery | Add workers |
| Database | Read replicas |
| Redis | Cluster mode |
| Ollama | GPU instances |

---

## Monitoring Points

### Health Checks

```
GET /health
├── Database connectivity
├── Redis connectivity
├── Ollama availability
└── Celery queue status
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| Request latency | API response times |
| Task queue depth | Pending Celery tasks |
| Embedding coverage | Notes with embeddings |
| Cache hit rate | Redis efficiency |
| Error rate | Failed requests |

---

## Development Patterns

### Service Layer Pattern

```python
class NoteService:
    @staticmethod
    def create_note(db: Session, note: NoteCreate, user_id: int) -> Note:
        # Business logic encapsulated here
        note = Note(**note.dict(), owner_id=user_id)
        db.add(note)
        db.commit()
        return note
```

### Dependency Injection

```python
@router.get("/notes/")
async def list_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return NoteService.list_notes(db, current_user.id)
```

### Multi-tenant Isolation

```python
# Always filter by owner_id
notes = db.query(Note).filter(Note.owner_id == user.id).all()
```

---

## Error Handling

### Exception Hierarchy

```python
class MnemosyneException(Exception):
    """Base exception"""

class NotFoundError(MnemosyneException):
    """Resource not found"""

class AuthorizationError(MnemosyneException):
    """Not authorized"""

class ValidationError(MnemosyneException):
    """Input validation failed"""
```

### Global Handler

```python
@app.exception_handler(MnemosyneException)
async def handle_app_exception(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc)}
    )
```
