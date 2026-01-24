# Database Schema

Complete database schema documentation for Mnemosyne v1.1.0.

**Database:** PostgreSQL 16 with extensions
**Extensions:** pgvector, pg_trgm

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │    notes    │       │    images   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │◄──────│ owner_id    │       │ id          │
│ username    │       │ id          │◄──┐   │ owner_id    │───►│users│
│ email       │       │ title       │   │   │ filename    │
│ hashed_pw   │       │ content     │   │   │ ai_desc     │
└─────────────┘       │ embedding   │   │   │ blur_hash   │
                      └─────────────┘   │   └─────────────┘
                             │          │          │
                             ▼          │          ▼
                      ┌─────────────┐   │   ┌─────────────┐
                      │  note_tags  │   │   │ image_tags  │
                      ├─────────────┤   │   ├─────────────┤
                      │ note_id     │   │   │ image_id    │
                      │ tag_id      │───┼──▶│ tag_id      │───►│tags│
                      └─────────────┘   │   └─────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │image_note_relations│
                              ├───────────────────┤
                              │ image_id          │
                              │ note_id           │
                              └───────────────────┘
```

---

## Core Tables

### users

User accounts and authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| hashed_password | VARCHAR(255) | NOT NULL | bcrypt hash |
| display_name | VARCHAR(100) | | Display name |
| is_active | BOOLEAN | DEFAULT true | Account active |
| is_verified | BOOLEAN | DEFAULT false | Email verified |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMP | | Last update |

**Indexes:**
- `users_username_idx` on username
- `users_email_idx` on email

---

### notes

User notes with content and embeddings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| title | VARCHAR(500) | NOT NULL | Note title |
| content | TEXT | | Rich text content |
| slug | VARCHAR(500) | | URL-friendly slug |
| embedding | VECTOR(768) | | Semantic embedding |
| owner_id | INTEGER | FK users(id) | Owner reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMP | | Last update |
| is_daily | BOOLEAN | DEFAULT false | Daily note flag |
| daily_date | DATE | | Daily note date |

**Indexes:**
- `notes_owner_idx` on owner_id
- `notes_slug_idx` on slug
- `notes_embedding_idx` USING ivfflat on embedding
- `notes_content_fts` USING GIN on tsvector(content)

---

### images

Uploaded images with AI analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| file_path | VARCHAR(500) | NOT NULL | Storage path |
| mime_type | VARCHAR(50) | | MIME type |
| file_size | INTEGER | | Size in bytes |
| width | INTEGER | | Pixel width |
| height | INTEGER | | Pixel height |
| blur_hash | VARCHAR(100) | | Blur hash string |
| ai_description | TEXT | | AI-generated description |
| analysis_status | VARCHAR(20) | | queued/processing/completed/failed |
| owner_id | INTEGER | FK users(id) | Owner reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Upload time |

**Indexes:**
- `images_owner_idx` on owner_id
- `images_status_idx` on analysis_status

---

### tags

Global tag entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Tag name (lowercase) |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |

**Indexes:**
- `tags_name_idx` on name
- `tags_name_trgm` USING GIN on name gin_trgm_ops

---

## Junction Tables

### note_tags

Many-to-many notes to tags.

| Column | Type | Constraints |
|--------|------|-------------|
| note_id | INTEGER | FK notes(id), NOT NULL |
| tag_id | INTEGER | FK tags(id), NOT NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |

**Primary Key:** (note_id, tag_id)

---

### image_tags

Many-to-many images to tags.

| Column | Type | Constraints |
|--------|------|-------------|
| image_id | INTEGER | FK images(id), NOT NULL |
| tag_id | INTEGER | FK tags(id), NOT NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |

**Primary Key:** (image_id, tag_id)

---

### image_note_relations

Many-to-many images to notes.

| Column | Type | Constraints |
|--------|------|-------------|
| image_id | INTEGER | FK images(id), NOT NULL |
| note_id | INTEGER | FK notes(id), NOT NULL |
| created_at | TIMESTAMP | DEFAULT NOW() |

**Primary Key:** (image_id, note_id)

---

## Security Tables

### user_2fa

Two-factor authentication secrets.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| user_id | INTEGER | FK users(id), UNIQUE | User reference |
| secret | VARCHAR(32) | NOT NULL | TOTP secret |
| is_enabled | BOOLEAN | DEFAULT false | 2FA enabled |
| backup_codes | TEXT[] | | Hashed backup codes |
| created_at | TIMESTAMP | DEFAULT NOW() | Setup time |

---

### password_reset_tokens

Password reset requests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| user_id | INTEGER | FK users(id) | User reference |
| token | VARCHAR(64) | UNIQUE, NOT NULL | Reset token |
| expires_at | TIMESTAMP | NOT NULL | Expiration time |
| used | BOOLEAN | DEFAULT false | Token used |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |

---

### login_attempts

Login attempt tracking for lockout.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| user_id | INTEGER | FK users(id) | User reference |
| ip_address | VARCHAR(45) | | Client IP |
| success | BOOLEAN | NOT NULL | Attempt success |
| created_at | TIMESTAMP | DEFAULT NOW() | Attempt time |

---

### user_sessions

Active session tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Session ID |
| user_id | INTEGER | FK users(id) | User reference |
| token_hash | VARCHAR(64) | | Token hash |
| ip_address | VARCHAR(45) | | Client IP |
| user_agent | VARCHAR(500) | | Browser info |
| last_activity | TIMESTAMP | | Last request |
| created_at | TIMESTAMP | DEFAULT NOW() | Login time |

---

## Chat Tables

### conversations

RAG chat conversations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Conversation ID |
| title | VARCHAR(200) | | Conversation title |
| owner_id | INTEGER | FK users(id) | Owner reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMP | | Last message time |

---

### chat_messages

Individual chat messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Message ID |
| conversation_id | UUID | FK conversations(id) | Conversation ref |
| role | VARCHAR(20) | NOT NULL | user/assistant/system |
| content | TEXT | NOT NULL | Message content |
| created_at | TIMESTAMP | DEFAULT NOW() | Message time |

---

### message_citations

Citation references in messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| message_id | UUID | FK chat_messages(id) | Message reference |
| note_id | INTEGER | FK notes(id) | Source note |
| excerpt | TEXT | | Relevant excerpt |
| relevance | FLOAT | | Similarity score |
| citation_index | INTEGER | | [1], [2], etc. |

---

## Graph Tables

### semantic_edges

AI-computed similarity edges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| source_id | INTEGER | FK notes(id) | Source note |
| target_id | INTEGER | FK notes(id) | Target note |
| similarity | FLOAT | NOT NULL | Cosine similarity |
| edge_type | VARCHAR(20) | DEFAULT 'semantic' | Edge type |
| created_at | TIMESTAMP | DEFAULT NOW() | Computation time |

**Index:** Unique on (source_id, target_id)

---

### graph_positions

Stable node positions for visualization.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| node_id | VARCHAR(50) | NOT NULL | Node identifier |
| node_type | VARCHAR(20) | NOT NULL | note/tag/image |
| x | FLOAT | | X coordinate |
| y | FLOAT | | Y coordinate |
| owner_id | INTEGER | FK users(id) | Owner reference |

---

### community_metadata

Cluster/community information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| community_id | INTEGER | NOT NULL | Community number |
| label | VARCHAR(100) | | Generated label |
| note_count | INTEGER | | Notes in community |
| representative_terms | TEXT[] | | Key terms |
| owner_id | INTEGER | FK users(id) | Owner reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Computation time |

---

## Collections Tables

### note_collections

Notebooks/project groupings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique identifier |
| name | VARCHAR(200) | NOT NULL | Collection name |
| description | TEXT | | Description |
| owner_id | INTEGER | FK users(id) | Owner reference |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation time |

---

### collection_notes

Junction for collections to notes.

| Column | Type | Constraints |
|--------|------|-------------|
| collection_id | INTEGER | FK note_collections(id) |
| note_id | INTEGER | FK notes(id) |
| position | INTEGER | | Sort order |

**Primary Key:** (collection_id, note_id)

---

## PostgreSQL Extensions

### pgvector

Vector similarity search.

```sql
CREATE EXTENSION vector;

-- 768-dimensional embedding column
ALTER TABLE notes ADD COLUMN embedding vector(768);

-- IVFFlat index for approximate nearest neighbor
CREATE INDEX notes_embedding_idx ON notes
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Similarity query
SELECT * FROM notes
ORDER BY embedding <=> $query_vector
LIMIT 10;
```

### pg_trgm

Trigram fuzzy matching.

```sql
CREATE EXTENSION pg_trgm;

-- Trigram index on tag names
CREATE INDEX tags_name_trgm ON tags
USING GIN (name gin_trgm_ops);

-- Fuzzy search query
SELECT * FROM tags
WHERE name % 'machin'
ORDER BY similarity(name, 'machin') DESC;
```

### Full-Text Search

Built-in PostgreSQL FTS.

```sql
-- Generate tsvector on insert/update
CREATE INDEX notes_content_fts ON notes
USING GIN (to_tsvector('english', content));

-- Full-text query
SELECT * FROM notes
WHERE to_tsvector('english', content) @@ plainto_tsquery('english', 'machine learning')
ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', 'machine learning')) DESC;
```

---

## Data Integrity

### Foreign Key Cascades

```sql
-- Notes deleted when user deleted
ALTER TABLE notes
ADD CONSTRAINT notes_owner_fk
FOREIGN KEY (owner_id) REFERENCES users(id)
ON DELETE CASCADE;

-- Tags preserved, junction rows deleted
ALTER TABLE note_tags
ADD CONSTRAINT note_tags_note_fk
FOREIGN KEY (note_id) REFERENCES notes(id)
ON DELETE CASCADE;
```

### Unique Constraints

- `users.username` - Unique usernames
- `users.email` - Unique emails
- `tags.name` - Unique tag names
- `(note_id, tag_id)` - No duplicate tag assignments

---

## Migration Notes

Migrations are handled via SQLAlchemy and Alembic-style scripts in `backend/migrations/`.

### Running Migrations

Migrations run automatically on application startup via `create_all()` or explicit migration scripts.

### Migration Files

| File | Purpose |
|------|---------|
| `add_security_tables.py` | 2FA, sessions, login tracking |
| `add_brain_tables.py` | Semantic edges, communities |
| `add_blurhash_fields.py` | Image blur hash support |
| `add_favorites_trash_fields.py` | Soft delete support |
