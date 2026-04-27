# CLAUDE.md - Kubernetes Agentic AI

## Project Overview

- **Project Name**: Kubernetes Agentic AI
- **Type**: Autonomous DevOps Agent
- **Core Functionality**: Self-healing Kubernetes pod that detects, diagnoses, and fixes issues automatically using LLM
- **Target Users**: DevOps engineers, SREs, Platform teams

## Architecture

### Agent Loop
```
COLLECT -> ANALYZE -> FIX -> VERIFY -> REPEAT
```

1. **COLLECT**: Gathers all Kubernetes data (pod logs, events, describe, PVC, nodes)
2. **ANALYZE**: Uses LLM to diagnose root cause and generate fix
3. **FIX**: Executes kubectl commands to fix the issue
4. **VERIFY**: Checks if pod is healthy
5. **REPEAT**: Loops until success or max iterations

### Components

| File | Purpose |
|------|---------|
| `agent.py` | Main agent loop |
| `collector.py` | Collects all K8s data |
| `analyzer.py` | LLM-driven diagnosis |
| `fixer.py` | Executes fixes |
| `tools.py` | kubectl operations |
| `prompts.py` | LLM system prompts |
| `config.py` | Configuration |
| `doc_generator.py` | Auto-generates docs |

## Commands

### Run Agent (Continuous)
```bash
python main.py
```

### Run Diagnosis Only
```bash
python main.py --diagnose
```

### With Environment
```bash
export POD_NAME=my-pod
export NAMESPACE=default
export LLM_MODEL=gemma3:4b
python main.py
```

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| POD_NAME | (required) | Pod to monitor |
| NAMESPACE | default | Kubernetes namespace |
| LLM_MODEL | gemma3:4b | LLM model to use |
| MAX_ITERATIONS | 20 | Max retry attempts |
| SLEEP_SECONDS | 10 | Wait between checks |
| AUTO_FIX_ENABLED | true | Enable auto-fixing |

## Available Tools

### Pod Tools
- `get_pod_status`
- `get_pod_logs`
- `get_pod_events`
- `get_pod_describe`
- `delete_pod`
- `exec_in_pod`
- `is_pod_healthy`

### Deployment Tools
- `scale_deployment`
- `update_deployment_image`
- `patch_deployment`

### Resource Tools
- `get_all_pods`
- `get_pvc_status`
- `get_node_status`
- `get_events`

### YAML Tools
- `apply_yaml`
- `load_yaml`
- `save_yaml`

## LLM Integration

Uses Ollama with gemma3:4b for:
- Root cause analysis
- Fix command generation
- Health verification

## Success Criteria

- Pod phase = Running
- All containers ready = true
- No container restarts (or minimal)

## Auto-Documentation

This file is auto-generated. Run with `AUTO_UPDATE_DOCS=true` to regenerate.
Last updated: 2026-04-27T22:15:38.359298
