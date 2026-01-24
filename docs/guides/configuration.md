# Configuration Guide

This guide covers all configuration options for Mnemosyne.

---

## Environment Variables

Configuration is managed through environment variables, typically set in a `.env` file.

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://user:password@db:5432/ai_notes_db` | PostgreSQL connection string |
| `POSTGRES_USER` | `user` | Database username |
| `POSTGRES_PASSWORD` | `password` | Database password |
| `POSTGRES_DB` | `ai_notes_db` | Database name |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (generated) | JWT signing key - **must be changed in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT token expiration (24 hours) |
| `ALGORITHM` | `HS256` | JWT algorithm |

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `VISION_MODEL` | `llama3.2-vision:11b` | Model for image analysis |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Model for text embeddings |
| `CHAT_MODEL` | `llama3.2:3b` | Model for RAG chat |

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum image upload size |

---

## AI Model Configuration

### Selecting Vision Models

Edit the `VISION_MODEL` variable to change the image analysis model:

```bash
# Recommended - Best quality
VISION_MODEL=llama3.2-vision:11b

# Alternative - Faster, less accurate
VISION_MODEL=qwen2.5vl:7b-q4_K_M
```

### Model Memory Requirements

| Model | VRAM Required | Quality |
|-------|---------------|---------|
| llama3.2-vision:11b | 8GB+ | High |
| qwen2.5vl:7b-q4_K_M | 4GB+ | Medium |
| nomic-embed-text | 2GB | N/A (embeddings) |

### Downloading Models

Models are downloaded on first use or can be pre-downloaded:

```bash
docker-compose exec ollama ollama pull llama3.2-vision:11b
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose exec ollama ollama pull llama3.2:3b
```

---

## Rate Limiting

Rate limits protect the system from abuse. Configure in the backend settings:

### Default Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Registration | 5/hour |
| Login | 10/minute |
| Note Create/Update/Delete | 30/minute |
| Image Upload | 20/minute |
| Search | 20-30/minute |
| RAG Query | 20/minute |
| Graph Data | 30/minute |

### Adjusting Limits

Rate limits are defined in the router decorators. To modify, edit the relevant `router.py` file:

```python
@router.post("/", dependencies=[Depends(RateLimiter(times=50, seconds=60))])
async def create_note(...):
    ...
```

---

## Docker Configuration

### Resource Limits

Configure container resources in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### GPU Configuration

GPU access for Ollama is configured in `docker-compose.yml`:

```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

To disable GPU (CPU-only mode), remove the `deploy.resources.reservations.devices` section.

---

## Storage Configuration

### File Storage

Uploaded images are stored in a Docker volume:

```yaml
volumes:
  uploads:
    driver: local
```

To use external storage, mount a host directory:

```yaml
volumes:
  - /path/to/storage:/app/uploads
```

### Database Persistence

Database data persists in the `db_data` volume:

```yaml
volumes:
  db_data:
    driver: local
```

---

## Network Configuration

### Ports

Default port mappings:

| Service | Internal | External |
|---------|----------|----------|
| Frontend | 3000 | 3000 |
| Backend | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Ollama | 11434 | 11434 |

To change external ports, modify `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:3000"  # Access frontend on port 8080
```

### CORS Configuration

Configure allowed origins for cross-origin requests:

```bash
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## Celery Configuration

### Worker Settings

```python
# backend/app/core/celery_app.py
celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    task_time_limit=300,  # 5 minute timeout
)
```

### Scaling Workers

Run multiple workers for higher throughput:

```bash
docker-compose up -d --scale celery_worker=3
```

---

## Logging Configuration

### Log Levels

| Level | Description |
|-------|-------------|
| DEBUG | Detailed debugging information |
| INFO | General operational messages |
| WARNING | Warning messages |
| ERROR | Error messages |
| CRITICAL | Critical errors |

### Setting Log Level

```bash
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

---

## Production Configuration

### Security Checklist

1. **Change SECRET_KEY** - Generate a strong random key
2. **Disable DEBUG** - Set `DEBUG=false`
3. **Configure HTTPS** - Use a reverse proxy with SSL
4. **Restrict CORS** - Only allow your domain
5. **Change default passwords** - Database, Redis
6. **Enable rate limiting** - Protect against abuse

### Example Production `.env`

```bash
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://produser:securepassword@db:5432/mnemosyne
REDIS_URL=redis://:redispassword@redis:6379/0
CORS_ORIGINS=https://yourdomain.com
```

---

## Troubleshooting Configuration

### Environment Not Loading

Ensure `.env` file is in the project root and Docker Compose can read it:

```bash
docker-compose config
```

### Variable Not Taking Effect

Restart services after changing environment:

```bash
docker-compose down
docker-compose up -d
```

### Verifying Configuration

Check loaded configuration:

```bash
docker-compose exec backend env | grep -E "DATABASE|REDIS|OLLAMA"
```
