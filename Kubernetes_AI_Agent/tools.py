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
from langchain.tools import Tool
from config import YAML_FILE_PATH, IMAGE_MAP, LABEL_SELECTOR
from config import LABEL_SELECTOR

# ---------------------------
# Get pod phase
# ---------------------------
def get_pod_phase(_: str) -> str:
    cmd = f"kubectl get pods -l {LABEL_SELECTOR} -o json"
    output = subprocess.getoutput(cmd)

    data = json.loads(output)
    if not data["items"]:
        return "NotFound"

    return data["items"][0]["status"]["phase"]


# ---------------------------
# Get pod status
# ---------------------------
def get_pod_status(_: str) -> str:
    return subprocess.getoutput(f"kubectl describe pod -l {LABEL_SELECTOR}")


# ---------------------------
# Fix image
# ---------------------------
def fix_image(_: str) -> str:
    with open(YAML_FILE_PATH, "r") as f:
        data = yaml.safe_load(f)

    container = data['spec']['containers'][0]
    current_image = container['image']

    app_name = current_image.split(":")[0]
    correct_image = IMAGE_MAP.get(app_name)

    if not correct_image:
        return "NO_ACTION"

    if current_image == correct_image:
        return "NO_ACTION"

    container['image'] = correct_image

    with open(YAML_FILE_PATH, "w") as f:
        yaml.dump(data, f)

    return "IMAGE_FIXED"


# ---------------------------
# Apply YAML
# ---------------------------
def apply_yaml(_: str) -> str:
    delete_cmd = f"kubectl delete pod -l {LABEL_SELECTOR} --ignore-not-found"
    apply_cmd = f"kubectl apply -f {YAML_FILE_PATH}"

    delete_output = subprocess.getoutput(delete_cmd)
    apply_output = subprocess.getoutput(apply_cmd)

    return f"{delete_output}\n{apply_output}"


# ---------------------------
# Get events
# ---------------------------
def get_events(_: str) -> str:
    return subprocess.getoutput(
        f"kubectl get events -l {LABEL_SELECTOR} --sort-by=.metadata.creationTimestamp"
    )


# ---------------------------
# Tools list
# ---------------------------
tools = [
    Tool(name="GetPodPhase", func=get_pod_phase, description="Get pod phase"),
    Tool(name="GetPodStatus", func=get_pod_status, description="Describe pod"),
    Tool(name="FixImage", func=fix_image, description="Fix wrong image"),
    Tool(name="ApplyYAML", func=apply_yaml, description="Apply Kubernetes YAML from file. DO NOT provide YAML input."),
    Tool(name="GetEvents", func=get_events, description="Get events")
]