# Notes Feature

The notes feature is the core of Mnemosyne, providing rich text editing, wikilinks, hashtags, and automatic organization.

---

## Overview

Notes in Mnemosyne are more than just text documents. They're interconnected knowledge nodes that can:
- Link to other notes via wikilinks
- Be categorized with hashtags
- Have AI-generated embeddings for semantic search
- Be associated with images
- Form a visual knowledge graph

---

## Note Structure

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique identifier |
| `title` | String | Note title (required) |
| `content` | Text | Note body in HTML/Markdown |
| `slug` | String | URL-friendly identifier |
| `embedding` | Vector | 768-dim semantic embedding |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last modification |
| `owner_id` | Integer | User who owns the note |

### Relationships

- **Tags** - Many-to-many with tags table
- **Images** - Many-to-many with images table
- **Wikilinks** - Implicit via content parsing

---

## Creating Notes

### Basic Creation

```http
POST /notes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My First Note",
  "content": "<p>Hello, Mnemosyne!</p>"
}
```

Response:
```json
{
  "id": 1,
  "title": "My First Note",
  "content": "<p>Hello, Mnemosyne!</p>",
  "slug": "my-first-note",
  "tags": [],
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Automatic Processing

When a note is created:
1. **Slug generation** - Title converted to URL-friendly slug
2. **Hashtag extraction** - `#tags` parsed and linked
3. **Wikilink parsing** - `[[links]]` identified
4. **Embedding generation** - Queued for semantic indexing

---

## Wikilinks

Wikilinks connect notes together to form a knowledge graph.

### Syntax

| Format | Example | Result |
|--------|---------|--------|
| Basic | `[[Note Title]]` | Links to "Note Title" |
| Aliased | `[[Note Title|display]]` | Shows "display", links to "Note Title" |

### Usage Example

```markdown
This relates to my [[Project Ideas]] note.
See also [[Meeting Notes|the meeting]].
```

### Resolution

When rendering:
1. Parser finds `[[...]]` patterns
2. Title extracted
3. Note looked up by title/slug
4. If found: render as link
5. If not found: offer to create stub

### Creating Stubs

For unresolved wikilinks:

```http
POST /wikilinks/create-stub
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Note Title"
}
```

---

## Hashtags

Hashtags categorize and organize notes.

### Syntax

```
#tagname
```

Rules:
- Lowercase only (auto-converted)
- No spaces (use hyphens: `#my-tag`)
- Alphanumeric and hyphens
- Extracted automatically from content

### Example

```markdown
Today's #meeting notes about #project-alpha.
```

Both `meeting` and `project-alpha` tags are automatically created and linked.

---

## Rich Text Editor

The frontend uses **Tiptap** for rich text editing.

### Supported Formatting

| Format | Syntax/Shortcut |
|--------|-----------------|
| Bold | `Ctrl+B` or `**text**` |
| Italic | `Ctrl+I` or `*text*` |
| Heading 1 | `# ` at line start |
| Heading 2 | `## ` at line start |
| Heading 3 | `### ` at line start |
| Bullet List | `- ` at line start |
| Numbered List | `1. ` at line start |
| Task List | `[ ] ` at line start |
| Code Inline | `` `code` `` |
| Code Block | ` ``` ` on new line |
| Quote | `> ` at line start |

### Slash Commands

Type `/` to open the command menu:

| Command | Description |
|---------|-------------|
| `/heading` | Insert heading |
| `/bullet` | Start bullet list |
| `/numbered` | Start numbered list |
| `/task` | Insert task list |
| `/code` | Insert code block |
| `/quote` | Insert blockquote |
| `/image` | Insert image |
| `/link` | Create wikilink |

---

## Backlinks

Backlinks show all notes that reference the current note.

### Getting Backlinks

```http
GET /notes/{id}/backlinks
Authorization: Bearer <token>
```

Response:
```json
{
  "backlinks": [
    {
      "id": 5,
      "title": "Meeting Notes",
      "context": "...discussed the [[My Note]] concept..."
    },
    {
      "id": 12,
      "title": "Ideas",
      "context": "...see also [[My Note]] for..."
    }
  ]
}
```

---

## Enhanced Notes

Get notes with full relationship data:

```http
GET /notes-enhanced/
Authorization: Bearer <token>
```

Response includes:
- Note content
- All tags
- Linked images
- Backlink count
- Wikilink count

### Single Note Enhanced

```http
GET /notes/{id}/enhanced
Authorization: Bearer <token>
```

Includes graph data for visualization:
- Direct connections
- Semantic neighbors
- Suggested links

---

## Orphaned Notes

Notes with no wikilink connections:

```http
GET /notes/orphaned/list
Authorization: Bearer <token>
```

Useful for:
- Finding isolated content
- Identifying integration opportunities
- Maintaining knowledge graph health

---

## Most Linked Notes

Find your most referenced notes:

```http
GET /notes/most-linked/
Authorization: Bearer <token>
```

Response:
```json
[
  {"id": 1, "title": "Core Concepts", "link_count": 47},
  {"id": 5, "title": "Project Ideas", "link_count": 23},
  {"id": 12, "title": "Meeting Notes", "link_count": 18}
]
```

---

## API Endpoints

### CRUD Operations

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/notes/` | List all notes | 30/min |
| GET | `/notes/{id}` | Get single note | 30/min |
| POST | `/notes/` | Create note | 30/min |
| PUT | `/notes/{id}` | Update note | 30/min |
| DELETE | `/notes/{id}` | Delete note | 30/min |

### Enhanced Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/notes-enhanced/` | Notes with relationships | 30/min |
| GET | `/notes/{id}/enhanced` | Single note enhanced | 30/min |
| GET | `/notes/{id}/graph` | Note graph data | 30/min |
| GET | `/notes/{id}/backlinks` | Incoming links | 30/min |
| GET | `/notes/orphaned/list` | Unlinked notes | 30/min |
| GET | `/notes/most-linked/` | Popular notes | 30/min |

### Tag Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notes/{id}/tags/{name}` | Add tag |
| DELETE | `/notes/{id}/tags/{tag_id}` | Remove tag |

---

## Automatic Embedding Generation

When notes are created or updated:

1. Content queued for embedding
2. Celery worker processes queue
3. `nomic-embed-text` generates 768-dim vector
4. Vector stored in `embedding` field
5. Available for semantic search

### Regenerate Embedding

```http
POST /search/notes/{id}/regenerate-embedding
Authorization: Bearer <token>
```

---

## Best Practices

### Note Organization

1. **Use meaningful titles** - Helps with wikilink discovery
2. **Add relevant tags** - Enables filtering and clustering
3. **Create wikilinks liberally** - Builds knowledge graph
4. **Keep notes atomic** - One concept per note
5. **Review orphans regularly** - Connect isolated notes

### Writing for AI

1. **Be descriptive** - AI embeddings capture meaning
2. **Use consistent terminology** - Improves semantic search
3. **Add context** - Helps RAG chat answer questions
4. **Link related content** - Graph traversal finds connections
