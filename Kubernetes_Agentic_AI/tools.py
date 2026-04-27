"""
Tools Module - kubectl Actions for Kubernetes

Provides all kubectl actions the agent can perform:
- Pod operations (logs, exec, describe, delete)
- Deployment operations (scale, image update, patch)
- Resource queries (PVC, nodes, events)
- YAML operations
"""

import subprocess
import json
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import YAML_FILE_PATH, NAMESPACE, LABEL_SELECTOR, POD_NAME


# ---------------------------
# Helper: Run shell command
# ---------------------------
def run_cmd(cmd: str, timeout: int = 30) -> str:
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {str(e)}"


def run_cmd_json(cmd: str) -> Dict[str, Any]:
    """Run command and parse JSON output."""
    output = run_cmd(cmd)
    try:
        return json.loads(output)
    except:
        return {"error": output, "raw": output}


# ======================
# POD TOOLS
# ======================

def get_pod_status(pod_name: str = None) -> Dict[str, Any]:
    """Get pod status JSON."""
    name = pod_name or POD_NAME
    if not name:
        return {"error": "POD_NAME not set"}

    return run_cmd_json(f"kubectl get pod {name} -n {NAMESPACE} -o json")


def get_pod_logs(pod_name: str = None, tail: int = 200,
                 container: str = None) -> str:
    """Get pod container logs."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: POD_NAME not set"

    cmd = f"kubectl logs {name} -n {NAMESPACE} --tail={tail}"
    if container:
        cmd += f" -c {container}"

    return run_cmd(cmd)


def get_pod_previous_logs(pod_name: str = None, tail: int = 200) -> str:
    """Get previous container logs (for crash recovery)."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: POD_NAME not set"

    return run_cmd(f"kubectl logs {name} -n {NAMESPACE} --previous --tail={tail}")


def get_pod_events(pod_name: str = None) -> str:
    """Get events related to pod."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: Pod name required"

    cmd = (
        f"kubectl get events -n {NAMESPACE} "
        f"--field-selector involvedObject.name={name} "
        f"--sort-by='.lastTimestamp' -o wide"
    )
    return run_cmd(cmd)


def get_pod_describe(pod_name: str = None) -> str:
    """Get full pod description."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: POD_NAME not set"

    return run_cmd(f"kubectl describe pod {name} -n {NAMESPACE}")


def delete_pod(pod_name: str = None, force: bool = False) -> str:
    """Delete a pod."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: POD_NAME not set"

    cmd = f"kubectl delete pod {name} -n {NAMESPACE}"
    if force:
        cmd += " --grace-period=0 --force"

    return run_cmd(cmd)


def exec_in_pod(pod_name: str = None, container: str = None,
                command: str = "/bin/sh") -> str:
    """Execute command in pod."""
    name = pod_name or POD_NAME
    if not name:
        return "ERROR: POD_NAME not set"

    cmd = f"kubectl exec {name} -n {NAMESPACE}"
    if container:
        cmd += f" -c {container}"
    cmd += f" -- {command}"

    return run_cmd(cmd)


# ======================
# DEPLOYMENT TOOLS
# ======================

def get_deployments() -> str:
    """Get deployments in namespace."""
    return run_cmd(f"kubectl get deployments -n {NAMESPACE} -o wide")


def get_deployment_yaml(deployment: str) -> str:
    """Get deployment YAML."""
    return run_cmd(f"kubectl get deployment {deployment} -n {NAMESPACE} -o yaml")


def scale_deployment(deployment: str, replicas: int) -> str:
    """Scale deployment."""
    return run_cmd(
        f"kubectl scale deployment {deployment} -n {NAMESPACE} --replicas={replicas}"
    )


def update_deployment_image(deployment: str, container: str,
                           new_image: str) -> str:
    """Update deployment container image."""
    return run_cmd(
        f"kubectl set image deployment/{deployment} {container}={new_image}"
    )


def patch_deployment(deployment: str, patch: str, patch_type: str = "strategic") -> str:
    """Patch deployment."""
    patch_flag = f"--{patch_type}-merge" if patch_type == "strategic" else ""
    return run_cmd(
        f"kubectl patch deployment {deployment} -n {NAMESPACE} {patch_flag} -p '{patch}'"
    )


def rollout_status(deployment: str) -> str:
    """Get deployment rollout status."""
    return run_cmd(f"kubectl rollout status deployment/{deployment} -n {NAMESPACE}")


def rollout_undo(deployment: str) -> str:
    """Undo deployment rollout."""
    return run_cmd(f"kubectl rollout undo deployment/{deployment} -n {NAMESPACE}")


# ======================
# RESOURCE QUERY TOOLS
# ======================

def get_all_pods() -> str:
    """Get all pods in namespace."""
    return run_cmd(f"kubectl get pods -n {NAMESPACE} -o wide")


def get_pods_json() -> Dict[str, Any]:
    """Get all pods as JSON."""
    return run_cmd_json(f"kubectl get pods -n {NAMESPACE} -o json")


def get_pvc_status() -> str:
    """Get PVC status in namespace."""
    return run_cmd(f"kubectl get pvc -n {NAMESPACE} -o wide")


def get_pv_details() -> str:
    """Get detailed PV info."""
    return run_cmd("kubectl get pv -o wide")


def get_node_status() -> str:
    """Get node status."""
    return run_cmd("kubectl get nodes -o wide")


def get_node_conditions() -> str:
    """Get node conditions."""
    return run_cmd("kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: "
                   "{.status.conditions[*].type}{.status.conditions[*].status}{\"\\n\"}{end}'")


def get_services() -> str:
    """Get services in namespace."""
    return run_cmd(f"kubectl get svc -n {NAMESPACE} -o wide")


def get_endpoints() -> str:
    """Get service endpoints."""
    return run_cmd(f"kubectl get endpoints -n {NAMESPACE} -o wide")


def get_ingresses() -> str:
    """Get ingresses in namespace."""
    return run_cmd(f"kubectl get ingress -n {NAMESPACE} -o wide 2>/dev/null || echo 'No ingresses'")


def get_events(limit: int = 50) -> str:
    """Get recent events."""
    return run_cmd(f"kubectl get events -n {NAMESPACE} --sort-by='.lastTimestamp' | tail -{limit}")


def get_recent_errors(minutes: int = 30) -> str:
    """Get recent error events."""
    return run_cmd(
        f"kubectl get events -n {NAMESPACE} "
        f"--field-selector type=Warning "
        f"--since={minutes}m -o wide"
    )


# ======================
# YAML TOOLS
# ======================

def apply_yaml(yaml_path: str = None) -> str:
    """Apply YAML file."""
    path = yaml_path or YAML_FILE_PATH
    if not path:
        return "ERROR: YAML_FILE_PATH not set"

    return run_cmd(f"kubectl apply -f {path} -n {NAMESPACE}")


def delete_yaml(yaml_path: str = None) -> str:
    """Delete YAML file."""
    path = yaml_path or YAML_FILE_PATH
    if not path:
        return "ERROR: YAML_FILE_PATH not set"

    return run_cmd(f"kubectl delete -f {path} -n {NAMESPACE}")


def load_yaml(yaml_path: str = None) -> Dict[str, Any]:
    """Load YAML file."""
    path = yaml_path or YAML_FILE_PATH
    if not path:
        return {"error": "YAML_FILE_PATH not set"}

    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {"error": str(e)}


def save_yaml(data: Dict[str, Any], yaml_path: str = None) -> str:
    """Save YAML file."""
    path = yaml_path or YAML_FILE_PATH
    if not path:
        return "ERROR: YAML_FILE_PATH not set"

    try:
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        return f"Saved to {path}"
    except Exception as e:
        return f"ERROR: {str(e)}"


# ======================
# HEALTH CHECK
# ======================

def is_pod_healthy(pod_name: str = None, max_restarts: int = 3) -> bool:
    """Check if pod is healthy."""
    name = pod_name or POD_NAME
    if not name:
        return False

    pod = get_pod_status(name)
    if "error" in pod:
        return False

    # Check phase
    phase = pod.get("status", {}).get("phase")
    if phase != "Running":
        return False

    # Check containers ready
    container_statuses = pod.get("status", {}).get("containerStatuses", [])
    for cs in container_statuses:
        if not cs.get("ready", False):
            return False
        if cs.get("restartCount", 0) > max_restarts:
            return False

    return True


def get_pod_health_status(pod_name: str = None) -> Dict[str, Any]:
    """Get detailed health status."""
    name = pod_name or POD_NAME
    if not name:
        return {"error": "POD_NAME not set"}

    pod = get_pod_status(name)
    if "error" in pod:
        return pod

    phase = pod.get("status", {}).get("phase")
    container_statuses = pod.get("status", {}).get("containerStatuses", [])

    all_ready = all(cs.get("ready", False) for cs in container_statuses)
    total_restarts = sum(cs.get("restartCount", 0) for cs in container_statuses)

    return {
        "pod_name": name,
        "phase": phase,
        "all_containers_ready": all_ready,
        "total_restarts": total_restarts,
        "healthy": phase == "Running" and all_ready
    }


# ======================
# Tool Registry
# ======================

# Pod tools
pod_tools = {
    "get_pod_status": get_pod_status,
    "get_pod_logs": get_pod_logs,
    "get_pod_events": get_pod_events,
    "get_pod_describe": get_pod_describe,
    "delete_pod": delete_pod,
    "exec_in_pod": exec_in_pod,
    "is_pod_healthy": is_pod_healthy,
    "get_pod_health_status": get_pod_health_status,
}

# Deployment tools
deployment_tools = {
    "get_deployments": get_deployments,
    "get_deployment_yaml": get_deployment_yaml,
    "scale_deployment": scale_deployment,
    "update_deployment_image": update_deployment_image,
    "patch_deployment": patch_deployment,
    "rollout_status": rollout_status,
}

# Resource tools
resource_tools = {
    "get_all_pods": get_all_pods,
    "get_pvc_status": get_pvc_status,
    "get_node_status": get_node_status,
    "get_services": get_services,
    "get_endpoints": get_endpoints,
    "get_events": get_events,
}

# YAML tools
yaml_tools = {
    "apply_yaml": apply_yaml,
    "delete_yaml": delete_yaml,
    "load_yaml": load_yaml,
    "save_yaml": save_yaml,
}

# All tools combined
tools = {**pod_tools, **deployment_tools, **resource_tools, **yaml_tools}


# ======================
# Utility Functions
# ======================

def get_tool_list() -> List[str]:
    """Get list of all available tools."""
    return list(tools.keys())


def execute_tool(tool_name: str, *args, **kwargs) -> Any:
    """Execute a tool by name."""
    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    tool = tools[tool_name]
    try:
        return tool(*args, **kwargs)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test tools
    print("Available tools:", get_tool_list())
    print("\nPod health:", is_pod_healthy())