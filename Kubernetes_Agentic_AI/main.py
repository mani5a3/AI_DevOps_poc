# run_agent()
#    ↓
# get_pod_status()
#    ↓
# plan_action()  ← (RULES + LLM)
#    ↓
# execute()
#    ↓
# tools (real kubectl actions)
#    ↓
# repeat
# Observe → Plan → Decide → Execute → Repeat


from agent import run_agent

if __name__ == "__main__":
    run_agent()