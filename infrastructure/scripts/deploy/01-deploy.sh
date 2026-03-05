#!/bin/bash
# =============================================================================
# Mrki Infrastructure Deployment Script
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENVIRONMENT="${ENVIRONMENT:-development}"
CLOUD_PROVIDER="${CLOUD_PROVIDER:-aws}"
REGION="${REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-mrki-cluster}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Mrki Infrastructure Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    all                 Deploy all infrastructure components
    terraform           Deploy Terraform infrastructure
    k8s                 Deploy Kubernetes manifests
    monitoring          Deploy monitoring stack
    storage             Deploy storage components
    networking          Deploy networking components
    backup              Deploy backup solutions
    destroy             Destroy all infrastructure

Options:
    -e, --environment   Environment (development|staging|production)
    -c, --cloud         Cloud provider (aws|gcp|azure)
    -r, --region        Cloud region
    -h, --help          Show this help message

Examples:
    $0 all -e production -c aws -r us-east-1
    $0 terraform -e staging -c gcp
    $0 k8s -e production
EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -c|--cloud)
                CLOUD_PROVIDER="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local tools=("terraform" "kubectl" "helm" "aws" "jq")
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed"
            exit 1
        fi
    done
    
    log_success "All prerequisites met"
}

# Deploy Terraform infrastructure
deploy_terraform() {
    log_info "Deploying Terraform infrastructure for $CLOUD_PROVIDER..."
    
    cd "$INFRA_DIR/terraform/$CLOUD_PROVIDER"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init -upgrade
    
    # Validate Terraform
    log_info "Validating Terraform configuration..."
    terraform validate
    
    # Plan Terraform
    log_info "Planning Terraform changes..."
    terraform plan -var="environment=$ENVIRONMENT" -var="aws_region=$REGION" -out=tfplan
    
    # Apply Terraform
    log_info "Applying Terraform changes..."
    terraform apply tfplan
    
    log_success "Terraform infrastructure deployed successfully"
}

# Deploy Kubernetes manifests
deploy_k8s() {
    log_info "Deploying Kubernetes manifests..."
    
    # Create namespaces
    log_info "Creating namespaces..."
    kubectl apply -f "$INFRA_DIR/k8s/namespaces/"
    
    # Deploy base manifests
    log_info "Deploying base manifests..."
    kubectl apply -f "$INFRA_DIR/k8s/base/"
    
    # Deploy HPA
    log_info "Deploying HPA configurations..."
    kubectl apply -f "$INFRA_DIR/k8s/hpa/"
    
    log_success "Kubernetes manifests deployed successfully"
}

# Deploy Helm charts
deploy_helm() {
    log_info "Deploying Helm charts..."
    
    # Add Helm repositories
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add jetstack https://charts.jetstack.io
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
    helm repo update
    
    # Install cert-manager
    log_info "Installing cert-manager..."
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true \
        --wait
    
    # Install NGINX Ingress Controller
    log_info "Installing NGINX Ingress Controller..."
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.replicaCount=2 \
        --set controller.nodeSelector."workload"="general" \
        --wait
    
    # Install kube-prometheus-stack
    log_info "Installing Prometheus Stack..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --values "$INFRA_DIR/monitoring/prometheus/values.yaml" \
        --wait
    
    # Install Loki
    log_info "Installing Loki..."
    helm upgrade --install loki grafana/loki-stack \
        --namespace monitoring \
        --set promtail.enabled=true \
        --wait
    
    # Install Velero
    log_info "Installing Velero..."
    helm upgrade --install velero vmware-tanzu/velero \
        --namespace velero \
        --create-namespace \
        --set configuration.provider=aws \
        --set configuration.backupStorageLocation.bucket=mrki-velero-backups \
        --set configuration.backupStorageLocation.config.region=us-east-1 \
        --wait
    
    log_success "Helm charts deployed successfully"
}

# Deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    kubectl apply -f "$INFRA_DIR/monitoring/prometheus/"
    kubectl apply -f "$INFRA_DIR/monitoring/grafana/"
    kubectl apply -f "$INFRA_DIR/monitoring/loki/"
    
    log_success "Monitoring stack deployed successfully"
}

# Deploy storage components
deploy_storage() {
    log_info "Deploying storage components..."
    
    kubectl apply -f "$INFRA_DIR/storage/postgresql/"
    kubectl apply -f "$INFRA_DIR/storage/mongodb/"
    kubectl apply -f "$INFRA_DIR/storage/redis/"
    kubectl apply -f "$INFRA_DIR/storage/s3/"
    
    log_success "Storage components deployed successfully"
}

# Deploy networking components
deploy_networking() {
    log_info "Deploying networking components..."
    
    kubectl apply -f "$INFRA_DIR/networking/ingress/"
    kubectl apply -f "$INFRA_DIR/networking/cert-manager/"
    kubectl apply -f "$INFRA_DIR/networking/cdn/"
    
    log_success "Networking components deployed successfully"
}

# Deploy backup solutions
deploy_backup() {
    log_info "Deploying backup solutions..."
    
    kubectl apply -f "$INFRA_DIR/backup/velero/"
    kubectl apply -f "$INFRA_DIR/backup/scripts/"
    
    log_success "Backup solutions deployed successfully"
}

# Deploy all components
deploy_all() {
    log_info "Starting full infrastructure deployment..."
    
    deploy_terraform
    configure_kubectl
    deploy_k8s
    deploy_helm
    deploy_storage
    deploy_networking
    deploy_monitoring
    deploy_backup
    
    log_success "Full infrastructure deployment completed!"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl..."
    
    case $CLOUD_PROVIDER in
        aws)
            aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
            ;;
        gcp)
            gcloud container clusters get-credentials "$CLUSTER_NAME" --region "$REGION"
            ;;
        azure)
            az aks get-credentials --resource-group "${CLUSTER_NAME}-rg" --name "$CLUSTER_NAME"
            ;;
    esac
    
    log_success "kubectl configured"
}

# Destroy infrastructure
destroy_infrastructure() {
    log_warn "This will destroy all infrastructure! Are you sure? (yes/no)"
    read -r confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "Destruction cancelled"
        exit 0
    fi
    
    log_info "Destroying infrastructure..."
    
    # Destroy Kubernetes resources
    kubectl delete -f "$INFRA_DIR/k8s/" --ignore-not-found=true || true
    kubectl delete -f "$INFRA_DIR/monitoring/" --ignore-not-found=true || true
    kubectl delete -f "$INFRA_DIR/storage/" --ignore-not-found=true || true
    kubectl delete -f "$INFRA_DIR/networking/" --ignore-not-found=true || true
    kubectl delete -f "$INFRA_DIR/backup/" --ignore-not-found=true || true
    
    # Destroy Helm releases
    helm uninstall -n cert-manager cert-manager || true
    helm uninstall -n ingress-nginx ingress-nginx || true
    helm uninstall -n monitoring prometheus || true
    helm uninstall -n monitoring loki || true
    helm uninstall -n velero velero || true
    
    # Destroy Terraform
    cd "$INFRA_DIR/terraform/$CLOUD_PROVIDER"
    terraform destroy -var="environment=$ENVIRONMENT" -var="aws_region=$REGION" -auto-approve
    
    log_success "Infrastructure destroyed"
}

# Main function
main() {
    parse_args "$@"
    
    if [[ -z "${COMMAND:-}" ]]; then
        show_help
        exit 1
    fi
    
    check_prerequisites
    
    case $COMMAND in
        all)
            deploy_all
            ;;
        terraform)
            deploy_terraform
            ;;
        k8s)
            configure_kubectl
            deploy_k8s
            ;;
        helm)
            configure_kubectl
            deploy_helm
            ;;
        monitoring)
            configure_kubectl
            deploy_monitoring
            ;;
        storage)
            configure_kubectl
            deploy_storage
            ;;
        networking)
            configure_kubectl
            deploy_networking
            ;;
        backup)
            configure_kubectl
            deploy_backup
            ;;
        destroy)
            destroy_infrastructure
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
