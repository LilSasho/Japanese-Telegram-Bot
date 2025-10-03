#!/bin/bash
# Rollback script for Japanese Learning Bot
# Usage: ./rollback.sh [revision-number]

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
NAMESPACE="japanese-bot"
DEPLOYMENT_NAME="japanese-learning-bot"
REVISION="${1:-}"

echo -e "${YELLOW}🔄 Rollback Manager for Japanese Learning Bot${NC}"
echo ""

# Show rollout history
echo -e "${YELLOW}📜 Deployment History:${NC}"
kubectl rollout history deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}
echo ""

# If no revision specified, ask user
if [ -z "$REVISION" ]; then
    read -p "Enter revision number to rollback to (or 'last' for previous): " REVISION
fi

# Perform rollback
if [ "$REVISION" = "last" ]; then
    echo -e "${YELLOW}⏪ Rolling back to previous revision...${NC}"
    kubectl rollout undo deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}
else
    echo -e "${YELLOW}⏪ Rolling back to revision ${REVISION}...${NC}"
    kubectl rollout undo deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --to-revision=${REVISION}
fi

# Wait for rollback to complete
echo -e "${YELLOW}⏳ Waiting for rollback to complete...${NC}"
kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=5m

# Show status
echo ""
echo -e "${GREEN}✅ Rollback complete!${NC}"
echo -e "${YELLOW}📊 Current Status:${NC}"
kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME}

echo ""
echo -e "${GREEN}🎉 Deployment rolled back successfully${NC}"
