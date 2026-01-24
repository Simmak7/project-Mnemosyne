# Search Feature

The search feature provides multiple ways to find content: full-text keyword search, semantic similarity search, and tag-based filtering.

---

## Overview

Mnemosyne offers three complementary search methods:

| Method | Best For | Technology |
|--------|----------|------------|
| **Full-Text** | Exact words and phrases | PostgreSQL tsvector |
| **Semantic** | Conceptual similarity | pgvector + embeddings |
| **Tag** | Category filtering | Trigram fuzzy match |

---

## Full-Text Search

Traditional keyword-based search using PostgreSQL's built-in full-text search.

### How It Works

```
User query: "machine learning basics"
    ↓
Parse into tokens: machine, learn, basic (stemmed)
    ↓
Search tsvector index
    ↓
Rank by relevance (ts_rank)
    ↓
Return sorted results
```

### Features

- **Stemming** - "learning" matches "learn", "learned"
- **Stop words** - Common words ignored
- **Ranking** - Results ordered by relevance
- **Highlighting** - Matched terms highlighted

### API

```http
GET /search/fulltext?query=machine+learning&limit=20
Authorization: Bearer <token>
```

Response:
```json
{
  "results": [
    {
      "id": 45,
      "title": "Machine Learning Basics",
      "excerpt": "...introduction to <b>machine</b> <b>learning</b>...",
      "score": 0.85,
      "type": "note"
    }
  ],
  "total": 12,
  "query": "machine learning"
}
```

---

## Semantic Search

Find content by meaning using vector embeddings.

### How It Works

```
User query: "artificial intelligence tutorials"
    ↓
Generate embedding (nomic-embed-text)
    ↓
768-dimensional vector
    ↓
pgvector similarity search (cosine)
    ↓
Return notes above threshold
```

### Embedding Model

- **Model:** nomic-embed-text
- **Dimensions:** 768
- **Latency:** ~100ms per embedding

### Similarity Thresholds

| Threshold | Use Case |
|-----------|----------|
| 0.5 | Exploratory (wide net) |
| 0.7 | Default (balanced) |
| 0.85 | High confidence |
| 0.95 | Near-identical content |

### API

```http
GET /search/semantic?query=artificial+intelligence&threshold=0.7
Authorization: Bearer <token>
```

Response:
```json
{
  "results": [
    {
      "id": 45,
      "title": "Machine Learning Basics",
      "similarity": 0.89,
      "type": "note"
    },
    {
      "id": 78,
      "title": "Neural Network Introduction",
      "similarity": 0.82,
      "type": "note"
    }
  ],
  "query": "artificial intelligence",
  "threshold": 0.7
}
```

---

## Tag Search

Fuzzy search for tags using trigram similarity.

### How It Works

```
User query: "mach"
    ↓
Trigram decomposition: "mac", "ach"
    ↓
Compare against tag trigrams
    ↓
Return tags by similarity score
```

### Features

- **Typo tolerance** - "machin" matches "machine"
- **Partial matching** - "learn" matches "learning"
- **Ranked results** - Most similar first

### API

```http
GET /search/tags?query=mach&limit=10
Authorization: Bearer <token>
```

Response:
```json
{
  "tags": [
    {"name": "machine-learning", "similarity": 0.8, "note_count": 15},
    {"name": "machines", "similarity": 0.7, "note_count": 3}
  ]
}
```

---

## Combined Search

Search across notes and images simultaneously.

### Notes Search

```http
GET /search/notes?query=project+meeting
Authorization: Bearer <token>
```

### Images Search

```http
GET /search/images?query=sunset+landscape
Authorization: Bearer <token>
```

### Combined (Full-Text)

```http
GET /search/fulltext?query=project+meeting
Authorization: Bearer <token>
```

Returns both notes and images matching the query.

---

## Similar Notes

Find notes similar to a specific note.

### API

```http
GET /search/notes/{id}/similar?limit=10&threshold=0.6
Authorization: Bearer <token>
```

Response:
```json
{
  "source": {"id": 45, "title": "Machine Learning Basics"},
  "similar": [
    {"id": 78, "title": "Deep Learning Notes", "similarity": 0.88},
    {"id": 92, "title": "Neural Networks", "similarity": 0.82}
  ]
}
```

### Use Cases

- **Discovery** - Find related content
- **Deduplication** - Identify similar notes
- **Suggestions** - Recommend connections

---

## Unlinked Mentions

Find notes that mention another note's title but don't have a wikilink.

### API

```http
GET /search/notes/{id}/unlinked-mentions
Authorization: Bearer <token>
```

Response:
```json
{
  "note": {"id": 45, "title": "Machine Learning"},
  "unlinked": [
    {
      "id": 78,
      "title": "Project Notes",
      "context": "...discussed Machine Learning approaches..."
    }
  ]
}
```

### Use Case

Discover potential wikilink opportunities to strengthen your knowledge graph.

---

## Embedding Management

### Coverage Statistics

Check how many notes have embeddings:

```http
GET /search/embeddings/coverage
Authorization: Bearer <token>
```

Response:
```json
{
  "total_notes": 150,
  "with_embeddings": 145,
  "without_embeddings": 5,
  "coverage_percent": 96.7
}
```

### Regenerate Embedding

Force regeneration of a note's embedding:

```http
POST /search/notes/{id}/regenerate-embedding
Authorization: Bearer <token>
```

**Rate limit:** 10 per minute

### Embedding Generation

Embeddings are generated:
- **Automatically** - When notes are created/updated
- **Asynchronously** - Via Celery task queue
- **On demand** - Via regenerate endpoint

---

## Search Syntax

### Basic Queries

| Query | Matches |
|-------|---------|
| `machine learning` | Notes containing both words |
| `"machine learning"` | Exact phrase (if supported) |
| `machine OR learning` | Notes with either word |

### Filters

| Filter | Example |
|--------|---------|
| Tag filter | `?query=meeting&tag=project` |
| Date filter | `?query=meeting&after=2024-01-01` |
| Type filter | `?query=sunset&type=image` |

---

## API Endpoints

### Full-Text Search

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/search/fulltext` | Combined search | 20/min |
| GET | `/search/notes` | Notes only | 30/min |
| GET | `/search/images` | Images only | 30/min |

### Semantic Search

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/search/semantic` | Semantic search | 20/min |
| GET | `/search/notes/{id}/similar` | Similar notes | 30/min |
| GET | `/search/notes/{id}/unlinked-mentions` | Potential links | 30/min |

### Tag Search

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/search/tags` | Fuzzy tag search | 30/min |

### Embedding Management

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/search/embeddings/coverage` | Statistics | 30/min |
| POST | `/search/notes/{id}/regenerate-embedding` | Regenerate | 10/min |

---

## PostgreSQL Extensions

### tsvector (Full-Text)

```sql
-- Index creation
CREATE INDEX notes_content_fts ON notes
USING GIN (to_tsvector('english', content));

-- Query
SELECT * FROM notes
WHERE to_tsvector('english', content) @@ plainto_tsquery('english', 'machine learning');
```

### pgvector (Semantic)

```sql
-- Extension
CREATE EXTENSION vector;

-- Column
ALTER TABLE notes ADD COLUMN embedding vector(768);

-- Index
CREATE INDEX notes_embedding_idx ON notes
USING ivfflat (embedding vector_cosine_ops);

-- Query
SELECT * FROM notes
ORDER BY embedding <=> $query_embedding
LIMIT 10;
```

### pg_trgm (Fuzzy)

```sql
-- Extension
CREATE EXTENSION pg_trgm;

-- Index
CREATE INDEX tags_name_trgm ON tags
USING GIN (name gin_trgm_ops);

-- Query
SELECT * FROM tags
WHERE name % 'machin'
ORDER BY similarity(name, 'machin') DESC;
```

---

## Performance Tips

### Query Optimization

1. **Be specific** - Narrow queries are faster
2. **Use appropriate method** - Full-text for keywords, semantic for concepts
3. **Set reasonable thresholds** - Higher thresholds = fewer results = faster

### Index Maintenance

1. **Vacuum regularly** - Keep indexes efficient
2. **Monitor coverage** - Ensure embeddings are generated
3. **Check index health** - Rebuild if needed

### Caching

- Search results cached briefly
- Tag search results cached longer
- Clear cache on content changes

---

## Best Practices

### For Users

1. **Try both methods** - Keyword and semantic complement each other
2. **Use tags** - Pre-filtering by tag narrows results
3. **Check similar notes** - Discover related content
4. **Review unlinked mentions** - Build your graph

### For Content

1. **Write clearly** - Better embeddings from clear text
2. **Use consistent terms** - Improves semantic matching
3. **Add relevant tags** - Enables filtering
4. **Keep titles descriptive** - Helps unlinked mention detection
