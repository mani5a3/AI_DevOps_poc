# Kubernetes Agentic AI

An **autonomous AI agent** that detects, diagnoses, and fixes Kubernetes pod issues automatically using LLM intelligence.

## Overview

This is a **true agentic AI** system (not just rule-based automation):

1. **Collects** ALL logs and Kubernetes data automatically
2. **Analyzes** using LLM to find root cause
3. **Generates** fix commands dynamically (not pre-written)
4. **Fixes** issues until success
5. **Verifies** pod health after each attempt

## Architecture

```
COLLECT -> ANALYZE -> FIX -> VERIFY -> REPEAT
```
       <-- REPEAT --
```

## Features

- **Dynamic Diagnosis**: LLM analyzes ALL logs (not just status)
- **Auto-Fix**: Generates and executes fixes dynamically
- **Self-Healing**: Keeps retrying until pod is healthy
- **Comprehensive**: Handles any issue type (ImagePullBackOff, CrashLoopBackOff, OOMKilled, etc.)
- **Auto-Docs**: Updates documentation after successful fix

## Requirements

- Python 3.8+
- Kubernetes cluster (or kubectl configured)
- Ollama with gemma3:4b model

## Quick Start

### 1. Configure .env
```bash
POD_NAME=my-pod
NAMESPACE=default
LLM_MODEL=gemma3:4b
MAX_ITERATIONS=20
```

### 2. Run the Agent
```bash
python main.py
```

### 3. Watch it fix issues!
The agent will:
- Collect all pod logs and events
- Analyze with LLM
- Execute fixes automatically
- Repeat until healthy

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| POD_NAME | (required) | Pod name to monitor |
| NAMESPACE | default | Kubernetes namespace |
| LLM_MODEL | gemma3:4b | Ollama model |
| MAX_ITERATIONS | 20 | Max fix attempts |
| SLEEP_SECONDS | 10 | Wait between checks |
| AUTO_FIX_ENABLED | true | Enable auto-fixing |

## Supported Issue Types

The agent can diagnose and fix ANY issue:

- **ImagePullBackOff** - Invalid/missing images
- **CrashLoopBackOff** - Container crashes
- **OOMKilled** - Memory limits exceeded
- **Evicted** - Node pressure eviction
- **Pending** - Scheduling failures
- **Terminating** - Stuck termination
- **Service Issues** - No endpoints
- **PVC Issues** - Storage problems
- **Any Unknown Issue** - LLM handles novel problems

## How It Works

### 1. Collection Phase
```python
# Collects all of this:
- Pod status (phase, conditions)
- Container logs (last 200 lines)
- Previous logs (crash recovery)
- Pod events
- Pod describe output
- Node status
- PVC status
- Service endpoints
- Recent errors
```

### 2. Analysis Phase
```
Sends ALL data to LLM:
Issue Type: CrashLoopBackOff
Root Cause: Missing env var DATABASE_URL
Fix: kubectl set env deployment/myapp DATABASE_URL=postgres://...
Confidence: 0.95
```

### 3. Fix Phase
```python
# Executes the generated command
kubectl set env deployment/myapp DATABASE_URL=postgres://...
```

### 4. Verify Phase
```
Checks: phase=Running, all containers ready, no restarts
```

### 5. Repeat
```
If not healthy -> collect new data -> analyze again -> new fix -> verify
```

## Files

| File | Description |
|------|-------------|
| `agent.py` | Main agent loop |
| `collector.py` | Data collection |
| `analyzer.py` | LLM diagnosis |
| `fixer.py` | Fix execution |
| `tools.py` | kubectl operations |
| `prompts.py` | LLM prompts |
| `config.py` | Configuration |
| `main.py` | Entry point |

## Development

### Add New Tool
```python
# In tools.py
def my_new_tool(pod_name: str):
    return run_cmd("kubectl get pod " + pod_name)
```

### Update LLM Model
```bash
export LLM_MODEL=llama3
```

### Debug Mode
```bash
export VERBOSE=true
python main.py
```

## License

MIT

---

Auto-generated: 2026-04-27T22:15:38.359298
