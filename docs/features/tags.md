# Tags Feature

Tags provide a flexible way to categorize and organize notes and images across your knowledge base.

---

## Overview

Tags in Mnemosyne are:
- **Global** - Shared across all users (but associations are per-user)
- **Case-insensitive** - "Python", "python", "PYTHON" are the same tag
- **Many-to-many** - A note/image can have multiple tags, and vice versa
- **Auto-created** - New tags are created on demand

---

## Tag Characteristics

### Case Insensitivity

All tags are stored in lowercase:

```
#Python → python
#MACHINE-LEARNING → machine-learning
#My Tag → my-tag
```

### Naming Rules

| Rule | Valid | Invalid |
|------|-------|---------|
| Lowercase letters | `project` | - |
| Numbers | `project2024` | - |
| Hyphens | `my-project` | - |
| No spaces | - | `my project` |
| No special chars | - | `project@work` |

### Global Sharing

Tags are stored globally but associations are user-specific:
- User A and User B can both use the tag "python"
- User A's notes with "python" are separate from User B's
- This enables potential future collaboration features

---

## Adding Tags

### Via Hashtag Syntax

In notes, use `#tagname`:

```markdown
This is my #meeting notes for #project-alpha.
```

Tags are automatically:
1. Extracted from content
2. Created if new
3. Associated with the note

### Via API

Add tag to a note:

```http
POST /notes/{note_id}/tags/{tag_name}
Authorization: Bearer <token>
```

Add tag to an image:

```http
POST /images/{image_id}/tags/{tag_name}
Authorization: Bearer <token>
```

Response:
```json
{
  "id": 1,
  "name": "project-alpha",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Removing Tags

From a note:

```http
DELETE /notes/{note_id}/tags/{tag_id}
Authorization: Bearer <token>
```

From an image:

```http
DELETE /images/{image_id}/tags/{tag_id}
Authorization: Bearer <token>
```

---

## Listing Tags

### All User Tags

```http
GET /tags/
Authorization: Bearer <token>
```

Response:
```json
[
  {"id": 1, "name": "python", "note_count": 12, "image_count": 3},
  {"id": 2, "name": "meeting", "note_count": 8, "image_count": 0},
  {"id": 3, "name": "project-alpha", "note_count": 5, "image_count": 2}
]
```

### Search Tags

```http
GET /search/tags?query=proj
Authorization: Bearer <token>
```

Uses fuzzy matching (trigrams) to find similar tags:

Response:
```json
[
  {"id": 3, "name": "project-alpha", "similarity": 0.8},
  {"id": 7, "name": "project-beta", "similarity": 0.75},
  {"id": 12, "name": "projects", "similarity": 0.6}
]
```

---

## Tag Creation

Tags are created automatically when first used:

```python
# Service logic (simplified)
def get_or_create_tag(db, name, owner_id):
    name = name.lower().strip()
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.commit()
    return tag
```

### Manual Creation

Create a tag explicitly:

```http
POST /tags/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "new-tag"
}
```

Returns existing tag if already exists (idempotent).

---

## Tag Associations

### Database Schema

```
notes ←→ note_tags ←→ tags
images ←→ image_tags ←→ tags
```

### Junction Tables

**note_tags:**
| Column | Type |
|--------|------|
| note_id | FK to notes |
| tag_id | FK to tags |
| created_at | DateTime |

**image_tags:**
| Column | Type |
|--------|------|
| image_id | FK to images |
| tag_id | FK to tags |
| created_at | DateTime |

---

## Filtering by Tags

### Notes with Tag

```http
GET /notes/?tag=python
Authorization: Bearer <token>
```

### Images with Tag

```http
GET /images/?tag=python
Authorization: Bearer <token>
```

### Multiple Tags (AND)

```http
GET /notes/?tags=python,machine-learning
Authorization: Bearer <token>
```

Returns notes that have ALL specified tags.

---

## AI Tag Extraction

### From Notes

When saving a note:
1. Content parsed for `#tagname` patterns
2. Tags extracted and normalized
3. Associations created
4. Removed tags disassociated

### From Images

When AI analyzes an image:
1. AI identifies relevant tags
2. Tags extracted from AI response
3. Tags created/associated automatically

### Example AI Tags

Image of a sunset might generate:
- `sunset`
- `nature`
- `landscape`
- `sky`
- `orange`

---

## Tag Statistics

### Per-Tag Counts

Each tag tracks:
- Number of associated notes
- Number of associated images
- Total usage count

### Most Used Tags

```http
GET /tags/?sort=usage&limit=10
Authorization: Bearer <token>
```

---

## API Endpoints

### Tag CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tags/` | List user tags |
| POST | `/tags/` | Create/get tag |

### Note Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notes/{id}/tags/{name}` | Add tag |
| DELETE | `/notes/{id}/tags/{id}` | Remove tag |

### Image Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/images/{id}/tags/{name}` | Add tag |
| DELETE | `/images/{id}/tags/{id}` | Remove tag |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/tags?query=X` | Fuzzy search |

---

## Important Note: Global Tags

**Tags are NOT filtered by owner_id in queries!**

This is intentional - tags are global entities. The per-user isolation happens at the junction table level (note_tags, image_tags).

```python
# CORRECT - Tag query
tag = db.query(Tag).filter(Tag.name == name).first()

# WRONG - Don't filter by owner
tag = db.query(Tag).filter(Tag.name == name, Tag.owner_id == user.id).first()
```

---

## Best Practices

### Naming Conventions

1. **Use lowercase** - System converts anyway
2. **Use hyphens for spaces** - `machine-learning` not `machinelearning`
3. **Be consistent** - Decide on singular/plural
4. **Be specific** - `python-web` better than just `programming`

### Organization Strategies

1. **Topic tags** - `machine-learning`, `web-development`
2. **Project tags** - `project-alpha`, `client-acme`
3. **Status tags** - `in-progress`, `completed`, `archived`
4. **Type tags** - `meeting`, `idea`, `reference`

### Avoid Tag Proliferation

1. **Review existing tags** before creating new ones
2. **Consolidate similar tags** periodically
3. **Use tag search** to find existing options
4. **Limit tags per item** - 3-7 is usually sufficient
