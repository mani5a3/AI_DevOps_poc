"""
Analyzer Module - LLM-driven Diagnosis and Fix Generation

Analyzes collected Kubernetes data using LLM to:
1. Determine root cause of issues
2. Generate specific fix commands
3. Return structured diagnosis + fix
"""

import json
import re
from typing import Dict, Any, Optional, List
from ollama import chat

from prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    FIX_GENERATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT
)
from collector import collect_all_data, format_for_llm


class DiagnosisResult:
    """Result of LLM diagnosis."""

    def __init__(self, issue_type: str, root_cause: str, fix_command: str,
                 fix_yaml: str, confidence: float, raw_response: str):
        self.issue_type = issue_type
        self.root_cause = root_cause
        self.fix_command = fix_command
        self.fix_yaml = fix_yaml
        self.confidence = confidence
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "root_cause": self.root_cause,
            "fix_command": self.fix_command,
            "fix_yaml": self.fix_yaml,
            "confidence": self.confidence,
        }

    def __repr__(self):
        return (f"DiagnosisResult(type={self.issue_type}, "
                f"confidence={self.confidence}, fix={self.fix_command[:50]}...)")


def analyze_with_llm(context_data: str, model: str = "gemma3:4b") -> DiagnosisResult:
    """
    Send all collected data to LLM for diagnosis.

    Args:
        context_data: Formatted Kubernetes data
        model: LLM model to use

    Returns:
        DiagnosisResult with issue type, root cause, and fix
    """
    # Build the diagnosis prompt
    user_prompt = f"""
Analyze the following Kubernetes diagnostic data and determine:

1. **Issue Type**: What is the exact problem? (e.g., ImagePullBackOff, CrashLoopBackOff, OOMKilled, Pending, Evicted, etc.)

2. **Root Cause**: What is the underlying cause? Be specific.

3. **Fix Command**: Provide a specific kubectl command to fix this issue. Be exact and actionable.

4. **Fix YAML** (optional): If YAML modification is needed, provide the complete YAML patch.

5. **Confidence**: Rate your confidence 0.0-1.0

Return ONLY valid JSON in this exact format:

{{
    "issue_type": "ImagePullBackOff",
    "root_cause": "The image 'redis:invalid-tag' does not exist in the registry",
    "fix_command": "kubectl set image deployment/myapp myapp=redis:latest",
    "fix_yaml": "",
    "confidence": 0.95
}}

--- DIAGNOSTIC DATA ---
{context_data}

"""

    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": 0.1,
                "num_predict": 2000
            }
        )

        content = response.get("message", {}).get("content", "")
        return parse_diagnosis_response(content)

    except Exception as e:
        return DiagnosisResult(
            issue_type="error",
            root_cause=f"LLM call failed: {str(e)}",
            fix_command="",
            fix_yaml="",
            confidence=0.0,
            raw_response=str(e)
        )


def parse_diagnosis_response(response: str) -> DiagnosisResult:
    """Parse LLM JSON response into DiagnosisResult."""
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())

            return DiagnosisResult(
                issue_type=data.get("issue_type", "unknown"),
                root_cause=data.get("root_cause", "Unable to determine"),
                fix_command=data.get("fix_command", ""),
                fix_yaml=data.get("fix_yaml", ""),
                confidence=float(data.get("confidence", 0.5)),
                raw_response=response
            )
    except (json.JSONDecodeError, AttributeError) as e:
        pass

    # Fallback: try to extract what we can
    issue_type = "unknown"
    root_cause = response[:500]
    fix_command = ""

    # Try to find fix command in response
    cmd_match = re.search(r'kubectl [^\n]+', response)
    if cmd_match:
        fix_command = cmd_match.group()

    return DiagnosisResult(
        issue_type=issue_type,
        root_cause=root_cause,
        fix_command=fix_command,
        fix_yaml="",
        confidence=0.3,
        raw_response=response
    )


def generate_fix_with_llm(current_state: str, failed_fix: str = "",
                           model: str = "gemma3:4b") -> str:
    """
    Generate alternative fix when previous fix failed.

    Args:
        current_state: Current pod state
        failed_fix: What was attempted before
        model: LLM model

    Returns:
        New kubectl command to try
    """
    user_prompt = f"""
The previous fix failed. Current pod state:

{current_state}

Previous attempted fix:
{failed_fix}

Generate an ALTERNATIVE fix approach. Think about what else could be wrong:

- Different image tag?
- Missing environment variable?
- Resource limits too low?
- Volume mount issues?
- Security context problems?
- Node selector/tolerations?

Return ONLY a new kubectl command that might work:

{{
    "fix_command": "kubectl exec ...",
    "reasoning": "Why this approach might work"
}}

"""

    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": FIX_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": 0.3,
                "num_predict": 500
            }
        )

        content = response.get("message", {}).get("content", "")

        # Extract command from response
        cmd_match = re.search(r'kubectl [^\n]+', content)
        if cmd_match:
            return cmd_match.group()

        return ""

    except Exception as e:
        return f"ERROR: {str(e)}"


def verify_fix_with_llm(pod_status: str, expected_state: str = "Running",
                        model: str = "gemma3:4b") -> bool:
    """
    Verify if pod is actually fixed using LLM.

    Args:
        pod_status: Current pod status JSON
        expected_state: What we expect (usually "Running")

    Returns:
        True if pod is healthy
    """
    user_prompt = f"""
Analyze this pod status and determine if it's healthy:

{pod_status}

Expected state: {expected_state}

Is the pod healthy? Return ONLY valid JSON:

{{
    "healthy": true,
    "reason": "Container is running and ready"
}}

OR

{{
    "healthy": false,
    "reason": "Container is in Waiting state with ImagePullBackOff"
}}

"""

    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": 0.1,
                "num_predict": 200
            }
        )

        content = response.get("message", {}).get("content", "")

        # Try to parse JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("healthy", False)

    except Exception as e:
        pass

    # Fallback to simple check
    return "Running" in pod_status and "ready" in pod_status.lower()


def analyze_and_diagnose(model: str = "gemma3:4b") -> DiagnosisResult:
    """
    Main entry point: Collect data and analyze.

    Args:
        model: LLM model to use

    Returns:
        DiagnosisResult with diagnosis and fix
    """
    # Collect all data
    data = collect_all_data()

    # Format for LLM
    context = format_for_llm(data)

    # Analyze
    return analyze_with_llm(context, model)


if __name__ == "__main__":
    # Test analysis
    print("Starting diagnosis...")
    result = analyze_and_diagnose()
    print(f"\nDiagnosis: {result.issue_type}")
    print(f"Root Cause: {result.root_cause}")
    print(f"Fix Command: {result.fix_command}")
    print(f"Confidence: {result.confidence}")