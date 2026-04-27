"""
Agentic AI - Main Agent Loop

True Agentic AI for Kubernetes self-healing:
1. COLLECT → Get all logs, events, status
2. ANALYZE → LLM diagnoses the issue
3. FIX → Execute LLM-generated fix
4. VERIFY → Check if pod is healthy
5. REPEAT → Loop until success or max iterations
"""

import time
import json
from datetime import datetime

from config import (
    NAMESPACE, POD_NAME, MAX_ITERATIONS, SLEEP_SECONDS,
    LLM_MODEL, AUTO_FIX_ENABLED, VERBOSE, AUTO_UPDATE_DOCS
)
from collector import collect_all_data, format_for_llm
from analyzer import analyze_and_diagnose, generate_fix_with_llm
from fixer import execute_fix_command, apply_fix_from_diagnosis, retry_with_backoff
from tools import is_pod_healthy, get_pod_health_status


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(iteration: int, pod_status: dict):
    """Print current status."""
    phase = pod_status.get("status", {}).get("phase", "Unknown")
    containers = pod_status.get("status", {}).get("containerStatuses", [])

    ready = []
    not_ready = []
    for c in containers:
        name = c.get("name", "unknown")
        if c.get("ready", False):
            ready.append(name)
        else:
            state = c.get("state", {})
            reason = state.get("waiting", {}).get("reason", "NotReady")
            not_ready.append(f"{name}({reason})")

    print(f"\n--- Iteration {iteration} ---")
    print(f"Pod Phase: {phase}")
    print(f"Ready: {ready}")
    if not_ready:
        print(f"Not Ready: {not_ready}")


def run_agent():
    """Main agent loop - Collect → Analyze → Fix → Verify → Repeat."""

    print_header("KUBERNETES AGENTIC AI")
    print(f"Namespace: {NAMESPACE}")
    print(f"Pod: {POD_NAME}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"LLM Model: {LLM_MODEL}")
    print(f"Auto Fix: {AUTO_FIX_ENABLED}")

    # Track attempts
    attempts = []
    success = False
    start_time = datetime.now()

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"{'='*60}")

        iteration_start = datetime.now()

        # Step 1: COLLECT - Get all data
        print("\n[1/4] COLLECTING DATA...")
        try:
            data = collect_all_data()
            context = format_for_llm(data)
            if VERBOSE:
                print(f"Collected {len(data)} data sources")
        except Exception as e:
            print(f"ERROR collecting data: {e}")
            continue

        # Get current pod status for display
        pod_status = data.get("pod_status", {})
        print_status(iteration, pod_status)

        # Step 2: ANALYZE - LLM diagnosis
        print("\n[2/4] ANALYZING WITH LLM...")
        try:
            diagnosis = analyze_and_diagnose(model=LLM_MODEL)

            print(f"\n  Issue Type: {diagnosis.issue_type}")
            print(f"  Root Cause: {diagnosis.root_cause[:200]}...")
            print(f"  Suggested Fix: {diagnosis.fix_command[:100] if diagnosis.fix_command else 'None'}")
            print(f"  Confidence: {diagnosis.confidence:.2f}")

            if diagnosis.issue_type == "error":
                print("  ERROR: LLM analysis failed, continuing...")
                time.sleep(SLEEP_SECONDS)
                continue

        except Exception as e:
            print(f"ERROR in analysis: {e}")
            time.sleep(SLEEP_SECONDS)
            continue

        # Step 3: FIX - Execute the fix
        if AUTO_FIX_ENABLED and diagnosis.fix_command:
            print("\n[3/4] EXECUTING FIX...")

            fix_result = None

            # Try the suggested fix
            result = execute_fix_command(diagnosis.fix_command)

            if result["success"]:
                print(f"  ✓ Fix applied: {diagnosis.fix_command}")
                fix_result = result
            else:
                print(f"  ✗ Fix failed: {result.get('error', 'Unknown error')}")

                # Try alternative fix
                if diagnosis.root_cause:
                    print("  Trying alternative fix...")
                    alt_cmd = generate_fix_with_llm(
                        format_for_llm(data),
                        diagnosis.fix_command,
                        LLM_MODEL
                    )

                    if alt_cmd and alt_cmd.startswith("kubectl"):
                        result = execute_fix_command(alt_cmd)
                        if result["success"]:
                            print(f"  ✓ Alternative fix: {alt_cmd}")
                            fix_result = result

            # Record attempt
            attempts.append({
                "iteration": iteration,
                "issue_type": diagnosis.issue_type,
                "fix_command": diagnosis.fix_command,
                "success": fix_result is not None,
                "timestamp": datetime.now().isoformat()
            })

        else:
            print("\n[3/4] SKIPPING FIX (dry-run or no fix)")

        # Step 4: VERIFY - Check if pod is healthy
        print("\n[4/4] VERIFYING HEALTH...")

        # Wait a bit for changes to take effect
        time.sleep(SLEEP_SECONDS)

        # Check health
        healthy = is_pod_healthy(POD_NAME)

        if healthy:
            success = True
            print("\n" + "=" * 60)
            print("  ✓✓✓ SUCCESS: POD IS HEALTHY! ✓✓✓")
            print("=" * 60)
            break
        else:
            health_status = get_pod_health_status(POD_NAME)
            print(f"  Pod Status: {health_status}")
            print(f"  Not healthy yet, will retry...")

        # Calculate iteration time
        iteration_time = (datetime.now() - iteration_start).total_seconds()
        print(f"\n  Iteration took: {iteration_time:.1f}s")

        # Calculate backoff for next iteration
        backoff = retry_with_backoff(iteration, MAX_ITERATIONS)
        if backoff > 0:
            print(f"  Waiting {backoff}s before retry...")
            time.sleep(backoff)

    # Summary
    print_header("AGENT RUN SUMMARY")
    print(f"Pod: {POD_NAME}")
    print(f"Namespace: {NAMESPACE}")
    print(f"Success: {success}")
    print(f"Total Iterations: {iteration}")
    print(f"Total Time: {(datetime.now() - start_time).total_seconds():.1f}s")
    print(f"Fix Attempts: {len(attempts)}")

    if attempts:
        print("\nFix History:")
        for i, attempt in enumerate(attempts, 1):
            status = "✓" if attempt["success"] else "✗"
            print(f"  {i}. {status} {attempt['issue_type']}: {attempt['fix_command'][:60]}...")

    # Auto-update documentation
    if AUTO_UPDATE_DOCS and success:
        print("\n" + "=" * 60)
        print("  AUTO-UPDATING DOCUMENTATION")
        print("=" * 60)
        try:
            from doc_generator import generate_all_docs
            generate_all_docs()
            print("  ✓ Documentation updated!")
        except Exception as e:
            print(f"  ✗ Documentation update failed: {e}")

    return success


def run_once():
    """Run diagnosis once without fixing."""
    print_header("KUBERNETES AGENTIC AI - DIAGNOSIS ONLY")

    print("\n[1/2] COLLECTING DATA...")
    data = collect_all_data()
    context = format_for_llm(data)

    print("\n[2/2] ANALYZING WITH LLM...")
    diagnosis = analyze_and_diagnose(model=LLM_MODEL)

    print(f"\n{'='*60}")
    print("DIAGNOSIS RESULT")
    print("=" * 60)
    print(f"Issue Type: {diagnosis.issue_type}")
    print(f"Root Cause: {diagnosis.root_cause}")
    print(f"Fix Command: {diagnosis.fix_command}")
    print(f"Fix YAML: {diagnosis.fix_yaml or 'None'}")
    print(f"Confidence: {diagnosis.confidence:.2f}")

    return diagnosis


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        run_once()
    else:
        run_agent()