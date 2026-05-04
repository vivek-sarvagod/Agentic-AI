# Portal Survey Agent - Kubernetes Deployment Guide

## Overview
The portal-survey-agent has been added to the existing Helm chart alongside the UI and API services.

## What Was Added

### 1. Helm Templates
- **`agent-deployment.yaml`**: Kubernetes Deployment for the agent service
- **`agent-service.yaml`**: Kubernetes Service exposing the agent on NodePort 30083
- **Updated `ingress.yaml`**: Added `/agent/*` path routing

### 2. Configuration
- **Updated `values.yaml`**: Added complete agent configuration section
- **Updated `secret.yaml`**: Added OPENAI_API_KEY to application secrets

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Kubernetes Cluster (portal-survey namespace)           │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────┐ │
│  │ UI Pod         │  │ API Pod        │  │ Agent Pod │ │
│  │ :8080          │  │ :8000          │  │ :8001     │ │
│  │ (NodePort      │  │ (NodePort      │  │ (NodePort │ │
│  │  30082)        │  │  30081)        │  │  30083)   │ │
│  └────────────────┘  └────────────────┘  └───────────┘ │
│         │                    │                  │        │
│         └────────────────────┴──────────────────┘        │
│                              │                           │
│                    ┌─────────▼─────────┐                │
│                    │  Ingress (Nginx)  │                │
│                    │  / → UI           │                │
│                    │  /api/* → API     │                │
│                    │  /agent/* → Agent │                │
│                    └───────────────────┘                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  External RDS MySQL                                 │ │
│  │  (portal-survey-db.*.rds.amazonaws.com)            │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Configuration Details

### Agent Service Ports
- **Internal Port**: 8001
- **Service Port**: 8001
- **NodePort**: 30083 (external access)

### Environment Variables
The agent automatically connects to:
- **API_BASE_URL**: `http://portal-survey-api:8000` (internal service)
- **MCP_SERVER_URL**: `http://portal-survey-api:8000/mcp` (internal service)
- **OPENAI_API_KEY**: Retrieved from Kubernetes secret

### Resource Allocation
```yaml
Requests:
  CPU: 200m
  Memory: 256Mi
Limits:
  CPU: 1000m
  Memory: 512Mi
```

## Prerequisites

### 1. Build and Push Agent Docker Image
```bash
cd portal-survey-agent

# Build the image
docker build -f docker/Dockerfile -t viveksarvagod/portal-survey-agent:latest .

# Push to Docker Hub
docker push viveksarvagod/portal-survey-agent:latest
```

### 2. Update OpenAI API Key
Edit `portal-charts/values.yaml` and replace the placeholder:
```yaml
secrets:
  openai_api_key: "sk-your-actual-openai-api-key-here"
```

## Deployment Steps

### Option 1: Fresh Install
```bash
cd portal-charts

# Install the complete chart (UI + API + Agent)
helm install portal-survey . \
  --namespace portal-survey \
  --create-namespace \
  --values values.yaml
```

### Option 2: Upgrade Existing Deployment
```bash
cd portal-charts

# Upgrade to add the agent to existing deployment
helm upgrade portal-survey . \
  --namespace portal-survey \
  --values values.yaml
```

### Option 3: Dry Run (Verify Configuration)
```bash
helm upgrade --install portal-survey . \
  --namespace portal-survey \
  --values values.yaml \
  --dry-run --debug
```

## Verification

### 1. Check Pod Status
```bash
kubectl get pods -n portal-survey

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# portal-survey-ui-xxx                    1/1     Running   0          1m
# portal-survey-api-xxx                   1/1     Running   0          1m
# portal-survey-agent-xxx                 1/1     Running   0          1m
```

### 2. Check Services
```bash
kubectl get svc -n portal-survey

# Expected output:
# NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
# portal-survey-ui       NodePort    10.43.x.x       <none>        80:30082/TCP
# portal-survey-api      NodePort    10.43.x.x       <none>        8000:30081/TCP
# portal-survey-agent    NodePort    10.43.x.x       <none>        8001:30083/TCP
```

### 3. Check Agent Logs
```bash
kubectl logs -n portal-survey -l app.kubernetes.io/name=portal-survey-agent -f
```

### 4. Test Agent Health Endpoint
```bash
# Via NodePort
curl http://<node-ip>:30083/health

# Via Ingress
curl http://<ingress-ip>/agent/health

# Expected response:
# {"status":"ok"}
```

### 5. Test Agent Chat Endpoint
```bash
# Via NodePort
curl -X POST http://<node-ip>:30083/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show all surveys"}'

# Via Ingress
curl -X POST http://<ingress-ip>/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show all surveys"}'
```

## Access URLs

### Direct Access (NodePort)
- **UI**: `http://<node-ip>:30082`
- **API**: `http://<node-ip>:30081`
- **Agent**: `http://<node-ip>:30083`

### Via Ingress
- **UI**: `http://<ingress-ip>/`
- **API**: `http://<ingress-ip>/api/`
- **Agent**: `http://<ingress-ip>/agent/`

## Troubleshooting

### Agent Pod Not Starting
```bash
# Check pod events
kubectl describe pod -n portal-survey -l app.kubernetes.io/name=portal-survey-agent

# Common issues:
# - Image pull failures: Check Docker Hub credentials
# - OPENAI_API_KEY missing: Verify secret exists
# - API connection issues: Ensure API pod is running
```

### Check Secrets
```bash
# Verify secrets exist
kubectl get secrets -n portal-survey

# Check secret contains OPENAI_API_KEY
kubectl get secret portal-survey-app-secrets -n portal-survey -o yaml
```

### Agent Can't Connect to API
```bash
# Test internal DNS resolution
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n portal-survey -- sh
# Inside the pod:
curl http://portal-survey-api:8000/health
```

### View All Resources
```bash
kubectl get all -n portal-survey
```

## Rollback

If you need to rollback:
```bash
# View deployment history
helm history portal-survey -n portal-survey

# Rollback to previous version
helm rollback portal-survey -n portal-survey

# Or rollback to specific revision
helm rollback portal-survey 1 -n portal-survey
```

## Uninstall

To completely remove the deployment:
```bash
helm uninstall portal-survey -n portal-survey

# Optionally delete the namespace
kubectl delete namespace portal-survey
```

## Next Steps

1. **Update UI Configuration**: Ensure the React app points to the correct agent endpoint:
   ```typescript
   // portal-survey-ui/src/services/agentApi.ts
   const AGENT_BASE_URL = process.env.REACT_APP_AGENT_URL || 'http://localhost:8001';
   ```

2. **Configure CORS**: If accessing from different domains, update ALLOWED_ORIGINS in values.yaml

3. **SSL/TLS**: For production, configure ingress with TLS certificates

4. **Monitoring**: Add Prometheus/Grafana for monitoring agent performance

5. **Scaling**: Adjust `agent.replicaCount` in values.yaml for horizontal scaling

## Configuration Reference

To customize the agent deployment, edit these sections in `values.yaml`:

```yaml
agent:
  replicaCount: 1              # Number of agent pods
  image:
    repository: viveksarvagod/portal-survey-agent
    tag: latest                # Use specific version tags for production
    pullPolicy: Always
  
  service:
    nodePort: 30083           # Change if port conflicts exist
  
  env:
    OPENAI_MODEL: gpt-4o-mini # Use gpt-4 for better performance
  
  resources:
    limits:
      cpu: 1000m              # Adjust based on load
      memory: 512Mi
```

## Support

For issues or questions, check:
- Agent logs: `kubectl logs -n portal-survey -l app.kubernetes.io/component=agent`
- API logs: `kubectl logs -n portal-survey -l app.kubernetes.io/component=api`
- Pod events: `kubectl describe pod -n portal-survey <pod-name>`
