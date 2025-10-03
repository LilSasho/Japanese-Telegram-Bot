# 🚀 Deployment Guide - Japanese Learning Telegram Bot

This directory contains all deployment configurations and automation scripts for production deployment of the Japanese Learning Telegram Bot.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Deployment Scripts](#deployment-scripts)
- [Production Checklist](#production-checklist)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Start

### Prerequisites

- Docker 20.10+
- Kubernetes 1.24+ (for production)
- kubectl configured
- Telegram Bot Token (from @BotFather)

### Local Docker Deployment

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env and add your BOT_TOKEN

# 2. Start with Docker Compose
cd deployment/docker
docker-compose up -d

# 3. View logs
docker-compose logs -f bot

# 4. Stop
docker-compose down
```

---

## 🐳 Docker Deployment

### Build Image

```bash
# Build locally
docker build -t japanese-learning-bot:latest -f deployment/docker/Dockerfile .

# Or use docker-compose
cd deployment/docker
docker-compose build
```

### Run Container

```bash
# With docker-compose (recommended)
docker-compose up -d

# Or manually
docker run -d \
  --name japanese-bot \
  --env-file .env \
  -v bot-data:/app/data \
  --restart unless-stopped \
  japanese-learning-bot:latest
```

### Configuration

The bot uses environment variables from `.env`:

```env
# Required
BOT_TOKEN=your_telegram_bot_token_here

# Database (default: SQLite)
DATABASE_URL=sqlite:///app/data/japanese_bot.db

# Learning Settings
LESSON_SIZE=5
MIN_REVIEW_INTERVAL=1
MAX_REVIEW_INTERVAL=365
DAILY_REVIEW_LIMIT=50

# Features
ENABLE_REMINDERS=true
ENABLE_STREAKS=true
ENABLE_QUIZ=true
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

1. **Kubernetes Cluster** (1.24+)
2. **kubectl** configured to access your cluster
3. **Docker Registry** access
4. **Bot Token** from @BotFather

### Deployment Steps

#### 1. Configure Secrets

**Important:** Update the secret with your actual bot token before deploying!

```bash
# Edit the secret file
vi deployment/kubernetes/secret.yaml

# Replace YOUR_TELEGRAM_BOT_TOKEN_HERE with your actual token
```

#### 2. Build and Push Image

```bash
# Set your registry
export DOCKER_REGISTRY=your-registry.example.com

# Build image
docker build -t ${DOCKER_REGISTRY}/japanese-learning-bot:v1.0 -f deployment/docker/Dockerfile .

# Push to registry
docker push ${DOCKER_REGISTRY}/japanese-learning-bot:v1.0
```

#### 3. Update Deployment Manifest

Edit `deployment/kubernetes/deployment.yaml` and update the image:

```yaml
containers:
- name: bot
  image: your-registry.example.com/japanese-learning-bot:v1.0  # Update this
```

#### 4. Deploy to Kubernetes

```bash
# Using the automated script (recommended)
cd deployment/scripts
./deploy.sh production v1.0

# Or manually
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/secret.yaml
kubectl apply -f deployment/kubernetes/pvc.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
```

#### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n japanese-bot

# View logs
kubectl logs -f deployment/japanese-learning-bot -n japanese-bot

# Check deployment health
kubectl get deployment japanese-learning-bot -n japanese-bot
```

### Kubernetes Architecture

```
┌─────────────────────────────────────┐
│     japanese-bot namespace          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   japanese-learning-bot      │  │
│  │   (Deployment, 1 replica)    │  │
│  │                              │  │
│  │  - Bot Container             │  │
│  │  - Resource Limits           │  │
│  │  - Health Checks             │  │
│  └──────────────────────────────┘  │
│           │                         │
│           │ mounts                  │
│           ▼                         │
│  ┌──────────────────────────────┐  │
│  │   bot-data-pvc              │  │
│  │   (1Gi PersistentVolume)     │  │
│  │   - SQLite database          │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   ConfigMap & Secrets        │  │
│  │   - Bot configuration        │  │
│  │   - Sensitive credentials    │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

The bot exposes metrics at `/metrics` (port 8000) for Prometheus scraping.

**Deploy Prometheus:**

```bash
# Apply Prometheus configuration
kubectl create configmap prometheus-config \
  --from-file=monitoring/prometheus/config.yml \
  -n japanese-bot

# Apply alerting rules
kubectl create configmap prometheus-alerts \
  --from-file=monitoring/alerts/rules.yml \
  -n japanese-bot

# Deploy Prometheus (using Helm)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus \
  --namespace japanese-bot \
  --values monitoring/prometheus-values.yaml
```

### Grafana Dashboards

1. **Access Grafana:**
   ```bash
   kubectl port-forward svc/grafana 3000:3000 -n japanese-bot
   # Visit http://localhost:3000
   ```

2. **Import Dashboard:**
   - Go to Dashboards → Import
   - Upload `monitoring/grafana/dashboards/bot-overview.json`

### Key Metrics

- `bot_messages_processed_total` - Total messages handled
- `bot_reviews_completed_total` - Reviews completed by users
- `bot_errors_total` - Error count
- `bot_daily_active_users` - Active users in 24h
- `bot_database_query_duration_seconds` - DB query latency

### Alerts

Configured alerts in `monitoring/alerts/rules.yml`:

- **BotDown** - Bot instance is unreachable
- **HighErrorRate** - Error rate > 0.1/sec
- **HighMemoryUsage** - Memory > 80%
- **DatabaseConnectionFailures** - DB connection issues
- **TelegramRateLimitHit** - API rate limiting detected

---

## 🛠 Deployment Scripts

### `deploy.sh`

Full deployment automation:

```bash
cd deployment/scripts

# Deploy to production
./deploy.sh production v1.0

# The script will:
# 1. Build Docker image
# 2. Push to registry
# 3. Apply Kubernetes manifests
# 4. Wait for rollout
# 5. Show status
```

### `backup.sh`

Database backup automation:

```bash
cd deployment/scripts

# Create backup
./backup.sh

# Create named backup
./backup.sh my-backup-name

# Backups are stored in ./backups/ and compressed
# Old backups are automatically cleaned (keeps last 30)
```

### `rollback.sh`

Quick rollback to previous version:

```bash
cd deployment/scripts

# Rollback to previous version
./rollback.sh last

# Rollback to specific revision
./rollback.sh 3
```

---

## ✅ Production Checklist

Before deploying to production:

### Security
- [ ] Update `BOT_TOKEN` in `secret.yaml` with real token
- [ ] Never commit secrets to version control
- [ ] Use external secrets management (Vault, AWS Secrets Manager)
- [ ] Enable RBAC and network policies
- [ ] Run container as non-root user (already configured)

### Configuration
- [ ] Set correct `DATABASE_URL` for production
- [ ] Configure resource limits based on load
- [ ] Set up persistent volume backups
- [ ] Configure log aggregation
- [ ] Set proper timezone settings

### Monitoring
- [ ] Deploy Prometheus and Grafana
- [ ] Configure alerting rules
- [ ] Set up notification channels (Slack, Email, PagerDuty)
- [ ] Create dashboards for key metrics
- [ ] Set up log monitoring

### High Availability
- [ ] **Note:** Telegram bots must run as single instance
- [ ] Set up database replication (if using PostgreSQL)
- [ ] Configure pod disruption budgets
- [ ] Implement automated backups
- [ ] Test disaster recovery procedures

### Performance
- [ ] Load test bot with expected traffic
- [ ] Optimize database queries
- [ ] Configure Redis caching
- [ ] Set appropriate resource limits
- [ ] Monitor memory usage over time

---

## 🔧 Troubleshooting

### Bot Not Starting

```bash
# Check pod logs
kubectl logs -f deployment/japanese-learning-bot -n japanese-bot

# Check pod events
kubectl describe pod -l app=japanese-learning-bot -n japanese-bot

# Common issues:
# - Invalid BOT_TOKEN
# - Database connection failure
# - Missing secrets or configmaps
```

### High Memory Usage

```bash
# Check current memory
kubectl top pods -n japanese-bot

# Increase memory limits in deployment.yaml:
resources:
  limits:
    memory: "1Gi"  # Increase from 512Mi
```

### Database Issues

```bash
# Check database file permissions
kubectl exec -it deployment/japanese-learning-bot -n japanese-bot -- \
  ls -la /app/data/

# Backup and restore database
./deployment/scripts/backup.sh
```

### Telegram API Rate Limiting

```bash
# Check rate limit metrics
kubectl logs deployment/japanese-learning-bot -n japanese-bot | grep rate_limit

# Solution: Implement exponential backoff (already in code)
# Monitor with alert: TelegramRateLimitHit
```

### Rolling Back Deployment

```bash
# Quick rollback
./deployment/scripts/rollback.sh last

# Or view history and choose version
kubectl rollout history deployment/japanese-learning-bot -n japanese-bot
./deployment/scripts/rollback.sh 3
```

---

## 📚 Additional Resources

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Prometheus Operator](https://prometheus-operator.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 🆘 Support

For issues or questions:

1. Check logs: `kubectl logs -f deployment/japanese-learning-bot -n japanese-bot`
2. Review metrics in Grafana
3. Check GitHub issues
4. Contact the development team

---

**Last Updated:** 2025-10-03
**Version:** 1.0.0
