#!/bin/bash
# Deployment script for Japanese Learning Telegram Bot
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
NAMESPACE="japanese-bot"
DEPLOYMENT_NAME="japanese-learning-bot"
DOCKER_IMAGE="${DOCKER_REGISTRY:-your-registry}/japanese-learning-bot"
VERSION="${2:-latest}"

echo -e "${GREEN}🚀 Deploying Japanese Learning Bot${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}Version: ${VERSION}${NC}"
echo ""

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ kubectl found${NC}"
}

# Function to check cluster connection
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Connected to cluster: $(kubectl config current-context)${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"

    cd "$(dirname "$0")/../.."

    docker build \
        -t "${DOCKER_IMAGE}:${VERSION}" \
        -t "${DOCKER_IMAGE}:latest" \
        -f deployment/docker/Dockerfile \
        .

    echo -e "${GREEN}✅ Image built successfully${NC}"
}

# Function to push Docker image
push_image() {
    echo -e "${YELLOW}📤 Pushing Docker image to registry...${NC}"

    docker push "${DOCKER_IMAGE}:${VERSION}"
    docker push "${DOCKER_IMAGE}:latest"

    echo -e "${GREEN}✅ Image pushed successfully${NC}"
}

# Function to create namespace if it doesn't exist
create_namespace() {
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        echo -e "${GREEN}✅ Namespace ${NAMESPACE} exists${NC}"
    else
        echo -e "${YELLOW}📦 Creating namespace ${NAMESPACE}...${NC}"
        kubectl apply -f deployment/kubernetes/namespace.yaml
        echo -e "${GREEN}✅ Namespace created${NC}"
    fi
}

# Function to deploy Kubernetes resources
deploy_k8s() {
    echo -e "${YELLOW}☸️  Deploying to Kubernetes...${NC}"

    # Apply manifests in order
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/secret.yaml
    kubectl apply -f deployment/kubernetes/pvc.yaml
    kubectl apply -f deployment/kubernetes/deployment.yaml

    echo -e "${GREEN}✅ Kubernetes resources applied${NC}"
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "${YELLOW}⏳ Waiting for deployment to be ready...${NC}"

    kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=5m

    echo -e "${GREEN}✅ Deployment ready${NC}"
}

# Function to show deployment status
show_status() {
    echo -e "${YELLOW}📊 Deployment Status:${NC}"
    kubectl get pods -n ${NAMESPACE} -l app=${DEPLOYMENT_NAME}
    echo ""
    kubectl get deployment ${DEPLOYMENT_NAME} -n ${NAMESPACE}
}

# Main deployment flow
main() {
    check_kubectl
    check_cluster

    # Ask for confirmation
    echo -e "${YELLOW}⚠️  This will deploy to ${ENVIRONMENT} environment.${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi

    build_image
    push_image
    create_namespace
    deploy_k8s
    wait_for_deployment
    show_status

    echo ""
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo -e "${GREEN}Monitor logs with: kubectl logs -f deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}${NC}"
}

# Run main function
main
