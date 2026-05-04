# PORTAL SURVEY APPLICATION
## Deployment Guide: React App + FastAPI on AWS using Rancher & Helm

---

**Document Information:**
- **Docker Hub Username:** viveksarvagod
- **AWS Account ID:** 101945099861
- **Image Registry:** Docker Hub (public images)
- **Kubernetes Provider:** Rancher on AWS EC2

---

## TABLE OF CONTENTS

1. Part 1: Prerequisites & Dependencies
2. Part 2: Step-by-Step Deployment Guide
3. Part 3: Create New Cluster & Migrate from Old Cluster
4. Part 4: Troubleshooting Guide
5. Part 5: Quick Reference Commands
6. Part 6: Deployment Checklist

---

# PART 1: PREREQUISITES & DEPENDENCIES

## 1.1 Project Folder Structure

```
645-Assignment-3/
├── portal-survey-api/          [FastAPI Backend Service]
│   ├── docker/
│   │   └── Dockerfile
│   ├── src/
│   └── requirements.txt
│
├── portal-survey-ui/           [React Frontend Application]
│   ├── docker/
│   │   └── Dockerfile
│   ├── src/
│   └── package.json
│
└── portal-charts/              [Helm Charts]
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
```

## 1.2 System Requirements

- Docker Desktop installed and running
- kubectl (Kubernetes CLI) v1.24+
- helm (v3.x) installed
- Rancher deployed on AWS EC2
- Kubernetes cluster created in Rancher
- Docker Hub account (viveksarvagod)
- AWS Academic Lab account

## 1.3 Installation Commands

### Install kubectl (macOS)
```bash
brew install kubectl
kubectl version --client
```

### Install Helm (macOS)
```bash
brew install helm
helm version
```

---

# PART 2: STEP-BY-STEP DEPLOYMENT GUIDE

## PHASE 1: BUILD AND PUSH DOCKER IMAGES

### Step 1: Build and Push API Image

```bash
cd /path/to/645-Assignment-3
docker login
cd portal-survey-api
docker build -t viveksarvagod/portal-survey-api:latest -f docker/Dockerfile .
docker push viveksarvagod/portal-survey-api:latest
```

**VERIFY:** https://hub.docker.com/r/viveksarvagod/portal-survey-api

### Step 2: Build and Push UI Image

```bash
cd ../portal-survey-ui
docker build -t viveksarvagod/portal-survey-ui:latest -f docker/Dockerfile .
docker push viveksarvagod/portal-survey-ui:latest
```

**VERIFY:** https://hub.docker.com/r/viveksarvagod/portal-survey-ui

---

## PHASE 2: PREPARE KUBERNETES SECRETS

### Step 3: Generate Database Secrets

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encode credentials to base64
echo -n "your-db-host" | base64
echo -n "your-db-username" | base64
echo -n "your-db-password" | base64
echo -n "your-jwt-secret" | base64
```

### Step 4: Update values.yaml

**FILE:** portal-charts/values.yaml

```yaml
secrets:
  api:
    DB_HOST: "BASE64_ENCODED_HOST"
    DB_USER: "BASE64_ENCODED_USER"
    DB_PASSWORD: "BASE64_ENCODED_PASSWORD"
    JWT_SECRET_KEY: "BASE64_ENCODED_JWT"
```

---

## PHASE 3: CONNECT TO RANCHER CLUSTER

### Step 5: Download Kubeconfig from Rancher

1. Open: http://YOUR_RANCHER_IP
2. Click your cluster
3. Click "Copy KubeConfig"
4. Save to: ~/.kube/rancher-config

### Step 6: Verify Cluster Access

```bash
export KUBECONFIG=~/.kube/rancher-config
kubectl cluster-info
kubectl get nodes
```

---

## PHASE 4: DEPLOY WITH HELM

### Step 7: Deploy Application

```bash
cd /path/to/645-Assignment-3/portal-charts
kubectl create namespace portal-survey
helm install portal-survey . -n portal-survey
```

### Step 8: Verify Deployment

```bash
kubectl get pods -n portal-survey
kubectl get svc -n portal-survey
kubectl logs -n portal-survey -l app.kubernetes.io/name=portal-survey-api -f
```

---

## PHASE 5: ACCESS APPLICATIONS

### Step 9: Port Forward to Applications

**Access UI:**
```bash
kubectl port-forward -n portal-survey svc/portal-survey-ui 3000:80
# Open: http://localhost:3000
```

**Access API:**
```bash
kubectl port-forward -n portal-survey svc/portal-survey-api 8000:8000
# Open: http://localhost:8000/docs
```

---

# PART 3: CREATE NEW CLUSTER & MIGRATE FROM OLD CLUSTER

## Important: Clean Cluster Strategy

**Context:** You have an old cluster from a previous assignment with running pods/nodes.
**Solution:** Create a new cluster for this assignment, verify it works, then delete the old cluster.

**Benefits:**
- ✅ Clean environment (no interference from old assignment)
- ✅ Easy to test and verify before cleanup
- ✅ Low risk (old cluster still available if something goes wrong)
- ✅ Proper separation between assignments

---

## PHASE 1: CREATE NEW CLUSTER

### Step 10: Create New Kubernetes Cluster in Rancher

**Option A: Using Rancher UI (RECOMMENDED - EASIEST)**

```
1. Open Rancher Dashboard: http://YOUR_RANCHER_IP
2. Click "Clusters" in left navigation
3. Click blue "Create" button
4. Select "Amazon EC2" as provider
5. Fill in cluster configuration:
   - Cluster Name: portal-survey-prod (or assignment-3-cluster)
   - Kubernetes Version: v1.30
   - Number of Nodes: 1
   - Node Instance Type: t3.small (cost-effective)
   - Region: us-east-1
6. Click "Create" button
7. Wait for status to become "Active" (10-15 minutes)
8. Rancher will automatically show kubeconfig download option
```

** IMPORTANT: Manual UI approach is recommended - simplest and most reliable!**

---

### Option B: Using Rancher API/CLI (ADVANCED - Optional)

If you want to create cluster via command line:

```bash
# REQUIRES: Rancher API token and environment setup
# This is optional - UI method is simpler!

# 1. Set environment variables
export RANCHER_URL="https://YOUR_RANCHER_IP"
export RANCHER_ACCESS_KEY="your-api-key"
export RANCHER_SECRET_KEY="your-secret-key"

# 2. Create cluster using API (requires curl or rancher-cli)
curl -X POST "$RANCHER_URL/v3/clusters" \
  -H "Authorization: Bearer $RANCHER_ACCESS_KEY:$RANCHER_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "portal-survey-prod",
    "driver": "amazonec2",
    "amazonec2Config": {
      "instanceType": "t3.small",
      "region": "us-east-1"
    }
  }'

# 3. Wait for cluster to be created
# Check status in Rancher Dashboard
```

**RECOMMENDATION:** Use Option A (Rancher UI) - it's much simpler and doesn't require API setup!

---

## PHASE 2: GET KUBECONFIG & DEPLOY TO NEW CLUSTER

### Step 11: Download Kubeconfig for New Cluster

```bash
# From Rancher Dashboard:
# 1. Select your new cluster (portal-survey-prod)
# 2. Click "Copy KubeConfig" button (top right corner)
# 3. Save to: ~/.kube/rancher-new-config

# Verify the file was saved
cat ~/.kube/rancher-new-config
```

### Step 12: Verify Connection to New Cluster

```bash
# Set kubeconfig to new cluster
export KUBECONFIG=~/.kube/rancher-new-config

# Verify connection to NEW cluster
kubectl cluster-info

# Expected output should show NEW cluster info, NOT the old one

# Check nodes in new cluster
kubectl get nodes

# Should show only new nodes, not old cluster nodes
```

### Step 13: Deploy Portal Survey to New Cluster

```bash
# Make sure you're connected to NEW cluster
echo $KUBECONFIG  # Should be ~/.kube/rancher-new-config

# Navigate to Helm charts
cd /path/to/645-Assignment-3/portal-charts

# Create namespace
kubectl create namespace portal-survey

# Install Helm deployment to NEW cluster
helm install portal-survey . -n portal-survey

# Verify pods are created in new cluster
kubectl get pods -n portal-survey

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# portal-survey-api-xxxxx           1/1     Running   0          2m
# portal-survey-ui-xxxxx            1/1     Running   0          2m
```

### Step 14: Test Application on New Cluster

```bash
# Port forward to UI (new cluster)
kubectl port-forward -n portal-survey svc/portal-survey-ui 3000:80 &

# Port forward to API (new cluster)
kubectl port-forward -n portal-survey svc/portal-survey-api 8000:8000 &

# Test in browser
# UI: http://localhost:3000
# API Docs: http://localhost:8000/docs

# Verify everything works before deleting old cluster
```

---

## PHASE 3: DELETE OLD CLUSTER (CLEANUP)

### Step 15: Verify New Cluster is Working Perfectly

Before deleting old cluster, ensure:
- ✅ New cluster created and "Active" in Rancher
- ✅ Pods running in new cluster
- ✅ UI accessible and responsive
- ✅ API responding correctly
- ✅ Database connection working
- ✅ All tests passed

### Step 16: Delete Old Cluster from Rancher

```bash
# OPTION A: Using Rancher UI (RECOMMENDED)
1. Go to Rancher Dashboard: http://YOUR_RANCHER_IP
2. Click "Clusters" in left menu
3. Find your OLD cluster (the one from previous assignment)
4. Click on the cluster name to select it
5. Click "Delete" button (or three-dot menu → Delete)
6. Confirm deletion by typing cluster name if prompted
7. Wait for cluster to be completely removed (5-10 minutes)

# During deletion, Rancher will automatically:
# - Stop all pods and services in old cluster
# - Delete all Kubernetes resources
# - Terminate associated EC2 instances
# - Clean up AWS resources and load balancers
```

**⚠️ IMPORTANT WARNINGS:**
- ⚠️ Deletion is PERMANENT - all data in old cluster will be lost
- ⚠️ Do this ONLY after confirming new cluster is working
- ⚠️ This will also stop AWS EC2 instances and you won't be charged
- ⚠️ If you still need old cluster, keep it running

### Step 17: Verify Old Cluster is Deleted

```bash
# From Rancher Dashboard
1. Go to "Clusters" menu
2. Confirm old cluster is no longer listed
3. Only new cluster (portal-survey-prod) should be visible
4. Check AWS EC2 console - old instances should be terminated
```

---

## TROUBLESHOOTING: SWITCHING BETWEEN CLUSTERS

If you need to switch between clusters during testing:

```bash
# List all available kubeconfig contexts
kubectl config get-contexts

# OUTPUT example:
# CURRENT   NAME              CLUSTER    
# *         rancher-new       ...
#           rancher-old       ...

# Switch to NEW cluster
export KUBECONFIG=~/.kube/rancher-new-config
kubectl cluster-info

# Switch to OLD cluster (if needed for comparison)
export KUBECONFIG=~/.kube/rancher-old-config
kubectl cluster-info

# Verify which cluster you're currently connected to
kubectl config current-context
kubectl get nodes  # Check node names to confirm
```

---

# PART 4: TROUBLESHOOTING GUIDE

## Issue: Pods stuck in "Pending"
```bash
kubectl describe pod [POD_NAME] -n portal-survey
# Check resource constraints and logs
```

## Issue: ImagePullBackOff
- Verify images on Docker Hub
- Check image tag matches values.yaml
- Ensure images are public

## Issue: Database connection errors
- Verify DB credentials in values.yaml
- Ensure database is accessible from cluster
- Check AWS security groups

## Issue: Cannot connect to Rancher
```bash
kubectl config current-context
kubectl cluster-info
# Download kubeconfig again from Rancher Dashboard
```

## Issue: Connected to wrong cluster
```bash
# Verify which cluster you're connected to
kubectl config current-context
kubectl get nodes | head -1

# Switch to correct cluster
export KUBECONFIG=~/.kube/rancher-new-config
kubectl cluster-info
```

---

# PART 5: QUICK REFERENCE COMMANDS

## Docker Commands
```bash
docker login
docker build -t viveksarvagod/portal-survey-api:latest -f docker/Dockerfile .
docker push viveksarvagod/portal-survey-api:latest
docker images
```

## Kubectl Commands
```bash
kubectl cluster-info
kubectl get pods -n portal-survey
kubectl get svc -n portal-survey
kubectl describe pod [POD_NAME] -n portal-survey
kubectl logs [POD_NAME] -n portal-survey -f
kubectl port-forward svc/[SERVICE] 3000:80 -n portal-survey
kubectl config current-context
kubectl config get-contexts
```

## Helm Commands
```bash
helm install portal-survey . -n portal-survey
helm upgrade portal-survey . -n portal-survey
helm uninstall portal-survey -n portal-survey
helm list -n portal-survey
helm lint .
helm template .
```

---

# PART 6: DEPLOYMENT CHECKLIST

## Prerequisites
- ☐ Docker Desktop running
- ☐ kubectl installed
- ☐ Helm installed
- ☐ Docker Hub account ready
- ☐ Rancher server running
- ☐ Old cluster accessible (for reference)

## Docker Images
- ☐ API image built
- ☐ API image pushed to Docker Hub
- ☐ UI image built
- ☐ UI image pushed to Docker Hub
- ☐ Images verified on Docker Hub

## NEW Cluster Creation
- ☐ New cluster created in Rancher UI
- ☐ New cluster status is "Active"
- ☐ Kubeconfig downloaded for new cluster
- ☐ kubectl connected to NEW cluster
- ☐ Can list nodes in new cluster

## Kubernetes Configuration
- ☐ Kubeconfig saved to ~/.kube/rancher-new-config
- ☐ export KUBECONFIG set to new cluster
- ☐ Cluster connectivity verified
- ☐ Different from old cluster confirmed

## Helm Deployment
- ☐ Database credentials gathered
- ☐ Credentials encoded to base64
- ☐ JWT secret key generated
- ☐ values.yaml updated with secrets
- ☐ Chart syntax validated

## Deployment Execution
- ☐ Namespace created in NEW cluster
- ☐ Helm install executed on NEW cluster
- ☐ All pods running in NEW cluster
- ☐ Services created in NEW cluster
- ☐ No pod errors

## Post-Deployment
- ☐ UI accessible on NEW cluster
- ☐ API accessible on NEW cluster
- ☐ Database connectivity confirmed
- ☐ Logs reviewed for errors
- ☐ Application working end-to-end

## OLD Cluster Deletion
- ☐ NEW cluster verified working
- ☐ All testing completed
- ☐ OLD cluster identified in Rancher
- ☐ OLD cluster deleted
- ☐ Deletion confirmed in Rancher Dashboard
- ☐ AWS EC2 instances terminated

---

## Summary of Workflow

```
1. Build & Push Docker Images (Steps 1-2)
           ↓
2. Prepare Database Secrets (Steps 3-4)
           ↓
3. Create NEW Cluster in Rancher (Step 10)
           ↓
4. Download NEW Cluster Kubeconfig (Step 11)
           ↓
5. Deploy to NEW Cluster with Helm (Steps 13-14)
           ↓
6. Test Application on NEW Cluster (Step 14)
           ↓
7. Delete OLD Cluster from Rancher (Step 16)
           ↓
8. Done! Your app is running on clean cluster
```

---

**Document Created:** April 11, 2026
**Last Updated:** April 12, 2026
**Project:** Portal Survey Application (645 Assignment 3)
**Author:** Vivek Sarvagod
