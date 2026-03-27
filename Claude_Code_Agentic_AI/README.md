# Kubernetes Agentic AI

An autonomous AI agent for Kubernetes that automatically detects, diagnoses, and fixes common pod issues including:

- **ImagePullBackOff** - Invalid or missing container images
- **CrashLoopBackOff** - Application crashes on startup
- **OOMKilled** - Out of Memory terminations
- **Evicted** - Pod evictions due to resource pressure
- **Pending** - Pod scheduling issues

## Features

- Continuous monitoring of Kubernetes pods
- Automatic diagnosis of failure reasons
- Auto-fix capabilities with configurable strategies
- Automatic redeployment and verification
- Dry-run mode for testing
- Backup of original deployment files before modifications

## Requirements

- Python 3.8+
- Kubernetes cluster (or kubectl configured locally)
- `kubectl` command-line tool

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the agent (optional):

Edit `config.yaml` to customize:
- Namespace to monitor
- Check interval
- Fix strategies
- Resource limits

## Usage

### Run the Agent (Continuous Mode)

```bash
# Monitor default namespace
python kubernetes_agent.py

# Monitor specific namespace
python kubernetes_agent.py --namespace my-app

# Dry-run mode (detect issues but don't fix)
python kubernetes_agent.py --dry-run

# Use custom config
python kubernetes_agent.py --config my-config.yaml
```

### Run Once (One-time Scan)

```bash
# Detect issues once and exit
python kubernetes_agent.py --once

# With specific namespace
python kubernetes_agent.py --namespace default --once
```

## Configuration

Edit `config.yaml` to customize the agent behavior:

```yaml
kubernetes:
  namespace: default          # Namespace to monitor
  check_interval_seconds: 30 # How often to check for issues
  max_retries: 5             # Max retry attempts
  timeout_seconds: 300       # Timeout for waiting on pod states

agent:
  dry_run: false             # Don't apply fixes
  auto_fix_enabled: true     # Enable auto-fixing
  log_level: INFO            # Logging level

fix_strategies:
  image_pull_backoff:
    action: update_image_tag
    fallback_image: nginx:latest
    max_retries: 3

  crash_loop_backoff:
    action: analyze_and_fix
    increase_resources: true

  oom_killed:
    action: increase_memory
    memory_increase_factor: 2.0
    max_memory_limit: 4Gi
```

## Sample Deployments

The `deployments/` directory contains sample deployments with intentional issues:

| File | Issue Type | Description |
|------|------------|-------------|
| `webapp.yaml` | ImagePullBackOff | Invalid image tag |
| `api.yaml` | CrashLoopBackOff | Missing environment variable |
| `worker.yaml` | OOMKilled | Insufficient memory limit |

Deploy samples to test:

```bash
kubectl apply -f deployments/webapp.yaml
kubectl apply -f deployments/api.yaml
kubectl apply -f deployments/worker.yaml
```

## How It Works

1. **Detection**: The agent polls Kubernetes for pods with issues
2. **Diagnosis**: Analyzes events and logs to determine root cause
3. **Fix**: Applies appropriate fix based on issue type:
   - ImagePullBackOff: Updates image tag or uses fallback
   - CrashLoopBackOff: Adds startup probes, adjusts resources
   - OOMKilled: Increases memory limits
   - Pending: Adds tolerations, adjusts scheduling
4. **Redeploy**: Applies the fixed configuration
5. **Verify**: Waits for pod to reach Running state

## Running Inside Kubernetes

Create a Kubernetes deployment to run the agent in-cluster:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8s-agent
  template:
    metadata:
      labels:
        app: k8s-agent
    spec:
      serviceAccountName: k8s-agent  # Create RBAC rules
      containers:
      - name: agent
        image: your-registry/k8s-agent:latest
        env:
        - name: NAMESPACE
          value: "default"
```

Create RBAC rules for the agent:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8s-agent

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: k8s-agent
rules:
- apiGroups: [""]
  resources: ["pods", "events"]
  verbs: ["get", "list", "watch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "patch", "update"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: k8s-agent
subjects:
- kind: ServiceAccount
  name: k8s-agent
roleRef:
  kind: Role
  name: k8s-agent
  apiGroup: rbac.authorization.k8s.io
```

## Logs

The agent logs all actions to stdout. Monitor with:

```bash
kubectl logs -f deployment/k8s-agent
```

## Development

### Adding New Fix Strategies

To add support for new issue types:

1. Add issue detection in `_detect_pod_issues()` method
2. Add fix method (e.g., `_fix_new_issue_type()`)
3. Add fix strategy in `config.yaml`
4. Update `fix_issue()` method to call new fix

## License

MIT