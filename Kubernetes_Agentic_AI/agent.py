from planner import plan_action
from executor import execute
from tools import get_pod_status
from config import MAX_ITERATIONS, SLEEP_SECONDS, POD_NAME
from tools import is_pod_healthy
import time
import json

def run_agent():

    print("\n Starting Agentic AI DevOps Agent...\n")

    for i in range(MAX_ITERATIONS):

        print(f"\n===== Iteration {i+1} =====")

        pod_json = get_pod_status("")

        print("\nPod JSON:\n", json.dumps(pod_json, indent=2))

        #  Correct success condition
        if is_pod_healthy(pod_json):
            print("\n SUCCESS: Pod is truly healthy")
            break

        print("\n Planning...")
        plan = plan_action(json.dumps(pod_json))
        print("Plan:", plan)

        print("\n Executing...")
        result = execute(plan, POD_NAME)
        print("Result:", result)

        print(f"\n Waiting {SLEEP_SECONDS}s...\n")
        time.sleep(SLEEP_SECONDS)