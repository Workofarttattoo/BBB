# Kubernetes Deployment Guide
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

## Prerequisites

- Kubernetes cluster (AWS EKS, GKE, or AKS)
- `kubectl` installed and configured
- Docker image built and pushed to registry
- cert-manager for TLS certificates (optional)
- NGINX Ingress Controller (optional)

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configure Secrets

**IMPORTANT**: Never commit actual secrets to git!

Create secrets from environment file:

```bash
# Create .env.production with actual values
kubectl create secret generic bbb-secrets \
  --from-env-file=.env.production \
  --namespace=bbb-production

kubectl create secret generic postgres-credentials \
  --from-literal=password='YOUR_POSTGRES_PASSWORD' \
  --namespace=bbb-production

kubectl create secret generic redis-credentials \
  --from-literal=password='YOUR_REDIS_PASSWORD' \
  --namespace=bbb-production
```

Or apply the template (after replacing CHANGEME values):

```bash
kubectl apply -f k8s/secrets.yaml
```

### 3. Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### 4. Deploy Database

```bash
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
```

Wait for databases to be ready:

```bash
kubectl wait --for=condition=ready pod -l app=postgres -n bbb-production --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n bbb-production --timeout=300s
```

### 5. Run Database Migrations

```bash
kubectl run -it --rm migrations \
  --image=bbb/api:latest \
  --restart=Never \
  --namespace=bbb-production \
  --env="DATABASE_URL=$(kubectl get secret bbb-secrets -n bbb-production -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
  -- alembic upgrade head
```

### 6. Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml
```

Wait for deployment:

```bash
kubectl rollout status deployment/bbb-api -n bbb-production
```

### 7. Setup Ingress (Optional)

```bash
# Install NGINX Ingress Controller (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager for TLS (if not already installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Apply ingress
kubectl apply -f k8s/ingress.yaml
```

## Verify Deployment

```bash
# Check all resources
kubectl get all -n bbb-production

# Check pods
kubectl get pods -n bbb-production

# Check services
kubectl get svc -n bbb-production

# Check ingress
kubectl get ingress -n bbb-production

# View logs
kubectl logs -f deployment/bbb-api -n bbb-production

# Check HPA status
kubectl get hpa -n bbb-production
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment bbb-api --replicas=5 -n bbb-production
```

### Auto-Scaling

The HPA is configured to auto-scale between 3-20 replicas based on CPU/memory usage.

View HPA status:

```bash
kubectl get hpa bbb-api-hpa -n bbb-production --watch
```

## Updating Deployment

### Update Image

```bash
# Build and push new image
docker build -t bbb/api:v1.1.0 .
docker push bbb/api:v1.1.0

# Update deployment
kubectl set image deployment/bbb-api api=bbb/api:v1.1.0 -n bbb-production

# Monitor rollout
kubectl rollout status deployment/bbb-api -n bbb-production
```

### Rollback

```bash
kubectl rollout undo deployment/bbb-api -n bbb-production
```

### Update ConfigMap or Secrets

```bash
# Update configmap
kubectl apply -f k8s/configmap.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/bbb-api -n bbb-production
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n bbb-production

# Check logs
kubectl logs <pod-name> -n bbb-production

# Get shell access
kubectl exec -it <pod-name> -n bbb-production -- /bin/sh
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm psql-test \
  --image=postgres:15-alpine \
  --restart=Never \
  --namespace=bbb-production \
  -- psql "postgresql://bbbuser:password@postgres:5432/bbb_production"
```

### Check Resource Usage

```bash
# View resource consumption
kubectl top pods -n bbb-production
kubectl top nodes
```

## Monitoring

Prometheus metrics are exposed at `/metrics` endpoint.

## Cleanup

```bash
# Delete all resources
kubectl delete namespace bbb-production
```

## Production Checklist

- [ ] Use production-grade database (AWS RDS, GCP Cloud SQL, etc.)
- [ ] Configure persistent volumes for stateful sets
- [ ] Setup backup/restore for databases
- [ ] Configure resource limits appropriately
- [ ] Enable pod security policies
- [ ] Setup network policies
- [ ] Configure monitoring and alerting
- [ ] Setup log aggregation (ELK, Datadog, etc.)
- [ ] Use secrets management (AWS Secrets Manager, Vault, etc.)
- [ ] Configure multi-zone deployment for HA
- [ ] Setup disaster recovery plan
- [ ] Configure pod disruption budgets
- [ ] Enable auto-scaling for cluster nodes

## Cost Optimization

- Use spot instances for non-critical workloads
- Configure appropriate resource requests/limits
- Use cluster autoscaler
- Monitor and optimize database queries
- Use caching (Redis) effectively
- Consider reserved instances for production
