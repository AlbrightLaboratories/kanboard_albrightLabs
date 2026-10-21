# Deployment Guide - Kanboard AlbrightLabs

Deploy the Kanboard dashboard to your Kubeadm cluster.

## Prerequisites

- kubectl configured for your cluster
- Access to the hr-project-tracking namespace
- Secrets configured (API tokens, GitHub tokens)

## Quick Deploy

```bash
# Clone the repo
git clone https://github.com/AlbrightLaboratories/kanboard_albrightLabs.git
cd kanboard_albrightLabs

# Create secrets (edit the template first!)
cp k8s/secrets.yaml.template k8s/secrets.yaml
# Edit k8s/secrets.yaml with your actual tokens
kubectl apply -f k8s/secrets.yaml

# Deploy everything
kubectl apply -k k8s/

# Wait for pods to be ready
kubectl rollout status deployment/kanboard -n hr-project-tracking
kubectl rollout status deployment/kanboard-ui -n hr-project-tracking
kubectl rollout status deployment/kanboard-backend -n hr-project-tracking
kubectl rollout status deployment/kanboard-mcp -n hr-project-tracking
```

## Access the Dashboard

### Option 1: NodePort (Direct Access)

The kanboard-ui service is exposed on NodePort 30080:

```bash
# Get your node IP
kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}'

# Access the dashboard
http://<node-ip>:30080
```

### Option 2: Port Forward (Local Development)

```bash
kubectl port-forward svc/kanboard-ui -n hr-project-tracking 3000:3000
# Access at http://localhost:3000
```

### Option 3: Ingress (with DNS)

If you have an ingress controller configured:

```bash
# Add to /etc/hosts (or DNS)
<node-ip>  kanboard.local
<node-ip>  kanboard-api.local
<node-ip>  maestro.local

# Access the dashboard
http://kanboard.local
```

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n hr-project-tracking

# Expected output:
# NAME                               READY   STATUS    RESTARTS   AGE
# kanboard-xxxxx                     1/1     Running   0          1m
# kanboard-ui-xxxxx                  1/1     Running   0          1m
# kanboard-backend-xxxxx             1/1     Running   0          1m
# kanboard-mcp-xxxxx                 1/1     Running   0          1m

# Check services
kubectl get svc -n hr-project-tracking

# Expected output:
# NAME               TYPE        CLUSTER-IP       PORT(S)          AGE
# kanboard           ClusterIP   10.xxx.xxx.xxx   80/TCP           1m
# kanboard-ui        NodePort    10.xxx.xxx.xxx   3000:30080/TCP   1m
# kanboard-backend   ClusterIP   10.xxx.xxx.xxx   8000/TCP,8001/TCP 1m
# kanboard-mcp       ClusterIP   10.xxx.xxx.xxx   3001/TCP         1m
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     hr-project-tracking namespace               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   React UI   │───▶│  Kanboard    │◀───│  kanboard-mcp    │  │
│  │  :3000/30080 │    │  PHP :80     │    │  MCP :3001       │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                    ▲              │
│         │                   │                    │              │
│         │            ┌──────────────┐            │              │
│         └───────────▶│   Backend    │────────────┘              │
│                      │  :8000/:8001 │                           │
│                      └──────────────┘                           │
│                             │                                   │
│                             ▼                                   │
│                      ┌──────────────┐                           │
│                      │   Sandbox    │                           │
│                      │  Namespace   │                           │
│                      └──────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| kanboard-ui | 3000 (NodePort 30080) | React dashboard |
| kanboard | 80 | Kanboard PHP API |
| kanboard-backend | 8000, 8001 | Maestro REST + WebSocket |
| kanboard-mcp | 3001 | MCP Server for Claude |

## Secrets Required

Create `k8s/secrets.yaml` from the template:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kanboard-secrets
  namespace: hr-project-tracking
type: Opaque
stringData:
  api-token: "your-kanboard-api-token"
  github-token: "your-github-token"
```

- **api-token**: Get from Kanboard admin panel (Settings > API)
- **github-token**: Personal access token with repo + workflow permissions

## Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n hr-project-tracking

# Check logs
kubectl logs <pod-name> -n hr-project-tracking
```

### Can't access dashboard

```bash
# Verify service is running
kubectl get svc kanboard-ui -n hr-project-tracking

# Check node port is open
kubectl get nodes -o wide
# Access http://<external-ip>:30080
```

### Kanboard API errors

```bash
# Check kanboard pod logs
kubectl logs -l app.kubernetes.io/name=kanboard -n hr-project-tracking

# Verify PVC is bound
kubectl get pvc -n hr-project-tracking
```

## Update Deployment

The deploy workflow triggers on push to main for paths `k8s/**`, `kanboard-ui/**`, `kanboard-mcp/**`, `backend/**`.

Manual trigger:
```bash
gh workflow run deploy -f environment=production
```

## Color Scheme

The dashboard uses semantic colors:
- **Red (#DC2626)**: Failure, error, money loss
- **Yellow (#F59E0B)**: Warning, may impact
- **Green (#10B981)**: Success, working, money making

Dashboard colors:
- **Blue (#2563EB)**: Primary brand
- **White (#FFFFFF)**: Background
- **Gold (#D4AF37)**: Accent/highlights
- **Black (#111827)**: Text
