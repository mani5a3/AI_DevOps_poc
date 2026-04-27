"""
Collector Module - Comprehensive Kubernetes Data Collection

Collects all relevant data from Kubernetes cluster for LLM analysis:
- Pod status, logs, events, describe
- PVC status, node status
- Service endpoints, ingress
- All unhealthy resources
"""

import subprocess
import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import NAMESPACE, LABEL_SELECTOR, POD_NAME


def run_cmd(cmd: str) -> str:
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out"
    except Exception as e:
        return f"ERROR: {str(e)}"


def get_pod_status() -> Dict[str, Any]:
    """Get pod status JSON."""
    if not POD_NAME:
        return {}

    cmd = f"kubectl get pod {POD_NAME} -n {NAMESPACE} -o json"
    output = run_cmd(cmd)

    try:
        return json.loads(output)
    except:
        return {"error": output}


def get_all_pods_status() -> Dict[str, Any]:
    """Get all pods status in namespace."""
    cmd = f"kubectl get pods -n {NAMESPACE} -o json"
    output = run_cmd(cmd)

    try:
        return json.loads(output)
    except:
        return {"error": output}


def get_pod_logs(tail_lines: int = 200) -> str:
    """Get pod container logs."""
    if not POD_NAME:
        return "ERROR: POD_NAME not set"

    pod_info = get_pod_status()
    if "error" in pod_info:
        return pod_info.get("error", "ERROR: Cannot get pod")

    # Get all container names
    containers = pod_info.get("spec", {}).get("containers", [])
    container_names = [c.get("name") for c in containers]

    logs = []
    for container in container_names:
        cmd = f"kubectl logs {POD_NAME} -n {NAMESPACE} -c {container} --tail={tail_lines}"
        output = run_cmd(cmd)
        logs.append(f"=== Container: {container} ===\n{output}")

    return "\n\n".join(logs)


def get_pod_previous_logs(tail_lines: int = 200) -> str:
    """Get previous container logs (for crash recovery)."""
    if not POD_NAME:
        return "ERROR: POD_NAME not set"

    pod_info = get_pod_status()
    if "error" in pod_info:
        return ""

    containers = pod_info.get("spec", {}).get("containers", [])
    container_names = [c.get("name") for c in containers]

    logs = []
    for container in container_names:
        cmd = f"kubectl logs {POD_NAME} -n {NAMESPACE} -c {container} --previous --tail={tail_lines}"
        output = run_cmd(cmd)
        if output.strip():
            logs.append(f"=== Previous Container: {container} ===\n{output}")

    return "\n\n".join(logs)


def get_pod_events() -> str:
    """Get events related to pod."""
    if not POD_NAME:
        return "ERROR: POD_NAME not set"

    cmd = (
        f"kubectl get events -n {NAMESPACE} "
        f"--field-selector involvedObject.name={POD_NAME} "
        f"--sort-by='.lastTimestamp' "
        f"-o wide"
    )
    return run_cmd(cmd)


def get_pod_describe() -> str:
    """Get full pod description."""
    if not POD_NAME:
        return "ERROR: POD_NAME not set"

    cmd = f"kubectl describe pod {POD_NAME} -n {NAMESPACE}"
    return run_cmd(cmd)


def get_node_status() -> str:
    """Get node status."""
    cmd = "kubectl get nodes -o wide"
    return run_cmd(cmd)


def get_node_conditions() -> str:
    """Get node conditions for all nodes."""
    cmd = "kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.conditions[*].type}{.status.conditions[*].status}{\"\\n\"}{end}'"
    return run_cmd(cmd)


def get_pvc_status() -> str:
    """Get PVC status in namespace."""
    cmd = f"kubectl get pvc -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_pv_details() -> str:
    """Get detailed PV info."""
    cmd = "kubectl get pv -o wide"
    return run_cmd(cmd)


def get_service_endpoints() -> str:
    """Get service endpoints."""
    cmd = f"kubectl get endpoints -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_services() -> str:
    """Get services in namespace."""
    cmd = f"kubectl get svc -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_ingresses() -> str:
    """Get ingresses in namespace."""
    cmd = f"kubectl get ingress -n {NAMESPACE} -o wide 2>/dev/null || echo 'No ingresses'"
    return run_cmd(cmd)


def get_deployments() -> str:
    """Get deployments in namespace."""
    cmd = f"kubectl get deployments -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_replica_sets() -> str:
    """Get replica sets in namespace."""
    cmd = f"kubectl get rs -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_configmaps() -> str:
    """Get configmaps in namespace."""
    cmd = f"kubectl get configmaps -n {NAMESPACE} -o wide"
    return run_cmd(cmd)


def get_secrets() -> str:
    """Get secrets in namespace."""
    cmd = f"kubectl get secrets -n {NAMESPACE} 2>/dev/null || echo 'No secrets access'"
    return run_cmd(cmd)


def get_recent_errors(minutes: int = 30) -> str:
    """Get recent error events in namespace."""
    since = (datetime.now() - timedelta(minutes=minutes)).isoformat()

    cmd = (
        f"kubectl get events -n {NAMESPACE} "
        f"--since={since} "
        f"--field-selector type=Warning "
        f"-o wide"
    )
    return run_cmd(cmd)


def get_all_unhealthy_resources() -> str:
    """Get all unhealthy resources in namespace."""
    output = []

    # Pods not Running
    cmd = f"kubectl get pods -n {NAMESPACE} -o json"
    pods_output = run_cmd(cmd)
    try:
        pods = json.loads(pods_output).get("items", [])
        unhealthy = [p for p in pods if p.get("status", {}).get("phase") != "Running"]
        if unhealthy:
            output.append("=== Unhealthy Pods ===")
            for p in unhealthy:
                phase = p.get("status", {}).get("phase")
                name = p.get("metadata", {}).get("name")
                output.append(f"{name}: {phase}")
    except:
        pass

    # PVCs not Bound
    cmd = f"kubectl get pvc -n {NAMESPACE} -o json"
    pvc_output = run_cmd(cmd)
    try:
        pvcs = json.loads(pvc_output).get("items", [])
        unbound = [p for p in pvcs if p.get("status", {}).get("phase") != "Bound"]
        if unbound:
            output.append("\n=== Unbound PVCs ===")
            for p in unbound:
                phase = p.get("status", {}).get("phase")
                name = p.get("metadata", {}).get("name")
                output.append(f"{name}: {phase}")
    except:
        pass

    # Deployments with unavailable replicas
    cmd = f"kubectl get deployments -n {NAMESPACE} -o json"
    deploy_output = run_cmd(cmd)
    try:
        deploys = json.loads(deploy_output).get("items", [])
        unavailable = [
            d for d in deploys
            if d.get("status", {}).get("unavailableReplicas", 0) > 0
        ]
        if unavailable:
            output.append("\n=== Deployments with Issues ===")
            for d in unavailable:
                name = d.get("metadata", {}).get("name")
                unavail = d.get("status", {}).get("unavailableReplicas")
                output.append(f"{name}: {unavail} unavailable replicas")
    except:
        pass

    return "\n".join(output) if output else "All resources appear healthy"


def get_resource_limits() -> str:
    """Get resource limits and requests for pod."""
    if not POD_NAME:
        return "ERROR: POD_NAME not set"

    cmd = f"kubectl get pod {POD_NAME} -n {NAMESPACE} -o jsonpath='{{.spec.containers[*].name}}:{{.spec.containers[*].resources.limits}}:{{.spec.containers[*].resources.requests}}'"
    return run_cmd(cmd)


def collect_all_data() -> Dict[str, Any]:
    """
    Collect all relevant data for LLM analysis.

    Returns a dictionary with all collected information.
    """
    data = {
        "collection_time": datetime.now().isoformat(),
        "namespace": NAMESPACE,
        "pod_name": POD_NAME,
    }

    # Core pod data
    data["pod_status"] = get_pod_status()
    data["pod_logs"] = get_pod_logs()
    data["pod_previous_logs"] = get_pod_previous_logs()
    data["pod_events"] = get_pod_events()
    data["pod_describe"] = get_pod_describe()

    # Cluster-wide data
    data["node_status"] = get_node_status()
    data["pvc_status"] = get_pvc_status()
    data["service_endpoints"] = get_service_endpoints()
    data["services"] = get_services()
    data["deployments"] = get_deployments()
    data["recent_errors"] = get_recent_errors()

    # Unhealthy resources
    data["unhealthy_resources"] = get_all_unhealthy_resources()

    return data


def format_for_llm(data: Dict[str, Any]) -> str:
    """
    Format collected data for LLM consumption.

    Creates a structured prompt with all relevant information.
    """
    lines = [
        "=" * 60,
        "KUBERNETES AGENTIC AI - DIAGNOSIS DATA",
        "=" * 60,
        f"Namespace: {data.get('namespace', 'N/A')}",
        f"Pod Name: {data.get('pod_name', 'N/A')}",
        f"Collection Time: {data.get('collection_time', 'N/A')}",
        "=" * 60,
    ]

    # Pod Status
    pod_status = data.get("pod_status", {})
    if "error" not in pod_status:
        phase = pod_status.get("status", {}).get("phase", "Unknown")
        reason = pod_status.get("status", {}).get("reason", "")
        message = pod_status.get("status", {}).get("message", "")

        lines.append("\n### POD STATUS ###")
        lines.append(f"Phase: {phase}")
        if reason:
            lines.append(f"Reason: {reason}")
        if message:
            lines.append(f"Message: {message}")

        # Container statuses
        container_statuses = pod_status.get("status", {}).get("containerStatuses", [])
        for cs in container_statuses:
            name = cs.get("name", "unknown")
            ready = cs.get("ready", False)
            restart_count = cs.get("restartCount", 0)
            state = cs.get("state", {})

            lines.append(f"\nContainer: {name}")
            lines.append(f"  Ready: {ready}")
            lines.append(f"  Restarts: {restart_count}")

            if "waiting" in state:
                w = state["waiting"]
                lines.append(f"  State: Waiting")
                lines.append(f"    Reason: {w.get('reason', 'N/A')}")
                lines.append(f"    Message: {w.get('message', 'N/A')}")
            elif "running" in state:
                lines.append(f"  State: Running")
            elif "terminated" in state:
                t = state["terminated"]
                lines.append(f"  State: Terminated")
                lines.append(f"    Exit Code: {t.get('exitCode', 'N/A')}")
                lines.append(f"    Reason: {t.get('reason', 'N/A')}")

    # Pod Logs
    logs = data.get("pod_logs", "")
    if logs and "ERROR" not in logs[:100]:
        lines.append("\n### POD LOGS (last 200 lines) ###")
        lines.append(logs[-10000:])  # Last 10000 chars

    # Previous logs (crash info)
    prev_logs = data.get("pod_previous_logs", "")
    if prev_logs:
        lines.append("\n### PREVIOUS POD LOGS (crash recovery) ###")
        lines.append(prev_logs[-5000:])

    # Pod Events
    events = data.get("pod_events", "")
    if events:
        lines.append("\n### POD EVENTS ###")
        lines.append(events[-3000:])

    # Unhealthy resources
    unhealthy = data.get("unhealthy_resources", "")
    if unhealthy and "healthy" not in unhealthy.lower():
        lines.append("\n### UNHEALTHY RESOURCES ###")
        lines.append(unhealthy)

    # Recent errors
    errors = data.get("recent_errors", "")
    if errors:
        lines.append("\n### RECENT ERRORS (last 30 min) ###")
        lines.append(errors[-5000:])

    # Node status
    nodes = data.get("node_status", "")
    if nodes:
        lines.append("\n### NODE STATUS ###")
        lines.append(nodes[-3000:])

    # PVC status
    pvcs = data.get("pvc_status", "")
    if pvcs:
        lines.append("\n### PVC STATUS ###")
        lines.append(pvcs)

    # Service endpoints
    svc_endpoints = data.get("service_endpoints", "")
    if svc_endpoints:
        lines.append("\n### SERVICE ENDPOINTS ###")
        lines.append(svc_endpoints[-2000:])

    lines.append("\n" + "=" * 60)
    lines.append("END OF DIAGNOSIS DATA")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    # Test collection
    data = collect_all_data()
    print("Collected data keys:", list(data.keys()))
    print("\nFormatted for LLM:")
    print(format_for_llm(data)[:2000])