# it keeps checking and fixing the Kubernetes pod until it becomes healthy.
# Iteration 1
#    ↓
# Check Phase
#    ↓
# If not Running:
#    ↓
# Get Status
#    ↓
# Send to Agent
#    ↓
# Agent decides fix
#    ↓
# Wait
#    ↓
# Iteration 2
# Why no apply_yaml here?
    # Your agent is expected to call:
        # FixImage
        # ApplyYAML

import time
from agent import create_agent
from tools import get_pod_phase, get_pod_status, apply_yaml

# ---------------------------
# Initialize Agent
# ---------------------------
agent = create_agent()

# ---------------------------
# Config
# ---------------------------
MAX_ITERATIONS = 10
SLEEP_SECONDS = 3

print("\n Starting AI DevOps Agent...\n")

for i in range(MAX_ITERATIONS):
    print(f"\n===== Iteration {i+1} =====")

    phase = get_pod_phase("").strip()
    print(f"Pod Phase: {phase}")

    if phase == "Running":
        print("SUCCESS: Pod is Running")
        break

    status = get_pod_status("")
    print("\n--- Pod Status ---\n")
    print(status)

    print("\n--- Agent Thinking ---\n")
    # Here You send pod status to agent Agent analyzes it
    # Agent decides:
    #     Fix image?
    #     Apply YAML?
    #     Check events?

    agent.invoke({"input": f"Pod issue:\n{status}"}) 

    # # Apply YAML only if pod is not Running
    # if phase != "Running":
    #     print("\n Applying desired state from YAML...")
    #     apply_output = apply_yaml("")
    #     print(apply_output)
    # else:
    #     print("\n Pod is already running, skipping YAML apply")

    print(f"\n Waiting {SLEEP_SECONDS}s...\n")
    time.sleep(SLEEP_SECONDS)