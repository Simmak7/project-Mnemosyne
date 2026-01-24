# Mnemosyne

**AI-Powered Note-Taking with Image Recognition**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.ai/)

---

Mnemosyne is a personal knowledge management system that combines traditional note-taking with cutting-edge AI capabilities. Named after the Greek goddess of memory, it helps you capture, organize, and retrieve your thoughts and images using artificial intelligence.

## Features

### Smart Note-Taking
- Rich text editor with Tiptap
- **Wikilinks** - Connect notes with `[[Note Title]]` syntax
- **Hashtags** - Organize with `#tags` that are automatically indexed
- **Backlinks** - See all notes referencing the current note

### AI Image Analysis
- Upload images and get automatic descriptions, titles, and tags
- Powered by local vision models (llama3.2-vision, qwen2.5vl)
- Each image creates a linked note for organization

### Knowledge Graph
- Interactive force-directed graph visualization
- Navigate connections between notes
- Discover orphaned and isolated content

### RAG-Powered Chat
- Ask questions about your knowledge base
- Citation-backed answers with source references
- Streaming responses with conversation history

### Smart Buckets
- **AI Clusters** - K-means clustering groups similar notes
- **Inbox** - Recent notes from the last 7 days
- **Orphans** - Notes without connections
- **Daily Notes** - Automatic journal entries

### Semantic Search
- Full-text search with PostgreSQL tsvector
- Vector similarity search with pgvector
- Find notes by meaning, not just keywords

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (16GB recommended for AI features)
- NVIDIA GPU with CUDA support (optional, for faster AI)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mnemosyne.git
   cd mnemosyne
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the application**
   ```bash
   docker-compose up -d --build
   ```

4. **Pull AI models** (first time only)
   ```bash
   docker exec -it ollama ollama pull llama3.2-vision:11b
   docker exec -it ollama ollama pull nomic-embed-text
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TanStack Query, Tiptap Editor, D3.js |
| **Backend** | FastAPI, SQLAlchemy, Celery, Pydantic |
| **Database** | PostgreSQL + pgvector extension |
| **Cache/Queue** | Redis |
| **AI/ML** | Ollama (local LLM inference) |
| **Infrastructure** | Docker Compose |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│                    React + TanStack Query                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
┌─────────────────────────▼───────────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Auth   │  │  Notes  │  │ Images  │  │   RAG   │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼─────────────┐
│                        Services                             │
│  PostgreSQL (pgvector)  │  Redis  │  Celery  │  Ollama    │
└─────────────────────────────────────────────────────────────┘
```

## Documentation

Detailed documentation is available in the [`/docs`](./docs) folder:

- [Installation Guide](./docs/guides/installation.md)
- [Quick Start](./docs/guides/quick-start.md)
- [Configuration](./docs/guides/configuration.md)
- [API Reference](./docs/api/README.md)
- [Architecture](./docs/technical/architecture.md)

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://ollama:11434` |
| `SECRET_KEY` | JWT signing key | (required) |
| `VISION_MODEL` | Model for image analysis | `llama3.2-vision:11b` |

See [`.env.example`](./.env.example) for all options.

## System Requirements

### Minimum
- 8GB RAM
- 20GB disk space
- Docker and Docker Compose

### Recommended (for AI features)
- 16GB+ RAM
- NVIDIA GPU with 8GB+ VRAM
- 50GB+ disk space for AI models
- CUDA support enabled

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

---

<p align="center">
  <strong>Mnemosyne</strong> - Remember Everything
</p>
