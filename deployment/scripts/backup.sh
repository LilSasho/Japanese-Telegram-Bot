#!/bin/bash
# Database backup script for Japanese Learning Bot
# Usage: ./backup.sh [backup-name]

set -euo pipefail

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
NAMESPACE="japanese-bot"
POD_SELECTOR="app=japanese-learning-bot"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-backup_${TIMESTAMP}}"

echo -e "${GREEN}💾 Starting database backup${NC}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Get the bot pod name
POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l ${POD_SELECTOR} -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD_NAME" ]; then
    echo "Error: No bot pod found"
    exit 1
fi

echo -e "${YELLOW}Found pod: ${POD_NAME}${NC}"

# Copy database from pod
echo -e "${YELLOW}Copying database...${NC}"
kubectl cp ${NAMESPACE}/${POD_NAME}:/app/data/japanese_bot.db "${BACKUP_DIR}/${BACKUP_NAME}.db"

# Compress backup
echo -e "${YELLOW}Compressing backup...${NC}"
gzip "${BACKUP_DIR}/${BACKUP_NAME}.db"

echo -e "${GREEN}✅ Backup complete: ${BACKUP_DIR}/${BACKUP_NAME}.db.gz${NC}"

# Optional: Upload to cloud storage
# aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.db.gz" s3://your-bucket/backups/
# gsutil cp "${BACKUP_DIR}/${BACKUP_NAME}.db.gz" gs://your-bucket/backups/

# Clean up old backups (keep last 30)
echo -e "${YELLOW}Cleaning old backups...${NC}"
cd "${BACKUP_DIR}"
ls -t *.db.gz | tail -n +31 | xargs -r rm

echo -e "${GREEN}🎉 Backup process complete${NC}"
