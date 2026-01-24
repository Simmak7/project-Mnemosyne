# Mnemosyne Documentation

**Version:** 1.1.0
**Last Updated:** January 2026

Welcome to the official documentation for Mnemosyne - an AI-Powered Note-Taking application with Image Recognition capabilities.

---

## What is Mnemosyne?

Mnemosyne is a personal knowledge management system that combines traditional note-taking with cutting-edge AI capabilities. Named after the Greek goddess of memory, it helps you capture, organize, and retrieve your thoughts and images using artificial intelligence.

### Key Capabilities

- **Smart Note-Taking** - Rich text editor with wikilinks, hashtags, and automatic organization
- **AI Image Analysis** - Upload images and let AI generate descriptions, titles, and tags automatically
- **Knowledge Graph** - Visualize connections between your notes using wikilinks
- **RAG-Powered Chat** - Ask questions about your knowledge base with citation-backed answers
- **Smart Buckets** - AI-powered clustering, daily notes, orphan detection, and inbox management
- **Semantic Search** - Find notes by meaning, not just keywords

---

## Documentation Index

### Getting Started
| Document | Description |
|----------|-------------|
| [Installation Guide](./guides/installation.md) | How to install and run Mnemosyne |
| [Quick Start](./guides/quick-start.md) | Get up and running in 5 minutes |
| [Configuration](./guides/configuration.md) | Environment variables and settings |

### Feature Documentation
| Feature | Description |
|---------|-------------|
| [Authentication](./features/authentication.md) | User accounts, security, 2FA |
| [Notes](./features/notes.md) | Creating and managing notes |
| [Images](./features/images.md) | Image upload and AI analysis |
| [Tags](./features/tags.md) | Tag management and organization |
| [Search](./features/search.md) | Full-text and semantic search |
| [Knowledge Graph](./features/knowledge-graph.md) | Wikilinks and visualization |
| [Smart Buckets](./features/smart-buckets.md) | AI clustering and daily notes |
| [RAG Chat](./features/rag-chat.md) | AI-powered Q&A with citations |

### Technical Reference
| Document | Description |
|----------|-------------|
| [API Reference](./api/README.md) | Complete REST API documentation |
| [Architecture](./technical/architecture.md) | System design and patterns |
| [Database Schema](./technical/database.md) | Data models and relationships |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18+, TanStack Query, Tiptap Editor |
| **Backend** | FastAPI, SQLAlchemy, Celery |
| **Database** | PostgreSQL with pgvector extension |
| **Cache/Queue** | Redis |
| **AI/ML** | Ollama (local LLM inference) |
| **Infrastructure** | Docker Compose |

---

## Quick Links

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Ollama API:** http://localhost:11434

---

## License

Mnemosyne is proprietary software. All rights reserved.

---

*For support or feedback, please contact the development team.*
