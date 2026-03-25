AI Agent:
    Uses LLM every iteration
Agentic AI:
    Uses LLM only when needed

Agentic AI DevOps – Kubernetes Self-Healing

An Agentic AI system that detects and fixes Kubernetes pod failures automatically using rule-based + LLM-driven decision making.

Overview:
    This project implements a self-healing loop:
        Detect pod issues
        Decide fix (rules → LLM fallback)
        Execute fix
        Repeat until healthy

Workflow:
        main.py
        ↓
        agent.py
        ↓
        planner.py (Rule → LLM)
        ↓
        executor.py
        ↓
        tools.py (kubectl actions)
        ↓
        Repeat until Pod = Running

planner.py:
    Handles decision-making using a hybrid approach
    Fast and deterministic
    Handles known Kubernetes issues
    Avoids unnecessary LLM calls

Rule-Based Logic (Primary):

    if "ImagePullBackOff" in status or "ErrImagePull" in status:
        return {
            "action": "FixImage",
            "image": "redis:latest"
        }
 
 LLM-Based Logic (Fallback):
    Used when no rule matches

Decision Strategy:
    1. Try rule-based decision
    2. If no match → use LLM
    3. Return action to executor