# Mrki Cloud Infrastructure

A comprehensive, production-ready cloud infrastructure solution for the Mrki platform, supporting multi-cloud deployment on AWS, GCP, and Azure.

## Overview

This infrastructure layer provides:

- **Kubernetes-based orchestration** with auto-scaling (HPA, VPA, Cluster Autoscaler)
- **Multi-cloud IaaS/PaaS abstractions** (AWS, GCP, Azure)
- **Real-time data processing pipelines**
- **Distributed storage** (PostgreSQL, MongoDB, Redis, S3-compatible object storage)
- **Serverless function deployment** templates
- **Monitoring, logging, and observability** (Prometheus, Grafana, Loki, Jaeger)
- **Load balancing and traffic management**
- **Backup and disaster recovery** automation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Mrki Platform                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Web App    │  │    API       │  │   Worker     │  │  Processor   │    │
│  │  (Next.js)   │  │   (Go/Node)  │  │  (Queue)     │  │  (Events)    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
├─────────┴─────────────────┴─────────────────┴─────────────────┴─────────────┤
│                         Kubernetes (EKS/GKE/AKS)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Ingress (NGINX) │  Cert-Manager │  External-DNS  │  Network Policies│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │      HPA/VPA        │  │  Cluster Autoscaler │  │   Pod Disruption    │  │
│  │   (Auto-scaling)    │  │   (Node scaling)    │  │      Budgets        │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                         Data Layer                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │   MongoDB    │  │    Redis     │  │    MinIO     │    │
│  │  (Primary)   │  │ (Document)   │  │   (Cache)    │  │  (S3 API)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│                      Monitoring & Observability                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Prometheus  │  │   Grafana    │  │    Loki      │  │   Jaeger     │    │
│  │  (Metrics)   │  │(Dashboards)  │  │   (Logs)     │  │  (Traces)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│                      Backup & Disaster Recovery                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │    Velero    │  │  CronJobs    │  │   S3/GCS     │                       │
│  │ (K8s backup) │  │ (DB backup)  │  │  (Storage)   │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
infrastructure/
├── terraform/              # Infrastructure-as-Code
│   ├── aws/               # AWS Terraform modules
│   ├── gcp/               # GCP Terraform modules
│   ├── azure/             # Azure Terraform modules
│   └── modules/           # Reusable Terraform modules
├── k8s/                   # Kubernetes manifests
│   ├── base/              # Base deployments, services, ingress
│   ├── helm-charts/       # Helm charts for applications
│   ├── hpa/               # Horizontal Pod Autoscaler configs
│   └── namespaces/        # Namespace definitions
├── serverless/            # Serverless function templates
│   ├── aws-lambda/        # AWS Lambda functions
│   ├── gcp-functions/     # GCP Cloud Functions
│   └── azure-functions/   # Azure Functions
├── monitoring/            # Monitoring stack
│   ├── prometheus/        # Prometheus configuration
│   ├── grafana/           # Grafana dashboards
│   ├── loki/              # Loki logging
│   └── jaeger/            # Distributed tracing
├── storage/               # Database configurations
│   ├── postgresql/        # PostgreSQL StatefulSet
│   ├── mongodb/           # MongoDB StatefulSet
│   ├── redis/             # Redis StatefulSet
│   └── s3/                # Object storage (MinIO)
├── networking/            # Network configurations
│   ├── ingress/           # NGINX Ingress Controller
│   ├── cert-manager/      # TLS certificate management
│   └── cdn/               # CDN and DNS configuration
├── backup/                # Backup solutions
│   ├── velero/            # Velero for K8s backup
│   └── scripts/           # Database backup scripts
└── scripts/               # Deployment scripts
    ├── deploy/            # Deployment automation
    └── utils/             # Utility scripts
```

## Quick Start

### Prerequisites

- Terraform >= 1.5.0
- kubectl
- Helm 3.x
- AWS CLI / gcloud / Azure CLI
- Docker

### Deployment

1. **Clone and configure:**
```bash
cd infrastructure
export ENVIRONMENT=production
export CLOUD_PROVIDER=aws
export REGION=us-east-1
```

2. **Deploy infrastructure:**
```bash
# Deploy all components
./scripts/deploy/01-deploy.sh all -e production -c aws -r us-east-1

# Or deploy individual components
./scripts/deploy/01-deploy.sh terraform -e production -c aws
./scripts/deploy/01-deploy.sh k8s -e production
./scripts/deploy/01-deploy.sh monitoring -e production
```

3. **Verify deployment:**
```bash
./scripts/utils/02-health-check.sh
```

## Multi-Cloud Support

### AWS

```bash
# Deploy to AWS
export AWS_REGION=us-east-1
cd terraform/aws
terraform init
terraform apply -var="environment=production"
```

**Features:**
- EKS (Elastic Kubernetes Service)
- RDS PostgreSQL
- ElastiCache Redis
- S3 + CloudFront CDN
- Application Load Balancer
- WAF (Web Application Firewall)
- Lambda functions
- SQS/SNS for messaging

### GCP

```bash
# Deploy to GCP
export GCP_PROJECT_ID=mrki-project
export GCP_REGION=us-central1
cd terraform/gcp
terraform init
terraform apply -var="environment=production"
```

**Features:**
- GKE (Google Kubernetes Engine)
- Cloud SQL PostgreSQL
- Memorystore Redis
- Cloud Storage + CDN
- Cloud Load Balancing
- Cloud Armor (WAF)
- Cloud Functions
- Pub/Sub for messaging

### Azure

```bash
# Deploy to Azure
export AZURE_REGION=East US
cd terraform/azure
terraform init
terraform apply -var="environment=production"
```

**Features:**
- AKS (Azure Kubernetes Service)
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Blob Storage + CDN
- Azure Load Balancer
- Azure WAF
- Azure Functions
- Service Bus for messaging

## Auto-Scaling Configuration

### Horizontal Pod Autoscaler (HPA)

```yaml
# API service: 3-50 replicas based on CPU/memory
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 3
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 70
```

### Vertical Pod Autoscaler (VPA)

```yaml
# Automatically adjusts CPU/memory requests
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
spec:
  updatePolicy:
    updateMode: "Auto"
```

### Cluster Autoscaler

Automatically scales node groups based on pending pods:
- **General nodes**: 1-10 nodes
- **Spot nodes**: 0-10 nodes (cost-effective)
- **GPU nodes**: 0-4 nodes (on-demand)

## Storage Configuration

### PostgreSQL

- **Primary**: 1 instance (can be replicated)
- **Storage**: 50GB with auto-resize
- **Backup**: Every 6 hours to S3
- **Retention**: 30 days

### MongoDB

- **Replicas**: 3-node replica set
- **Storage**: 20GB per node
- **Backup**: Every 6 hours to S3

### Redis

- **Mode**: Replication (1 master, 2 replicas)
- **Memory**: 512MB limit
- **Persistence**: AOF + RDB
- **Eviction**: allkeys-lru

### Object Storage (MinIO)

- **Nodes**: 4-node distributed cluster
- **Storage**: 100GB per node
- **API**: S3-compatible
- **Features**: Versioning, lifecycle policies

## Monitoring Stack

### Prometheus

- **Metrics collection**: All services
- **Retention**: 30 days
- **Storage**: 100GB
- **Alerting**: Built-in alert rules

### Grafana

- **Dashboards**: Pre-configured for Mrki
- **Data sources**: Prometheus, Loki, Jaeger
- **Authentication**: OAuth support

### Loki

- **Log aggregation**: All containers
- **Retention**: 30 days
- **Storage**: 100GB

### Jaeger

- **Distributed tracing**: Request flows
- **Sampling**: 1% in production

## Backup & Disaster Recovery

### Velero

- **Schedule**: Daily at 2 AM
- **Retention**: 30 days
- **Storage**: S3/GCS/Azure Blob
- **Scope**: All namespaces

### Database Backups

- **PostgreSQL**: Every 6 hours
- **MongoDB**: Every 6 hours
- **Redis**: Every 12 hours
- **Retention**: 30 days

### Disaster Recovery

1. **RPO (Recovery Point Objective)**: 6 hours
2. **RTO (Recovery Time Objective)**: 1 hour
3. **Cross-region replication**: Available

## Security

### Network Security

- **Network Policies**: Pod-to-pod traffic control
- **WAF**: OWASP rules, rate limiting
- **DDoS Protection**: Cloud provider native

### Data Security

- **Encryption at rest**: All storage encrypted
- **Encryption in transit**: TLS 1.2+
- **Secrets management**: External Secrets Operator

### Access Control

- **RBAC**: Kubernetes RBAC configured
- **IAM**: Cloud provider IAM integration
- **Service Mesh**: Optional Istio/Linkerd

## Cost Optimization

### Spot/Preemptible Instances

- **Worker nodes**: Spot instances for 60-90% savings
- **GPU nodes**: Preemptible for batch workloads

### Reserved Capacity

- **Production**: 1-year reserved instances
- **Savings**: Up to 40% discount

### Auto-scaling

- **Scale to zero**: Non-production environments
- **Scheduled scaling**: Business hours only

## Serverless Functions

### AWS Lambda

```python
# handler.py - Supports API Gateway, S3, SQS, SNS triggers
def lambda_handler(event, context):
    # Process events
    return {'statusCode': 200, 'body': 'Success'}
```

### GCP Cloud Functions

```javascript
// index.js - Supports HTTP, Pub/Sub, Cloud Storage triggers
functions.http('mrkiHttpHandler', async (req, res) => {
    // Process HTTP requests
    res.status(200).json({status: 'success'});
});
```

### Azure Functions

```python
# function_app.py - Supports HTTP, Queue, Blob, Timer triggers
@app.route(route="process", methods=["POST"])
def http_process(req: func.HttpRequest) -> func.HttpResponse:
    # Process requests
    return func.HttpResponse(json.dumps(result), status_code=200)
```

## Troubleshooting

### Health Check

```bash
# Run comprehensive health check
./scripts/utils/02-health-check.sh
```

### Common Issues

1. **Pods not starting**: Check resource quotas and node capacity
2. **HPA not scaling**: Verify metrics server is running
3. **Ingress not working**: Check NGINX controller logs
4. **Certificate issues**: Verify cert-manager and DNS

### Logs

```bash
# View application logs
kubectl logs -f deployment/mrki-api -n mrki-apps

# View all pods in namespace
kubectl logs -f -l app=mrki-api -n mrki-apps --all-containers

# View Loki logs in Grafana
# https://grafana.mrki.io/explore
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For support, email devops@mrki.io or join our Slack channel.
