# Smart Buckets Feature

Smart Buckets provide AI-powered organization tools including automatic clustering, inbox management, orphan detection, and daily notes.

---

## Overview

Smart Buckets are dynamic views into your knowledge base:

| Bucket | Purpose |
|--------|---------|
| **AI Clusters** | Notes grouped by semantic similarity |
| **Inbox** | Recent notes for processing |
| **Orphans** | Notes without connections |
| **Daily Notes** | Automatic journal entries |

---

## AI Clusters

Automatically group similar notes using K-means clustering on semantic embeddings.

### How It Works

```
All user notes with embeddings
    ↓
K-means clustering (k=auto or specified)
    ↓
Each note assigned to a cluster
    ↓
Cluster labeled by representative terms
    ↓
Results cached in Redis (1 hour)
```

### Automatic K Selection

If not specified, k is calculated:
```
k = max(3, min(10, sqrt(n/2)))
```
Where n = number of notes with embeddings.

### Get Clusters

```http
GET /buckets/clusters?k=5
Authorization: Bearer <token>
```

Response:
```json
{
  "clusters": [
    {
      "id": 0,
      "label": "Machine Learning",
      "note_count": 12,
      "representative_terms": ["neural", "training", "model"],
      "coherence_score": 0.85
    },
    {
      "id": 1,
      "label": "Project Management",
      "note_count": 8,
      "representative_terms": ["sprint", "deadline", "tasks"],
      "coherence_score": 0.78
    }
  ],
  "total_notes": 45,
  "unclustered": 5
}
```

### Get Cluster Notes

```http
GET /buckets/clusters/{cluster_id}/notes
Authorization: Bearer <token>
```

Response:
```json
{
  "cluster_id": 0,
  "label": "Machine Learning",
  "notes": [
    {"id": 1, "title": "Neural Network Basics", "similarity": 0.92},
    {"id": 5, "title": "Training Strategies", "similarity": 0.88},
    {"id": 12, "title": "Model Evaluation", "similarity": 0.85}
  ]
}
```

### Cache Management

Clusters are cached for performance:
- **Cache duration:** 1 hour
- **Cache key:** `clusters:{user_id}:{k}`

Invalidate cache manually:

```http
POST /buckets/clusters/invalidate-cache
Authorization: Bearer <token>
```

**Rate limit:** 5 per minute

---

## Inbox

Recent notes that may need processing or organization.

### Default Behavior

Returns notes created in the last 7 days.

### Get Inbox

```http
GET /buckets/inbox?days=7
Authorization: Bearer <token>
```

Response:
```json
{
  "notes": [
    {
      "id": 45,
      "title": "Meeting Notes",
      "created_at": "2024-01-15T10:00:00Z",
      "tag_count": 0,
      "wikilink_count": 0
    }
  ],
  "total": 12,
  "days": 7
}
```

### Inbox Indicators

Notes in inbox show:
- **Tag count** - How many tags assigned
- **Wikilink count** - How many connections
- **Age** - Days since creation

Use these to prioritize organization.

---

## Orphans

Notes with no wikilink connections (neither outgoing nor incoming).

### Why Track Orphans?

Orphaned notes:
- May be forgotten
- Could be integrated into your graph
- Might need wikilinks added
- Could be candidates for deletion

### Get Orphans

```http
GET /buckets/orphans
Authorization: Bearer <token>
```

Response:
```json
{
  "notes": [
    {
      "id": 23,
      "title": "Random Thought",
      "created_at": "2024-01-10T15:00:00Z",
      "tag_count": 2,
      "word_count": 150
    }
  ],
  "total": 8
}
```

### Orphan Resolution

For each orphan, consider:
1. **Add wikilinks** - Connect to related notes
2. **Add to existing note** - Merge content
3. **Delete** - If no longer relevant
4. **Leave as is** - Some notes are standalone

---

## Daily Notes

Automatic journal entries for daily capture.

### Daily Note Template

```markdown
# {Day}, {Month} {Day}, {Year}

## Morning Notes

## Tasks
- [ ]

## Evening Reflection

---
#daily-note
```

### Get/Create Today's Note

```http
POST /buckets/daily/today
Authorization: Bearer <token>
```

Response:
```json
{
  "id": 100,
  "title": "Wednesday, January 15, 2024",
  "content": "...",
  "is_new": true,
  "date": "2024-01-15"
}
```

If today's note exists, returns existing. Otherwise creates new.

### Get Note by Date

```http
GET /buckets/daily/2024-01-10
Authorization: Bearer <token>
```

Returns the daily note for that specific date, or 404 if not found.

### List Recent Daily Notes

```http
GET /buckets/daily?limit=30
Authorization: Bearer <token>
```

Response:
```json
{
  "notes": [
    {"id": 100, "date": "2024-01-15", "title": "Wednesday, January 15, 2024"},
    {"id": 95, "date": "2024-01-14", "title": "Tuesday, January 14, 2024"},
    {"id": 90, "date": "2024-01-13", "title": "Monday, January 13, 2024"}
  ],
  "total": 30
}
```

### Daily Note Features

- **Auto-tagged** - `#daily-note` added automatically
- **Consistent format** - Same template every day
- **Quick capture** - Jump to today's note instantly
- **Chronological** - Easy to review past days

---

## API Endpoints

### Clusters

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/buckets/clusters` | Get AI clusters | 10/min |
| GET | `/buckets/clusters/{id}/notes` | Get cluster notes | 30/min |
| POST | `/buckets/clusters/invalidate-cache` | Clear cache | 5/min |

### Inbox

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/buckets/inbox` | Get recent notes | 30/min |

### Orphans

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/buckets/orphans` | Get unlinked notes | 30/min |

### Daily Notes

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/buckets/daily` | List daily notes | 30/min |
| POST | `/buckets/daily/today` | Get/create today | 30/min |
| GET | `/buckets/daily/{date}` | Get by date | 30/min |

---

## Clustering Algorithm

### K-Means Process

1. **Collect embeddings** - Get all notes with valid embeddings
2. **Normalize vectors** - L2 normalization for cosine similarity
3. **Initialize centroids** - K-means++ initialization
4. **Iterate** - Assign notes, update centroids
5. **Converge** - Stop when stable or max iterations

### Cluster Labeling

Labels generated from:
1. Most common words in cluster notes
2. TF-IDF weighted terms
3. Exclusion of stop words

### Coherence Score

Measures cluster quality (0-1):
- **> 0.8** - Highly coherent
- **0.6-0.8** - Good
- **0.4-0.6** - Moderate
- **< 0.4** - Weak clustering

---

## Best Practices

### AI Clusters

1. **Experiment with k** - Try different values
2. **Review periodically** - Clusters evolve with content
3. **Use for discovery** - Find unexpected connections
4. **Don't over-rely** - AI isn't perfect

### Inbox Management

1. **Process regularly** - Daily or weekly review
2. **Add connections** - Wikilinks and tags
3. **Customize timeframe** - Adjust days parameter
4. **Zero inbox goal** - Keep it manageable

### Orphan Review

1. **Regular audits** - Monthly orphan review
2. **Connect or delete** - Don't let orphans accumulate
3. **Consider purpose** - Some notes are intentionally standalone
4. **Batch processing** - Handle multiple at once

### Daily Notes

1. **Consistent habit** - Same time each day
2. **Quick capture** - Don't overthink it
3. **Link as you go** - Add wikilinks to related notes
4. **Review weekly** - Extract insights to permanent notes
