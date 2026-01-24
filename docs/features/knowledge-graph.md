# Knowledge Graph Feature

The knowledge graph visualizes connections between your notes, tags, and images, enabling discovery and navigation of your knowledge base.

---

## Overview

The knowledge graph represents your knowledge as:
- **Nodes** - Notes, tags, images
- **Edges** - Wikilinks, tag associations, image links

This network view reveals patterns and connections that aren't visible in linear note lists.

---

## Wikilinks

Wikilinks are the primary mechanism for creating graph connections.

### Syntax

| Format | Example | Description |
|--------|---------|-------------|
| Basic | `[[Note Title]]` | Link to note by title |
| Aliased | `[[Note Title\|display]]` | Custom display text |
| Slug-based | `[[note-title]]` | Link by URL slug |

### Creating Links

In the editor, type `[[` to trigger autocomplete:

1. Start typing `[[`
2. Note suggestions appear
3. Select note or continue typing
4. Close with `]]`

### Link Resolution

When rendering content:
```
1. Parse [[...]] patterns
2. Extract title/slug
3. Look up note in database
4. If found → render as link
5. If not found → render as "stub" (offers creation)
```

### Creating Stub Notes

For unresolved links:

```http
POST /wikilinks/create-stub
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New Note Title"
}
```

Creates a new note with just the title, ready for content.

---

## Backlinks

Backlinks show which notes reference the current note.

### Finding Backlinks

```http
GET /notes/{id}/backlinks
Authorization: Bearer <token>
```

Response:
```json
{
  "backlinks": [
    {
      "id": 45,
      "title": "Meeting Notes",
      "context": "...discussed the [[Current Note]] approach...",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 5
}
```

### Use Cases

- **Impact analysis** - Who references this note?
- **Navigation** - Jump to related notes
- **Orphan prevention** - Notes with backlinks aren't orphans

---

## Graph Data Structure

### Node Types

| Type | Description | Visual |
|------|-------------|--------|
| `note` | User note | Circle |
| `tag` | Tag entity | Diamond |
| `image` | Image | Square |
| `entity` | Extracted entity | Triangle |

### Edge Types

| Type | Weight | Description |
|------|--------|-------------|
| `wikilink` | 1.0 | Explicit `[[link]]` |
| `tag` | 0.7 | Shared tag connection |
| `image` | 0.6 | Image-note link |
| `semantic` | 0.3-0.9 | AI-computed similarity |
| `session` | 0.2 | Co-viewed in session |

---

## Graph API

### Full Graph

Get the entire knowledge graph:

```http
GET /graph/data
Authorization: Bearer <token>
```

Response:
```json
{
  "nodes": [
    {"id": "note-1", "type": "note", "label": "Machine Learning", "size": 12},
    {"id": "note-2", "type": "note", "label": "Neural Networks", "size": 8},
    {"id": "tag-ml", "type": "tag", "label": "#machine-learning", "size": 5}
  ],
  "edges": [
    {"source": "note-1", "target": "note-2", "type": "wikilink", "weight": 1.0},
    {"source": "note-1", "target": "tag-ml", "type": "tag", "weight": 0.7}
  ],
  "stats": {
    "node_count": 150,
    "edge_count": 320,
    "density": 0.028
  }
}
```

### Local Neighborhood

Get graph around a specific node:

```http
GET /graph/local?nodeId=note-1&depth=2
Authorization: Bearer <token>
```

Parameters:
- `nodeId` - Center node ID
- `depth` - Hops from center (1-3)

### Clustered Map View

Get clustered overview:

```http
GET /graph/map
Authorization: Bearer <token>
```

Returns community-clustered graph for overview visualization.

### Path Finding

Find path between two nodes:

```http
GET /graph/path?from=note-1&to=note-50
Authorization: Bearer <token>
```

Response:
```json
{
  "path": ["note-1", "note-12", "note-34", "note-50"],
  "length": 3,
  "edges": [
    {"source": "note-1", "target": "note-12", "type": "wikilink"},
    {"source": "note-12", "target": "note-34", "type": "tag"},
    {"source": "note-34", "target": "note-50", "type": "wikilink"}
  ]
}
```

### Graph Search

Autocomplete for node names:

```http
GET /graph/search?q=machine
Authorization: Bearer <token>
```

### Graph Statistics

```http
GET /graph/stats
Authorization: Bearer <token>
```

Response:
```json
{
  "total_nodes": 150,
  "total_edges": 320,
  "notes": 120,
  "tags": 25,
  "images": 5,
  "avg_connections": 2.13,
  "max_connections": 15,
  "orphan_count": 8,
  "density": 0.028,
  "communities": 12
}
```

---

## Semantic Edges

AI-computed similarity connections (Phase 2+).

### Generation

```http
POST /graph/semantic/rebuild
Authorization: Bearer <token>
```

Process:
1. Load all note embeddings
2. Compute pairwise similarities
3. Create edges above threshold (0.7)
4. Store in semantic_edges table

### Statistics

```http
GET /graph/semantic/stats
Authorization: Bearer <token>
```

---

## Community Detection

Automatic clustering using Louvain algorithm.

### Rebuild Communities

```http
POST /graph/communities/rebuild
Authorization: Bearer <token>
```

Process:
1. Build NetworkX graph from edges
2. Run Louvain/Leiden algorithm
3. Assign community IDs to nodes
4. Store in community_metadata table

### Community Benefits

- **Overview** - See high-level structure
- **Navigation** - Browse by topic area
- **Discovery** - Find related content clusters

---

## Visualization

### Force-Directed Layout

The frontend uses force-directed simulation:

- **Attraction** - Linked nodes pull together
- **Repulsion** - All nodes push apart
- **Centering** - Graph stays centered
- **Stabilization** - Animation settles over time

### Visual Encoding

| Attribute | Meaning |
|-----------|---------|
| Node size | Connection count |
| Node color | Type (note, tag, image) |
| Edge thickness | Weight |
| Edge style | Type (solid=wikilink, dashed=semantic) |

### Controls

| Action | Result |
|--------|--------|
| Click node | Select, show details |
| Double-click | Navigate to note |
| Drag node | Reposition |
| Scroll | Zoom |
| Drag background | Pan |

---

## API Endpoints

### Graph Data

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/graph/data` | Full graph | 30/min |
| GET | `/graph/local` | Local neighborhood | 30/min |
| GET | `/graph/map` | Clustered view | 30/min |
| GET | `/graph/path` | Path finder | 30/min |
| GET | `/graph/search` | Node autocomplete | 30/min |
| GET | `/graph/stats` | Statistics | 30/min |

### Wikilinks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/wikilinks/resolve` | Resolve link batch |
| POST | `/wikilinks/create-stub` | Create stub note |

### Semantic (Phase 2+)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/graph/semantic/rebuild` | Rebuild edges |
| POST | `/graph/communities/rebuild` | Rebuild clusters |
| GET | `/graph/semantic/stats` | Edge statistics |

---

## Note Graph View

Each note has a local graph view:

```http
GET /notes/{id}/graph?depth=2
Authorization: Bearer <token>
```

Shows:
- The note as center node
- Direct connections (depth 1)
- Extended connections (depth 2)
- Suggested connections (semantic)

---

## Orphan Notes

Notes with no graph connections:

### Finding Orphans

```http
GET /notes/orphaned/list
Authorization: Bearer <token>
```

### Most Linked

Find hub notes:

```http
GET /notes/most-linked
Authorization: Bearer <token>
```

---

## Best Practices

### Building a Good Graph

1. **Link liberally** - More connections = better discovery
2. **Use consistent titles** - Makes linking easier
3. **Review orphans** - Connect isolated notes
4. **Check backlinks** - Understand note relationships

### Wikilink Strategies

1. **Atomic notes** - One concept per note
2. **Descriptive titles** - Easy to find and link
3. **Bidirectional thinking** - Consider both directions
4. **Hub notes** - Create index notes for topics

### Graph Maintenance

1. **Regular review** - Check graph health periodically
2. **Prune dead links** - Fix broken wikilinks
3. **Add semantic edges** - Run rebuild periodically
4. **Review communities** - Understand your knowledge structure

---

## Graph Algorithms

### PageRank (Importance)

Identifies important hub notes based on link structure.

### Shortest Path

Finds minimum hops between any two notes.

### Community Detection

Groups related notes into clusters using modularity optimization.

### Centrality Measures

- **Degree** - Number of connections
- **Betweenness** - Bridge between communities
- **Closeness** - Average distance to all nodes
