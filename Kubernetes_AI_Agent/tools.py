# | Tool         | Purpose                   |
# | ------------ | ------------------------- |
# | GetPodPhase  | Check if pod is Running   |
# | GetPodStatus | Get detailed pod info     |
# | FixImage     | Fix wrong container image |
# | ApplyYAML    | Apply changes to cluster  |
# | GetEvents    | Debug issues              |

import subprocess
import yaml
import json
import os
from langchain.tools import Tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------
# Config (from .env)
# ---------------------------
YAML_FILE_PATH = os.getenv("YAML_FILE_PATH")
NAMESPACE = os.getenv("NAMESPACE", "default")
LABEL_SELECTOR = os.getenv("LABEL_SELECTOR")
POD_NAME = os.getenv("POD_NAME")

# ---------------------------
# Helpers
# ---------------------------
def run_cmd(cmd: str) -> str:
    """Execute shell command safely"""
    return subprocess.getoutput(cmd)


# ---------------------------
# Get Pod Phase
# ---------------------------
def get_pod_phase(_: str) -> str:
    cmd = f"kubectl get pods -l {LABEL_SELECTOR} -n {NAMESPACE} -o json"
    output = run_cmd(cmd)

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return "Error: Invalid kubectl output"

    if not data.get("items"):
        return "NotFound"

    return data["items"][0].get("status", {}).get("phase", "Unknown")


# ---------------------------
# Get Pod Status
# ---------------------------
def get_pod_status(_: str) -> str:
    cmd = f"kubectl describe pod -l {LABEL_SELECTOR} -n {NAMESPACE}"
    return run_cmd(cmd)


# ---------------------------
# Fix Image (Dynamic)
# ---------------------------
def get_correct_image(current_image: str) -> str:
    """
    Dynamic image fix:
    Always convert to :latest tag
    """
    base = current_image.split(":")[0]
    return f"{base}:latest"


def fix_image(_: str) -> str:
    if not YAML_FILE_PATH:
        return "ERROR: YAML_FILE_PATH not set"

    with open(YAML_FILE_PATH, "r") as f:
        data = yaml.safe_load(f)

    container = data.get("spec", {}).get("containers", [])[0]

    current_image = container.get("image")

    if not current_image:
        return "ERROR: No image found in YAML"

    correct_image = get_correct_image(current_image)

    if current_image == correct_image:
        return "NO_ACTION"

    container["image"] = correct_image

    with open(YAML_FILE_PATH, "w") as f:
        yaml.dump(data, f)

    return f"IMAGE_FIXED: {current_image} → {correct_image}"


# ---------------------------
# Apply YAML
# ---------------------------
def apply_yaml(_: str) -> str:
    if not YAML_FILE_PATH:
        return "ERROR: YAML_FILE_PATH not set"

    delete_cmd = f"kubectl delete pod -l {LABEL_SELECTOR} -n {NAMESPACE} --ignore-not-found"
    apply_cmd = f"kubectl apply -f {YAML_FILE_PATH} -n {NAMESPACE}"

    delete_output = run_cmd(delete_cmd)
    apply_output = run_cmd(apply_cmd)

    return f"{delete_output}\n{apply_output}"


# ---------------------------
# Get Events
# ---------------------------
def get_events(POD_NAME: str) -> str:
    if not POD_NAME:
        return "ERROR: Pod name required"

    cmd = (
        f"kubectl get events -n {NAMESPACE} "
        f"--field-selector involvedObject.name={POD_NAME} "
        f"--sort-by=.metadata.creationTimestamp"
    )

    return run_cmd(cmd)


# ---------------------------
# Tools List
# ---------------------------
tools = [
    Tool(
        name="GetPodPhase",
        func=get_pod_phase,
        description="Get the current phase of the pod (Running, Pending, Failed, NotFound)"
    ),
    Tool(
        name="GetPodStatus",
        func=get_pod_status,
        description="Get detailed description of the pod"
    ),
    Tool(
        name="FixImage",
        func=fix_image,
        description="Fix incorrect container image in YAML dynamically"
    ),
    Tool(
        name="ApplyYAML",
        func=apply_yaml,
        description="Apply Kubernetes YAML file to cluster (no input required)"
    ),
    Tool(
        name="GetEvents",
        func=get_events,
        description="Get Kubernetes events for a specific pod name"
    )
]