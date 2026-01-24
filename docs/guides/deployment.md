# Deployment Guide

Complete guide for deploying Mnemosyne in various environments.

---

## Deployment Options

| Environment | Use Case | Complexity |
|-------------|----------|------------|
| Development | Local testing | Low |
| Single Server | Small team/personal | Medium |
| Production | High availability | High |

---

## Development Deployment

### Prerequisites

- Docker Desktop installed
- 8GB+ RAM available
- 20GB+ disk space

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd mnemosyne

# Start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Ollama | http://localhost:11434 |

---

## Single Server Deployment

Suitable for personal use or small teams.

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8GB | 16GB+ |
| Storage | 50GB SSD | 100GB+ SSD |
| GPU | None | NVIDIA 8GB+ |

### Setup Steps

#### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Relogin for group changes
exit
```

#### 2. Configure Firewall

```bash
# Allow required ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### 3. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd mnemosyne

# Create production environment
cp .env.example .env
nano .env
```

#### 4. Update Environment

```bash
# .env production settings
SECRET_KEY=your-very-long-random-secret-key-minimum-32-chars
DEBUG=false
LOG_LEVEL=WARNING

# Database
POSTGRES_USER=mnemosyne_user
POSTGRES_PASSWORD=secure_database_password
POSTGRES_DB=mnemosyne_prod

# Redis
REDIS_PASSWORD=secure_redis_password

# CORS (your domain)
CORS_ORIGINS=https://yourdomain.com
```

#### 5. Start Services

```bash
docker-compose -f docker-compose.yml up -d --build
```

#### 6. Setup Reverse Proxy

Using Nginx:

```nginx
# /etc/nginx/sites-available/mnemosyne
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/mnemosyne /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

---

## Production Deployment

For high availability and scalability.

### Architecture

```
                    ┌─────────────┐
                    │ Load Balancer│
                    │  (HAProxy)   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │ Backend 1│    │ Backend 2│    │ Backend 3│
     └────┬─────┘    └────┬─────┘    └────┬─────┘
          └───────────────┼───────────────┘
                          ▼
            ┌─────────────────────────┐
            │   PostgreSQL Primary    │
            │   └── Read Replica(s)   │
            └─────────────────────────┘
```

### Database Setup

#### Primary PostgreSQL

```bash
# Create production database
docker exec -it db psql -U postgres

CREATE USER mnemosyne_app WITH PASSWORD 'secure_password';
CREATE DATABASE mnemosyne_prod OWNER mnemosyne_app;
GRANT ALL PRIVILEGES ON DATABASE mnemosyne_prod TO mnemosyne_app;

# Enable extensions
\c mnemosyne_prod
CREATE EXTENSION vector;
CREATE EXTENSION pg_trgm;
```

#### Backup Configuration

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/backups/postgres
DATE=$(date +%Y%m%d_%H%M%S)
docker exec db pg_dump -U postgres mnemosyne_prod | gzip > $BACKUP_DIR/mnemosyne_$DATE.sql.gz

# Keep 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

Add to cron:

```bash
0 2 * * * /path/to/backup.sh
```

### Redis Configuration

```bash
# redis.conf for production
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

### Scaling Celery Workers

```bash
# Scale workers based on load
docker-compose up -d --scale celery_worker=5
```

### Monitoring Setup

#### Health Check Endpoint

```bash
# Check all services
curl http://localhost:8000/health
```

#### Prometheus Metrics (Optional)

Add to backend:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: ankane/pgvector:v0.5.1
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 4G
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 512M
    restart: always

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - db
      - redis
      - ollama
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
    restart: always

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.core.celery_app worker -l info
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - db
      - redis
      - ollama
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    deploy:
      resources:
        limits:
          memory: 512M
    restart: always

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

---

## GPU Configuration

### NVIDIA Setup

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Memory Requirements

| Model | GPU VRAM |
|-------|----------|
| llama3.2-vision:11b | 8GB+ |
| qwen2.5vl:7b-q4_K_M | 4GB+ |
| nomic-embed-text | 2GB |

---

## Security Checklist

### Before Going Live

- [ ] Change all default passwords
- [ ] Generate secure SECRET_KEY (32+ chars)
- [ ] Enable HTTPS with valid certificate
- [ ] Configure CORS for your domain only
- [ ] Enable firewall, close unnecessary ports
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Enable rate limiting
- [ ] Disable DEBUG mode
- [ ] Review file permissions

### Ongoing Security

- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated
- [ ] Regularly rotate secrets
- [ ] Test backup restoration
- [ ] Review access logs

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs db

# Check resource usage
docker stats
```

### Database Connection Failed

```bash
# Test database connectivity
docker exec -it db pg_isready -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### Ollama Not Responding

```bash
# Check Ollama status
docker exec -it ollama ollama list

# Pull models manually
docker exec -it ollama ollama pull llama3.2-vision:11b
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Maintenance

### Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Cleaning Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune

# Clear Celery results (Redis)
docker exec redis redis-cli FLUSHDB
```

### Log Management

```bash
# Configure Docker log rotation
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

sudo systemctl restart docker
```
