from tools import tools

def execute(plan, pod_name):
    action = plan.get("action")

    if action == "FixImage":
        image = plan.get("image")
        if not image:
            return "ERROR: No image provided"
        return tools["FixImage"](pod_name, image)

    elif action == "GetEvents":
        return tools["GetEvents"](pod_name)

    elif action == "ApplyYAML":
        return tools["ApplyYAML"](pod_name)

    else:
        return "NO_ACTION"