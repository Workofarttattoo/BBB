# Monitoring Setup Guide
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

## Overview

This directory contains monitoring configuration for Better Business Builder using:
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Metrics visualization and dashboards

## Quick Start

### 1. Deploy Prometheus

```bash
kubectl apply -f monitoring/prometheus.yaml
```

Verify Prometheus is running:

```bash
kubectl get pods -n bbb-production -l app=prometheus
kubectl logs -f deployment/prometheus -n bbb-production
```

Access Prometheus UI:

```bash
kubectl port-forward svc/prometheus 9090:9090 -n bbb-production
# Open http://localhost:9090
```

### 2. Deploy Grafana

```bash
kubectl apply -f monitoring/grafana.yaml
```

Verify Grafana is running:

```bash
kubectl get pods -n bbb-production -l app=grafana
```

Access Grafana UI:

```bash
# Get the LoadBalancer IP
kubectl get svc grafana -n bbb-production

# Or use port-forward
kubectl port-forward svc/grafana 3000:3000 -n bbb-production
# Open http://localhost:3000
```

Default credentials:
- Username: `admin`
- Password: (set in grafana-credentials secret)

## Available Metrics

### Application Metrics

- `bbb_requests_total`: Total HTTP requests (labeled by method, endpoint, status)
- `bbb_request_duration_seconds`: HTTP request duration histogram
- `bbb_active_businesses`: Current number of active businesses
- `bbb_agent_tasks_total`: Total agent tasks (labeled by role, status)
- `bbb_revenue_total`: Total revenue generated
- `bbb_ai_requests_total`: AI API requests (labeled by service, status)
- `bbb_payment_transactions_total`: Payment transactions (labeled by status)
- `bbb_subscription_changes_total`: Subscription changes (labeled by plan, action)
- `bbb_email_campaigns_total`: Email campaigns sent
- `bbb_social_posts_total`: Social media posts

### System Metrics

- Container CPU/memory usage
- Pod restart counts
- Network traffic
- Database connections
- Cache hit/miss rates

## Alerts

Configured alerts in `prometheus.yaml`:

1. **HighErrorRate**: Error rate > 5% for 5 minutes
2. **HighResponseTime**: p95 response time > 1 second
3. **PodCrashLooping**: Pods restarting frequently
4. **HighMemoryUsage**: Memory usage > 90%
5. **HighCPUUsage**: CPU usage > 80%
6. **DatabaseDown**: PostgreSQL unavailable
7. **RedisDown**: Redis unavailable

## Grafana Dashboards

### BBB API Dashboard

Pre-configured dashboard includes:

- Request rate (requests/second)
- Error rate (%)
- Response time (p50, p95, p99)
- Active businesses
- Agent task success rate
- Revenue metrics
- Resource usage (CPU, memory)

### Creating Custom Dashboards

1. Login to Grafana
2. Click "+" → "Dashboard"
3. Add panels with Prometheus queries
4. Save dashboard

Example queries:

```promql
# Request rate
rate(bbb_requests_total[5m])

# Error rate
rate(bbb_requests_total{status=~"5.."}[5m]) / rate(bbb_requests_total[5m])

# Response time p95
histogram_quantile(0.95, rate(bbb_request_duration_seconds_bucket[5m]))

# Active businesses trend
bbb_active_businesses

# Agent success rate
rate(bbb_agent_tasks_total{status="completed"}[5m]) / rate(bbb_agent_tasks_total[5m])
```

## Integration with Application

The metrics are already integrated in `src/blank_business_builder/metrics.py` and `main.py`.

To track custom metrics:

```python
from .metrics import (
    track_agent_task,
    update_business_metrics,
    track_ai_request,
    track_payment
)

# Track agent task
track_agent_task(agent_role="marketer", status="completed")

# Update business metrics
update_business_metrics(total_businesses=150, total_revenue=45000.00)

# Track AI request
track_ai_request(service="openai", duration=1.2, status="success")

# Track payment
track_payment(status="succeeded")
```

## Alertmanager (Optional)

To setup alerting notifications:

1. Deploy Alertmanager
2. Configure receivers (Slack, email, PagerDuty, etc.)
3. Update Prometheus config to use Alertmanager

Example Slack integration:

```yaml
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
```

## Troubleshooting

### Prometheus not scraping metrics

```bash
# Check Prometheus targets
# Open Prometheus UI → Status → Targets

# Verify pod annotations
kubectl get pod <pod-name> -n bbb-production -o yaml | grep prometheus.io
```

### Grafana datasource connection failed

```bash
# Check Prometheus service
kubectl get svc prometheus -n bbb-production

# Test connectivity from Grafana pod
kubectl exec -it deployment/grafana -n bbb-production -- curl http://prometheus:9090/api/v1/status/config
```

### Missing metrics

```bash
# Check if metrics endpoint is working
kubectl port-forward deployment/bbb-api 8000:8000 -n bbb-production
curl http://localhost:8000/metrics
```

## Production Recommendations

- [ ] Setup persistent storage for Prometheus data
- [ ] Configure Prometheus remote write to long-term storage (Thanos, Cortex)
- [ ] Setup Alertmanager with multiple receivers
- [ ] Configure Grafana authentication (SSO, OAuth)
- [ ] Create runbooks for each alert
- [ ] Setup on-call rotation
- [ ] Configure automated incident response
- [ ] Setup log aggregation (ELK, Loki)
- [ ] Configure distributed tracing (Jaeger, Tempo)
- [ ] Setup synthetic monitoring (uptime checks)
- [ ] Configure SLO/SLI dashboards

## Cost Optimization

- Use retention policies to limit storage
- Sample high-cardinality metrics
- Use recording rules for expensive queries
- Consider managed Prometheus (AWS AMP, GCP Managed Prometheus)
