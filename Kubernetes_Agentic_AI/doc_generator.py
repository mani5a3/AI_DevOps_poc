"""
Documentation Generator - Auto-generate CLAUDE.md and README.md

Generates complete documentation based on current implementation.
"""

import os
from datetime import datetime
from config import (
    NAMESPACE, POD_NAME, LLM_MODEL, MAX_ITERATIONS,
    SLEEP_SECONDS, AUTO_FIX_ENABLED
)
from tools import get_tool_list


def generate_claude_md() -> str:
    """Generate CLAUDE.md for Claude Code."""

    tools_list = get_tool_list()

    content = f"""# CLAUDE.md - Kubernetes Agentic AI

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
{chr(10).join(f'- `{t}`' for t in ['get_pod_status', 'get_pod_logs', 'get_pod_events', 'get_pod_describe', 'delete_pod', 'exec_in_pod', 'is_pod_healthy'])}

### Deployment Tools
{chr(10).join(f'- `{t}`' for t in ['scale_deployment', 'update_deployment_image', 'patch_deployment'])}

### Resource Tools
{chr(10).join(f'- `{t}`' for t in ['get_all_pods', 'get_pvc_status', 'get_node_status', 'get_events'])}

### YAML Tools
{chr(10).join(f'- `{t}`' for t in ['apply_yaml', 'load_yaml', 'save_yaml'])}

## LLM Integration

Uses Ollama with {LLM_MODEL} for:
- Root cause analysis
- Fix command generation
- Health verification

## Success Criteria

- Pod phase = Running
- All containers ready = true
- No container restarts (or minimal)

## Auto-Documentation

This file is auto-generated. Run with `AUTO_UPDATE_DOCS=true` to regenerate.
Last updated: {datetime.now().isoformat()}
"""

    return content


def generate_readme_md() -> str:
    """Generate README.md."""

    content = f"""# Kubernetes Agentic AI

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
- Ollama with {LLM_MODEL} model

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

Auto-generated: {datetime.now().isoformat()}
"""

    return content


def generate_all_docs():
    """Generate all documentation files."""

    # Generate CLAUDE.md
    claude_content = generate_claude_md()
    with open("CLAUDE.md", "w", encoding="utf-8") as f:
        f.write(claude_content)
    print("Generated CLAUDE.md")

    # Generate README.md
    readme_content = generate_readme_md()
    with open("README.MD", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Generated README.MD")


if __name__ == "__main__":
    generate_all_docs()
    print("\nDocumentation generated!")