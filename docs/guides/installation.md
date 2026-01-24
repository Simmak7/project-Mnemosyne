# Installation Guide

This guide will walk you through installing and running Mnemosyne on your local machine.

---

## Prerequisites

Before installing Mnemosyne, ensure you have the following:

### Required Software
- **Docker** - Version 20.10 or later
- **Docker Compose** - Version 2.0 or later
- **Git** - For cloning the repository

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 8GB | 16GB+ |
| Disk Space | 20GB | 50GB+ |
| CPU | 4 cores | 8+ cores |
| GPU | None | NVIDIA with 8GB+ VRAM |

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI-Powered Note-Taking and Image Recognition Software
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your preferred settings (see [Configuration Guide](./configuration.md) for details).

### 3. Start Services

```bash
docker-compose up -d --build
```

This command will:
1. Build the backend and frontend images
2. Pull required images (PostgreSQL, Redis, Ollama)
3. Create necessary networks and volumes
4. Start all services

### 4. Wait for Initialization

The first startup may take several minutes as:
- Database schemas are created
- AI models are downloaded
- Dependencies are installed

Monitor progress with:
```bash
docker-compose logs -f
```

### 5. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS          PORTS
backend             Up              0.0.0.0:8000->8000/tcp
celery_worker       Up
db                  Up              0.0.0.0:5432->5432/tcp
frontend            Up              0.0.0.0:3000->3000/tcp
ollama              Up              0.0.0.0:11434->11434/tcp
redis               Up              0.0.0.0:6379->6379/tcp
```

### 6. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

---

## GPU Setup (Optional)

For faster AI processing, configure GPU support:

### NVIDIA GPU

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Verify installation:
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

3. GPU support is already configured in `docker-compose.yml` for Ollama

### AMD GPU

AMD GPU support requires additional configuration. Contact support for guidance.

---

## Downloading AI Models

After installation, download the required AI models:

### Vision Model (Required for Image Analysis)

```bash
docker-compose exec ollama ollama pull llama3.2-vision:11b
```

Or the lighter alternative:
```bash
docker-compose exec ollama ollama pull qwen2.5vl:7b-q4_K_M
```

### Embedding Model (Required for Search)

```bash
docker-compose exec ollama ollama pull nomic-embed-text
```

### Chat Model (Optional, for RAG Chat)

```bash
docker-compose exec ollama ollama pull llama3.2:3b
```

---

## Troubleshooting

### Services Won't Start

Check logs for specific service:
```bash
docker-compose logs backend
docker-compose logs db
```

Common issues:
- Port conflicts: Change ports in `.env`
- Memory issues: Increase Docker memory allocation
- Disk space: Ensure sufficient free space

### Database Connection Failed

Ensure PostgreSQL is healthy:
```bash
docker-compose exec db pg_isready
```

Reset database if needed:
```bash
docker-compose down -v
docker-compose up -d
```

### Ollama Models Not Loading

Check Ollama status:
```bash
docker-compose exec ollama ollama list
```

Manually pull models:
```bash
docker-compose exec ollama ollama pull llama3.2-vision:11b
```

### Frontend Not Loading

Check frontend logs:
```bash
docker-compose logs frontend
```

Clear browser cache and try incognito mode.

---

## Stopping and Restarting

### Stop Services
```bash
docker-compose stop
```

### Restart Services
```bash
docker-compose restart
```

### Complete Shutdown (Preserves Data)
```bash
docker-compose down
```

### Complete Reset (Removes All Data)
```bash
docker-compose down -v
```

---

## Updating

To update to a new version:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

---

## Next Steps

- [Quick Start Guide](./quick-start.md) - Get started with your first note
- [Configuration Guide](./configuration.md) - Customize your installation
