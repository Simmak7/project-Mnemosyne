# Mnemosyne - Application Overview

**Version:** 1.1.0
**Type:** AI-Powered Personal Knowledge Management System

---

## Executive Summary

Mnemosyne is a comprehensive personal knowledge management application that leverages artificial intelligence to help users capture, organize, and retrieve information. The application combines traditional note-taking with AI-powered image analysis, semantic search, and an intelligent chatbot that can answer questions about your personal knowledge base.

---

## Core Features

### 1. Smart Note-Taking

Mnemosyne provides a rich text editing experience with advanced organizational features:

- **Rich Text Editor** - Full-featured Tiptap-based editor supporting headings, lists, code blocks, and more
- **Wikilinks** - Connect notes using `[[Note Title]]` syntax for building a knowledge graph
- **Hashtags** - Organize notes with `#tags` that are automatically extracted and indexed
- **Automatic Slugs** - URL-friendly slugs generated from note titles
- **Backlinks** - See all notes that reference the current note

### 2. AI Image Analysis

Upload images and let AI do the heavy lifting:

- **Automatic Description** - AI generates detailed descriptions of image content
- **Title Extraction** - Smart title generation from AI analysis
- **Tag Suggestions** - Automatic tag extraction from image content
- **Note Generation** - Each image creates a linked note for easy organization
- **Blur Hash Placeholders** - Instant visual feedback while images load

**Supported AI Models:**
- llama3.2-vision:11b (recommended, 4.7GB)
- qwen2.5vl:7b-q4_K_M (experimental, 4GB)

### 3. Knowledge Graph

Visualize and navigate your knowledge network:

- **Force-Directed Graph** - Interactive visualization of note connections
- **Wikilink Navigation** - Click links to navigate between notes
- **Backlink Discovery** - Find notes that reference your current note
- **Orphan Detection** - Identify isolated notes without connections
- **Semantic Edges** - AI-computed similarity relationships (Phase 2+)

### 4. RAG-Powered Chat

Ask questions about your knowledge base:

- **Citation-Backed Answers** - Every response includes source references
- **Multi-Source Retrieval** - Combines semantic, full-text, and graph-based search
- **Conversation History** - Persistent chat sessions with context awareness
- **Streaming Responses** - Real-time AI responses via Server-Sent Events
- **Deep Linking** - Jump directly to source notes from citations

### 5. Smart Buckets

AI-powered organization tools:

- **AI Clusters** - K-means clustering groups similar notes automatically
- **Inbox** - Recent notes from the last 7 days
- **Orphans** - Notes with no wikilink connections
- **Daily Notes** - Automatic daily journal entries with templates

### 6. Semantic Search

Find information by meaning, not just keywords:

- **Full-Text Search** - PostgreSQL tsvector-based search with ranking
- **Semantic Search** - pgvector-powered similarity search using embeddings
- **Tag Search** - Fuzzy matching for tag discovery
- **Similar Notes** - Find notes related to any specific note
- **Unlinked Mentions** - Discover potential wikilink opportunities

---

## User Workflow

### Typical Usage Pattern

```
1. CAPTURE
   ├── Write notes with rich text editor
   ├── Upload images for AI analysis
   └── Create daily notes for journaling

2. ORGANIZE
   ├── Add [[wikilinks]] to connect ideas
   ├── Apply #hashtags for categorization
   └── Let AI cluster similar content

3. RETRIEVE
   ├── Search by keyword or meaning
   ├── Navigate the knowledge graph
   └── Ask questions via RAG chat

4. DISCOVER
   ├── Find orphaned notes
   ├── Explore AI clusters
   └── Review backlinks and connections
```

---

## Technical Highlights

### Architecture

Mnemosyne uses a **Fractal Feature-Based Architecture** where each feature is self-contained with its own:
- API endpoints (router)
- Business logic (service)
- Data models (schemas)
- Async tasks (Celery)

### Async Processing

Long-running AI operations never block the user interface:

```
User uploads image
    ↓ (instant response)
Task queued to Celery
    ↓ (background processing)
AI analyzes image (30-60s)
    ↓
Client polls for completion
    ↓
Results displayed
```

### Security

- JWT-based authentication
- Password hashing with bcrypt
- Optional TOTP-based 2FA
- Account lockout after failed attempts
- Rate limiting on all endpoints

### AI/ML Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vision Analysis | Ollama + llama3.2-vision | Image description |
| Text Embeddings | nomic-embed-text | Semantic search |
| Vector Storage | pgvector | Similarity queries |
| Chat | Ollama + various LLMs | RAG responses |

---

## System Requirements

### Minimum Requirements
- 8GB RAM
- 20GB disk space
- Docker and Docker Compose
- Modern web browser

### Recommended for AI Features
- 16GB+ RAM
- NVIDIA GPU with 8GB+ VRAM
- 50GB+ disk space for AI models
- CUDA support enabled

---

## Deployment Options

### Development (Default)
```bash
docker-compose up -d --build
```
All services run locally with hot-reload enabled.

### Production
Configure environment variables for:
- External database URL
- Redis cluster
- SSL/TLS certificates
- CORS origins
- Rate limit tuning

---

## Version History

### v1.1.0 (Current)
- Neural Glass design system
- RAG Chat with citations
- AI image analysis
- Knowledge graph visualization
- Smart Buckets
- Semantic search

### v1.0.0 (Initial)
- Basic note CRUD
- Image upload
- Tag management
- User authentication

---

## Roadmap

### Planned Features
- OAuth2 social login
- Mobile application
- Collaborative workspaces
- Export/import functionality
- Plugin system
- Advanced LoRA personalization

---

*Mnemosyne - Remember Everything*
