import subprocess
import yaml
import json
from config import YAML_FILE_PATH, NAMESPACE, LABEL_SELECTOR

# ---------------------------
# Helper: Run shell command
# ---------------------------
def run_cmd(cmd: str) -> str:
    return subprocess.getoutput(cmd)


# ---------------------------
# Get Pod Status (JSON based)
# ---------------------------
def get_pod_status(_: str) -> dict:
    cmd = f"kubectl get pods -l {LABEL_SELECTOR} -n {NAMESPACE} -o json"
    output = run_cmd(cmd)

    try:
        return json.loads(output)
    except:
        return {}


# ---------------------------
# Check if Pod is Healthy 
# ---------------------------
def is_pod_healthy(pod_json: dict) -> bool:
    try:
        items = pod_json.get("items", [])
        if not items:
            return False

        pod = items[0]
        phase = pod.get("status", {}).get("phase")

        container_status = pod.get("status", {}).get("containerStatuses", [])[0]

        return (
            phase == "Running" and
            container_status.get("ready") == True and
            container_status.get("state", {}).get("waiting") is None
        )
    except:
        return False


# ---------------------------
# Fix Image (Dynamic)
# ---------------------------
def fix_image(pod_name: str, new_image: str) -> str:
    if not YAML_FILE_PATH:
        return "ERROR: YAML_FILE_PATH not set"

    # Load YAML
    with open(YAML_FILE_PATH, "r") as f:
        data = yaml.safe_load(f)

    try:
        current_image = data["spec"]["containers"][0]["image"]
    except:
        return "ERROR: Unable to read image from YAML"

    # Update image
    data["spec"]["containers"][0]["image"] = new_image

    # Save YAML
    with open(YAML_FILE_PATH, "w") as f:
        yaml.dump(data, f)

    # Delete old pod
    delete_output = run_cmd(
        f"kubectl delete pod {pod_name} -n {NAMESPACE} --ignore-not-found"
    )

    # Apply updated YAML
    apply_output = run_cmd(
        f"kubectl apply -f {YAML_FILE_PATH} -n {NAMESPACE}"
    )

    return f"""
IMAGE UPDATED: {current_image} → {new_image}

DELETE OUTPUT:
{delete_output}

APPLY OUTPUT:
{apply_output}
"""


# ---------------------------
# Apply YAML
# ---------------------------
def apply_yaml(_: str) -> str:
    if not YAML_FILE_PATH:
        return "ERROR: YAML_FILE_PATH not set"

    return run_cmd(
        f"kubectl apply -f {YAML_FILE_PATH} -n {NAMESPACE}"
    )


# ---------------------------
# Get Events (Debugging)
# ---------------------------
def get_events(pod_name: str) -> str:
    if not pod_name:
        return "ERROR: Pod name required"

    cmd = (
        f"kubectl get events -n {NAMESPACE} "
        f"--field-selector involvedObject.name={pod_name} "
        f"--sort-by=.metadata.creationTimestamp"
    )

    return run_cmd(cmd)


# ---------------------------
# Tool Registry (IMPORTANT)
# ---------------------------
tools = {
    "FixImage": fix_image,
    "ApplyYAML": apply_yaml,
    "GetEvents": get_events
}