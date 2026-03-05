#!/bin/bash
# =============================================================================
# Mrki Infrastructure Health Check Script
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACES=("mrki-apps" "mrki-data" "monitoring" "ingress-nginx" "velero")

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Check Kubernetes cluster health
check_k8s_cluster() {
    log_info "Checking Kubernetes cluster health..."
    
    # Check API server
    if kubectl cluster-info &> /dev/null; then
        log_success "Kubernetes API server is accessible"
    else
        log_error "Kubernetes API server is not accessible"
        return 1
    fi
    
    # Check nodes
    local ready_nodes=$(kubectl get nodes -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' | grep -c "True" || true)
    local total_nodes=$(kubectl get nodes --no-headers | wc -l)
    
    if [[ "$ready_nodes" -eq "$total_nodes" ]]; then
        log_success "All $total_nodes nodes are ready"
    else
        log_warn "$ready_nodes/$total_nodes nodes are ready"
    fi
}

# Check pod health
check_pods() {
    log_info "Checking pod health..."
    
    for ns in "${NAMESPACES[@]}"; do
        log_info "Checking namespace: $ns"
        
        # Check for pods not in Running or Completed state
        local problematic_pods=$(kubectl get pods -n "$ns" --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers 2>/dev/null || true)
        
        if [[ -z "$problematic_pods" ]]; then
            log_success "All pods in $ns are healthy"
        else
            log_error "Problematic pods in $ns:"
            echo "$problematic_pods"
        fi
        
        # Check for pods with high restart counts
        local high_restart_pods=$(kubectl get pods -n "$ns" -o jsonpath='{range .items[?(@.status.containerStatuses[0].restartCount>5)]}{.metadata.name}{"\n"}{end}' 2>/dev/null || true)
        
        if [[ -n "$high_restart_pods" ]]; then
            log_warn "Pods with high restart count in $ns:"
            echo "$high_restart_pods"
        fi
    done
}

# Check services
check_services() {
    log_info "Checking services..."
    
    local services=(
        "mrki-apps/mrki-api"
        "mrki-apps/mrki-web"
        "mrki-data/mrki-postgres"
        "mrki-data/mrki-redis"
        "monitoring/prometheus"
        "monitoring/grafana"
    )
    
    for svc in "${services[@]}"; do
        if kubectl get svc -n "${svc%/*}" "${svc#*/}" &> /dev/null; then
            log_success "Service $svc exists"
        else
            log_error "Service $svc not found"
        fi
    done
}

# Check ingress
check_ingress() {
    log_info "Checking ingress resources..."
    
    local ingresses=(
        "mrki-apps/mrki-ingress"
        "monitoring/grafana"
    )
    
    for ing in "${ingresses[@]}"; do
        if kubectl get ingress -n "${ing%/*}" "${ing#*/}" &> /dev/null; then
            log_success "Ingress $ing exists"
        else
            log_error "Ingress $ing not found"
        fi
    done
}

# Check persistent volumes
check_storage() {
    log_info "Checking storage..."
    
    # Check PVCs
    local bound_pvcs=$(kubectl get pvc --all-namespaces -o jsonpath='{range .items[?(@.status.phase=="Bound")]}{.metadata.name}{"\n"}{end}' | wc -l)
    local total_pvcs=$(kubectl get pvc --all-namespaces --no-headers | wc -l)
    
    if [[ "$bound_pvcs" -eq "$total_pvcs" ]]; then
        log_success "All $total_pvcs PVCs are bound"
    else
        log_warn "$bound_pvcs/$total_pvcs PVCs are bound"
    fi
    
    # Check for unbound PVCs
    local unbound_pvcs=$(kubectl get pvc --all-namespaces --field-selector=status.phase!=Bound --no-headers 2>/dev/null || true)
    if [[ -n "$unbound_pvcs" ]]; then
        log_error "Unbound PVCs:"
        echo "$unbound_pvcs"
    fi
}

# Check HPA
check_hpa() {
    log_info "Checking HPA status..."
    
    local hpas=$(kubectl get hpa -n mrki-apps --no-headers 2>/dev/null || true)
    
    if [[ -n "$hpas" ]]; then
        echo "$hpas"
        log_success "HPA resources found"
    else
        log_warn "No HPA resources found"
    fi
}

# Check certificates
check_certificates() {
    log_info "Checking certificates..."
    
    local certs=$(kubectl get certificates --all-namespaces --no-headers 2>/dev/null || true)
    
    if [[ -n "$certs" ]]; then
        local ready_certs=$(echo "$certs" | grep -c "True" || true)
        local total_certs=$(echo "$certs" | wc -l)
        
        if [[ "$ready_certs" -eq "$total_certs" ]]; then
            log_success "All $total_certs certificates are ready"
        else
            log_warn "$ready_certs/$total_certs certificates are ready"
        fi
    else
        log_warn "No certificates found"
    fi
}

# Check monitoring
check_monitoring() {
    log_info "Checking monitoring stack..."
    
    # Check Prometheus
    if kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
        log_success "Prometheus is running"
    else
        log_error "Prometheus is not running"
    fi
    
    # Check Grafana
    if kubectl get pods -n monitoring -l app=grafana -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
        log_success "Grafana is running"
    else
        log_error "Grafana is not running"
    fi
    
    # Check Loki
    if kubectl get pods -n monitoring -l app=loki -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
        log_success "Loki is running"
    else
        log_error "Loki is not running"
    fi
}

# Check backup status
check_backups() {
    log_info "Checking backup status..."
    
    # Check Velero
    if kubectl get pods -n velero -l app=velero &> /dev/null; then
        log_success "Velero is deployed"
        
        # Check backup schedules
        local schedules=$(kubectl get schedules -n velero --no-headers 2>/dev/null || true)
        if [[ -n "$schedules" ]]; then
            log_success "Backup schedules configured"
            echo "$schedules"
        else
            log_warn "No backup schedules found"
        fi
    else
        log_warn "Velero is not deployed"
    fi
}

# Check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Get top nodes
    log_info "Node resource usage:"
    kubectl top nodes 2>/dev/null || log_warn "Metrics server not available"
    
    # Get top pods
    log_info "Top resource-consuming pods:"
    kubectl top pods --all-namespaces --sort-by=cpu 2>/dev/null | head -20 || log_warn "Metrics server not available"
}

# Check events
check_events() {
    log_info "Checking recent events..."
    
    local warning_events=$(kubectl get events --all-namespaces --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -20 || true)
    
    if [[ -n "$warning_events" ]]; then
        log_warn "Recent warning events:"
        echo "$warning_events"
    else
        log_success "No recent warning events"
    fi
}

# Generate report
generate_report() {
    log_info "Generating health report..."
    
    local report_file="/tmp/mrki-health-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "======================================"
        echo "Mrki Infrastructure Health Report"
        echo "Generated: $(date)"
        echo "======================================"
        echo ""
        echo "Cluster Info:"
        kubectl cluster-info
        echo ""
        echo "Node Status:"
        kubectl get nodes
        echo ""
        echo "Pod Status:"
        kubectl get pods --all-namespaces
        echo ""
        echo "Service Status:"
        kubectl get services --all-namespaces
        echo ""
        echo "PVC Status:"
        kubectl get pvc --all-namespaces
        echo ""
        echo "Ingress Status:"
        kubectl get ingress --all-namespaces
        echo ""
        echo "HPA Status:"
        kubectl get hpa --all-namespaces
        echo ""
        echo "Certificate Status:"
        kubectl get certificates --all-namespaces
        echo ""
        echo "Recent Events:"
        kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -50
    } > "$report_file"
    
    log_success "Health report saved to: $report_file"
}

# Main function
main() {
    log_info "Starting Mrki infrastructure health check..."
    
    check_k8s_cluster
    check_pods
    check_services
    check_ingress
    check_storage
    check_hpa
    check_certificates
    check_monitoring
    check_backups
    check_resource_usage
    check_events
    
    generate_report
    
    log_info "Health check completed!"
}

main "$@"
