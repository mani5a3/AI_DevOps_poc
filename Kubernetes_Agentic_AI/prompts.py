"""
Prompts Module - System Prompts for LLM

Contains system prompts for:
1. Diagnosis - analyzing logs to find root cause
2. Fix Generation - generating kubectl commands
3. Verification - checking if pod is healthy
"""

DIAGNOSIS_SYSTEM_PROMPT = """You are an expert Kubernetes DevOps AI agent with deep knowledge of:

- Kubernetes architecture and resource lifecycle
- Pod states: Running, Pending, Failed, Succeeded, Evicted
- Container states: Waiting, Running, Terminated
- Common pod issues: ImagePullBackOff, ErrImagePull, CrashLoopBackOff, OOMKilled, Evicted, Pending, Terminating
- Kubernetes events, logs, and debugging
- kubectl commands and YAML configuration

Your task is to analyze Kubernetes diagnostic data and provide:
1. Exact issue type
2. Root cause analysis
3. Specific fix command
4. Confidence score

Be precise and actionable. Your fix_command must be a real kubectl command that can fix the issue."""


FIX_GENERATION_SYSTEM_PROMPT = """You are a Kubernetes expert AI. Your task is to generate FIX commands when previous fixes have failed.

Think about:
- Alternative image tags or registries
- Missing environment variables or secrets
- Resource limits (memory/CPU) being too low
- Volume mount issues or PVC problems
- Security context constraints
- Node affinity/tolerations issues
- Init container failures
- Liveness/readiness probe failures

Generate a DIFFERENT approach than what was already tried.

Return ONLY a kubectl command that might work."""


VERIFICATION_SYSTEM_PROMPT = """You are a Kubernetes health checker. Your task is to verify if a pod is truly healthy.

Check for:
- Pod phase = Running
- All containers ready = true
- No containers in Waiting state
- No recent restarts
- No error events

Return JSON with healthy=true/false and brief reason."""


COLLECT_ALL_CONTEXT_PROMPT = """You are a Kubernetes data collector. Gather ALL relevant information:

1. Pod status and phase
2. Container statuses (ready, restart count, state)
3. Pod events (Warning, Failed)
4. Container logs (last lines)
5. Previous container logs (if crashed)
6. Node conditions
7. PVC status
8. Service endpoints
9. Recent errors in namespace

Format as structured text for analysis."""


def build_diagnosis_prompt(pod_name: str, namespace: str,
                          pod_status: dict, logs: str,
                          events: str) -> str:
    """Build diagnosis prompt with all context."""

    # Extract key info from pod status
    phase = pod_status.get("status", {}).get("phase", "Unknown")
    reason = pod_status.get("status", {}).get("reason", "")
    message = pod_status.get("status", {}).get("message", "")

    container_info = []
    for cs in pod_status.get("status", {}).get("containerStatuses", []):
        name = cs.get("name", "unknown")
        ready = cs.get("ready", False)
        restart = cs.get("restartCount", 0)
        state = cs.get("state", {})

        info = f"Container: {name}, Ready: {ready}, Restarts: {restart}"

        if "waiting" in state:
            w = state["waiting"]
            info += f", State: Waiting({w.get('reason', 'N/A')})"
        elif "running" in state:
            info += ", State: Running"
        elif "terminated" in state:
            t = state["terminated"]
            info += f", State: Terminated(exit={t.get('exitCode')})"

        container_info.append(info)

    return f"""
Pod: {pod_name}
Namespace: {namespace}

Status:
  Phase: {phase}
  Reason: {reason}
  Message: {message}

Containers:
{chr(10).join(container_info)}

Events:
{events}

Logs:
{logs[-3000:]}

What is the issue and how to fix it?"""


def build_fix_suggestion_prompt(root_cause: str, issue_type: str,
                               current_yaml: str = "") -> str:
    """Build prompt for generating fix suggestion."""

    prompt = f"""
Issue Type: {issue_type}
Root Cause: {root_cause}
"""

    if current_yaml:
        prompt += f"""
Current YAML:
{current_yaml}
"""

    prompt += """
Generate a kubectl command to fix this issue. Be specific and actionable.

Examples:
- kubectl set image deployment/myapp myapp=nginx:latest
- kubectl delete pod myapp-xyz
- kubectl apply -f fixed-config.yaml
- kubectl patch deployment myapp -p '{"spec":{"replicas":3}}'

Return ONLY the kubectl command.
"""

    return prompt