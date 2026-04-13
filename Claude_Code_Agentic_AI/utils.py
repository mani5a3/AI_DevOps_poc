import os
import sys
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from kubernetes import client, config
    from kubernetes.client import ApiClient
    from kubernetes.client.rest import ApiException
except ImportError:
    print("Error: kubernetes package not installed. Run: pip install kubernetes")
    sys.exit(1)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger("k8s-agent")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load agent configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        logging.warning(f"Config file {config_path} not found, using defaults")
        return get_default_config()

    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def get_default_config() -> Dict[str, Any]:
    """Return default configuration."""
    return {
        "kubernetes": {
            "namespace": "default",
            "check_interval_seconds": 30,
            "max_retries": 5,
            "retry_delay_seconds": 10,
            "timeout_seconds": 300
        },
        "agent": {
            "dry_run": False,
            "auto_fix_enabled": True,
            "log_level": "INFO"
        },
        "fix_strategies": {
            "image_pull_backoff": {"action": "update_image_tag", "fallback_image": "nginx:latest"},
            "crash_loop_backoff": {"action": "analyze_and_fix"},
            "oom_killed": {"action": "increase_memory", "memory_increase_factor": 2.0},
            "evicted": {"action": "clear_and_redeploy"},
            "pending": {"action": "adjust_scheduling"}
        },
        "deployment": {
            "deployment_dir": "./deployments",
            "backup_dir": "./backups"
        }
    }


def load_kube_config() -> None:
    """Load Kubernetes configuration."""
    try:
        # Try in-cluster config first
        config.load_incluster_config()
    except config.ConfigException:
        try:
            # Fall back to local kubeconfig
            config.load_kube_config()
        except config.ConfigException:
            logging.error("Could not load Kubernetes configuration")
            sys.exit(1)


def get_k8s_client() -> client.CoreV1Api:
    """Get Kubernetes CoreV1 API client."""
    load_kube_config()
    return client.CoreV1Api()


def get_apps_client() -> client.AppsV1Api:
    """Get Kubernetes AppsV1 API client."""
    load_kube_config()
    return client.AppsV1Api()


def get_pod_status(pod) -> str:
    """Get pod phase/status."""
    return pod.status.phase if pod.status else "Unknown"


def get_container_statuses(pod) -> List[Dict[str, Any]]:
    """Extract container statuses from pod."""
    statuses = []
    if pod.status and pod.status.container_statuses:
        for cs in pod.status.container_statuses:
            statuses.append({
                "name": cs.name,
                "ready": cs.ready,
                "restart_count": cs.restart_count,
                "last_state": cs.last_state,
                "state": cs.state,
                "image": cs.image,
                "image_id": cs.image_id
            })
    return statuses


def get_container_state(cs) -> str:
    """Get container state as string."""
    if cs is None:
        return "unknown"

    if hasattr(cs, 'running') and cs.running:
        return "running"
    elif hasattr(cs, 'waiting') and cs.waiting:
        return f"waiting: {cs.waiting.reason}"
    elif hasattr(cs, 'terminated') and cs.terminated:
        return f"terminated: {cs.terminated.reason}"
    return "unknown"


def parse_memory(mem_str: str) -> int:
    """Parse memory string to bytes."""
    if not mem_str:
        return 0

    mem_str = str(mem_str).strip()
    units = {
        'Ki': 1024,
        'Mi': 1024 ** 2,
        'Gi': 1024 ** 3,
        'Ti': 1024 ** 4,
        'K': 1000,
        'M': 1000 ** 2,
        'G': 1000 ** 3,
        'T': 1000 ** 4
    }

    for unit, multiplier in units.items():
        if mem_str.endswith(unit):
            return int(mem_str[:-len(unit)]) * multiplier

    return int(mem_str)


def format_memory(bytes_val: int) -> str:
    """Format bytes to human readable memory string."""
    for unit in ['Gi', 'Mi', 'Ki']:
        if bytes_val >= 1024:
            bytes_val //= 1024
        else:
            return f"{bytes_val}{unit}"
    return f"{bytes_val}Gi"


def load_deployment_yaml(file_path: str) -> Dict[str, Any]:
    """Load deployment YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def save_deployment_yaml(file_path: str, data: Dict[str, Any]) -> None:
    """Save deployment YAML file."""
    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def backup_file(file_path: str, backup_dir: str = "./backups") -> str:
    """Create backup of a file."""
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = Path(file_path).name
    backup_path = Path(backup_dir) / f"{filename}.{timestamp}.bak"

    with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
        dst.write(src.read())

    return str(backup_path)


def find_deployment_file(deployment_name: str, deployment_dir: str = "./deployments") -> Optional[str]:
    """Find deployment YAML file by name."""
    deployment_path = Path(deployment_dir)
    if not deployment_path.exists():
        return None

    for yaml_file in deployment_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                if data and data.get('metadata', {}).get('name') == deployment_name:
                    return str(yaml_file)
        except Exception:
            continue

    return None


def get_pod_events(core_v1: client.CoreV1Api, namespace: str, pod_name: str) -> List[Dict[str, Any]]:
    """Get events related to a pod."""
    try:
        events = core_v1.list_namespaced_event(
            namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )
        return [
            {
                "type": e.type,
                "reason": e.reason,
                "message": e.message,
                "count": e.count,
                "last_timestamp": e.last_timestamp
            }
            for e in events.items
        ]
    except ApiException:
        return []


def get_pod_logs(core_v1: client.CoreV1Api, namespace: str, pod_name: str,
                  container: str = None, tail_lines: int = 100) -> str:
    """Get pod logs."""
    try:
        return core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
    except ApiException as e:
        return f"Error getting logs: {e}"