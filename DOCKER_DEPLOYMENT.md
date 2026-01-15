# Docker Production Deployment Guide

## Overview
Complete Docker setup for Nexaway with PostgreSQL + Flask API using Gunicorn.

## Architecture
```
┌─────────────────────────────────────┐
│     Docker Network (nexaway)        │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │  PostgreSQL  │  │  Flask API  │ │
│  │  Port 5432   │  │  Port 8000  │ │
│  └──────────────┘  └─────────────┘ │
│       nexaway_db      nexaway_api   │
│                                     │
└─────────────────────────────────────┘
```

## Files Included
- **Dockerfile** - Flask app with Gunicorn (3 workers)
- **docker-compose.yml** - DB + API services with health checks
- **.dockerignore** - Excludes unnecessary files from image
- **wsgi.py** - WSGI entry point for Gunicorn
- **.env.example** - Environment variables template

## Quick Start

### 1. Build & Run Locally
```bash
# Build images and start services
docker-compose up --build -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f db
```

### 2. Database Setup
```bash
# Create tables (automatic on startup)
docker-compose exec api python -c "from app import create_app, db; create_app().app_context().push(); db.create_all()"

# Seed data (optional)
docker-compose exec api python seed.py
```

### 3. Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Example API calls
curl http://localhost:8000/v1/external/currency?base=TND&targets=USD,EUR
curl http://localhost:8000/living-cost/Cairo

# Swagger documentation
curl http://localhost:8000/swagger
```

### 4. Stop Services
```bash
docker-compose down

# Remove data (caution!)
docker-compose down -v
```

## Production Deployment

### Environment Variables
Copy `.env.example` to `.env` and update:
```bash
SECRET_KEY=<generate-random-key>
JWT_SECRET_KEY=<generate-random-key>
RAPIDAPI_KEY=<your-rapidapi-key>
```

### Docker Compose Override (Production)
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'
services:
  api:
    environment:
      - FLASK_ENV=production
    restart: always
    deploy:
      replicas: 3  # Multiple instances
```

Run: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

### Render Deployment
1. Push to GitHub:
   ```bash
   git add .
   git commit -m "Docker production setup"
   git push origin main
   ```

2. Connect Render:
   - Go to Render dashboard
   - New → Web Service
   - Connect GitHub repo
   - Select `Dockerfile` as runtime
   - Set environment variables from `.env`
   - Deploy!

### GitHub Actions CI/CD (Optional)
Create `.github/workflows/docker.yml`:
```yaml
name: Docker Build & Push
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/setup-buildx-action@v1
      - uses: docker/build-push-action@v2
        with:
          push: true
          tags: nexaway:latest
```

## Configuration Reference

### Database
- **Type**: PostgreSQL 15
- **Host**: db (Docker network)
- **Port**: 5432
- **Database**: nexaway_prod
- **User**: nexaway
- **Password**: supersecret2026 (change in production!)

### Flask
- **Workers**: 3 (Gunicorn)
- **Bind**: 0.0.0.0:8000
- **Timeout**: 60s
- **Max Requests**: 1000

### Health Checks
- API: `GET /health`
- Database: `pg_isready`
- Interval: 30s
- Timeout: 10s
- Retries: 3

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs api

# Rebuild from scratch
docker-compose down
docker system prune -a
docker-compose up --build
```

### Database connection error
```bash
# Verify database is healthy
docker-compose exec db pg_isready -U nexaway

# Check network
docker network inspect nexaway_nexaway_network
```

### Port already in use
```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Permission errors
```bash
# Run with sudo
sudo docker-compose up -d

# Or adjust Docker permissions
sudo usermod -aG docker $USER
```

## Performance Optimization

### Database Connection Pooling
Update `app/extensions.py`:
```python
engine_options = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
db = SQLAlchemy(engine_options=engine_options)
```

### Caching
Configure Redis (optional):
```yaml
cache:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

### Load Balancing
Use Nginx reverse proxy:
```yaml
nginx:
  image: nginx:latest
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

## Monitoring

### Real-time Logs
```bash
docker-compose logs -f api
docker-compose logs -f db
```

### Container Stats
```bash
docker stats
```

### Database Monitoring
```bash
docker-compose exec db psql -U nexaway -d nexaway_prod -c "\l"
```

## Scaling

### Horizontal Scaling (Multiple Replicas)
```yaml
api:
  deploy:
    replicas: 3
```

### Vertical Scaling (More Resources)
```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

## Security Checklist
- [ ] Change default PostgreSQL password
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Regular backups of postgres_data volume
- [ ] Monitor API logs for suspicious activity
- [ ] Keep dependencies updated

## Backup & Restore

### Backup Database
```bash
docker-compose exec db pg_dump -U nexaway nexaway_prod > backup.sql
```

### Restore Database
```bash
docker-compose exec -T db psql -U nexaway nexaway_prod < backup.sql
```

## Updates

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
docker-compose up --build
```

### Zero-Downtime Deployment
```bash
# Build new image
docker-compose build

# Recreate containers without stopping
docker-compose up -d
```

## Additional Resources
- [Docker Docs](https://docs.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file)
- [Gunicorn Documentation](https://gunicorn.org)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Render Documentation](https://render.com/docs)
