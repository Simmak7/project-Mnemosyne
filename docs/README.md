# Mnemosyne Documentation

**Version:** 1.1.0-beta
**Last Updated:** February 2026

Welcome to the official documentation for Mnemosyne - an AI-Powered Note-Taking application with Image Recognition, PDF Document Management, Knowledge Graph, and Local AI capabilities.

---

## What is Mnemosyne?

Mnemosyne is a personal knowledge management system that combines traditional note-taking with cutting-edge AI capabilities. Named after the Greek goddess of memory, it helps you capture, organize, and retrieve your thoughts, images, and documents using artificial intelligence — all running 100% locally on your machine.

### Key Capabilities

- **Smart Note-Taking** - Rich text editor with wikilinks, hashtags, and automatic organization
- **AI Image Analysis** - Upload images and let AI generate descriptions, titles, and tags automatically
- **PDF Document Management** - Upload PDFs for AI enrichment, review workflow, and semantic search
- **Daily Journal** - Calendar-based journaling with mood tracking and AI insights
- **Knowledge Graph** - Visualize connections between your notes with communities and semantic edges
- **AI Chat (Dual Mode)** - NEXUS RAG retrieval and Brain AI companion with topic memory
- **Smart Buckets** - AI-powered clustering, orphan detection, and inbox management
- **Semantic Search** - Find notes, images, and documents by meaning, not just keywords

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
| [Authentication](./features/authentication.md) | User accounts, security, 2FA, session management |
| [Notes](./features/notes.md) | Creating and managing notes with wikilinks |
| [Images](./features/images.md) | Image upload and AI analysis |
| [Documents](./features/documents.md) | PDF upload, AI enrichment, and review workflow |
| [Journal](./features/journal.md) | Daily journal with calendar and mood tracking |
| [Tags](./features/tags.md) | Tag management and organization |
| [Search](./features/search.md) | Full-text and semantic search |
| [Knowledge Graph](./features/knowledge-graph.md) | Wikilinks, communities, and visualization |
| [Smart Buckets](./features/smart-buckets.md) | AI clustering and inbox |
| [AI Chat](./features/ai-chat.md) | NEXUS RAG and Brain AI companion |

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
| **Frontend** | React 18, TanStack Query, Tiptap Editor, D3.js |
| **Backend** | FastAPI, SQLAlchemy, Celery, Pydantic |
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

## Community

- [GitHub Repository](https://github.com/Simmak7/project-Mnemosyne)
- [Issue Tracker](https://github.com/Simmak7/project-Mnemosyne/issues)
- [Changelog](../CHANGELOG.md)
- [Security Policy](../SECURITY.md)

---

## License

Mnemosyne is open source software licensed under the [GNU Affero General Public License v3.0](../LICENSE).

---

*For support or feedback, please [open an issue](https://github.com/Simmak7/project-Mnemosyne/issues) on GitHub.*
