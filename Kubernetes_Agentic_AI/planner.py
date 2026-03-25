from ollama import chat
import json
import re

# ---------------------------
# Rule-based decision
# ---------------------------
def rule_based_decision(status: str):

    if "ErrImagePull" in status or "ImagePullBackOff" in status:

        import re
        match = re.search(r'"image":\s*"([^"]+)"', status)

        if match:
            failed_image = match.group(1)

            base = failed_image.split(":")[0]
            fixed_image = base + ":latest"

            return {
                "action": "FixImage",
                "image": fixed_image
            }

    if "items\": []" in status:
        return {"action": "ApplyYAML"}

    return None


# ---------------------------
# LLM decision
# ---------------------------
def llm_decision(status: str):

    prompt = f"""
You are an expert Kubernetes DevOps AI agent.

Analyze the following pod status/events:

{status}

Return ONLY valid JSON.

Examples:

{{
  "action": "FixImage",
  "image": "<correct-image>"
}}

{{
  "action": "GetEvents"
}}

{{
  "action": "ApplyYAML"
}}

{{
  "action": "DoNothing"
}}
"""

    response = chat(
        model="gemma3:4b",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response['message']['content'].strip()

    try:
        return json.loads(text)
    except:
        return {"action": "GetEvents"}


# ---------------------------
# Main planner
# ---------------------------
def plan_action(status: str):

    rule_plan = rule_based_decision(status)

    if rule_plan:
        print("Rule-based decision used")
        return rule_plan

    print("Using LLM decision")
    return llm_decision(status)