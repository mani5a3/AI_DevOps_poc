#!/usr/bin/env python3
"""
Kubernetes Agentic AI

An autonomous agent that monitors Kubernetes pods for common issues and automatically
detects, diagnoses, and fixes problems like ImagePullBackOff, CrashLoopBackOff, OOMKilled,
and other pod failure states.

Usage:
    python kubernetes_agent.py [--config CONFIG] [--dry-run] [--namespace NAMESPACE]
"""

import os
import sys
import time
import argparse
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml
from kubernetes import client
from kubernetes.client import ApiClient
from kubernetes.client.rest import ApiException

from utils import (
    setup_logging,
    load_config,
    get_default_config,
    get_k8s_client,
    get_apps_client,
    get_pod_status,
    get_container_statuses,
    get_container_state,
    parse_memory,
    format_memory,
    load_deployment_yaml,
    save_deployment_yaml,
    backup_file,
    find_deployment_file,
    get_pod_events,
    get_pod_logs
)


class PodIssue:
    """Represents a detected pod issue."""

    def __init__(self, pod_name: str, namespace: str, issue_type: str,
                 reason: str, message: str, container: str = None):
        self.pod_name = pod_name
        self.namespace = namespace
        self.issue_type = issue_type
        self.reason = reason
        self.message = message
        self.container = container
        self.fixed = False
        self.fix_attempts = 0

    def __repr__(self):
        return f"PodIssue({self.pod_name}, {self.issue_type}, {self.reason})"


class KubernetesAgent:
    """Agent that monitors and fixes Kubernetes pod issues."""

    def __init__(self, config_path: str = "config.yaml", dry_run: bool = False):
        self.logger = setup_logging()
        self.config = load_config(config_path)
        self.dry_run = dry_run or self.config.get('agent', {}).get('dry_run', False)
        self.auto_fix = self.config.get('agent', {}).get('auto_fix_enabled', True)

        if self.dry_run:
            self.logger.info("Running in DRY-RUN mode - no fixes will be applied")

        self.core_v1 = get_k8s_client()
        self.apps_v1 = get_apps_client()
        self.api_client = ApiClient()

        self.namespace = self.config.get('kubernetes', {}).get('namespace', 'default')
        self.check_interval = self.config.get('kubernetes', {}).get('check_interval_seconds', 30)
        self.max_retries = self.config.get('kubernetes', {}).get('max_retries', 5)
        self.timeout = self.config.get('kubernetes', {}).get('timeout_seconds', 300)

        self.fixed_issues = []
        self.failed_fixes = []

    def detect_issues(self, namespace: str = None) -> List[PodIssue]:
        """Detect all pod issues in the namespace."""
        namespace = namespace or self.namespace
        issues = []

        try:
            pods = self.core_v1.list_namespaced_pod(namespace).items
        except ApiException as e:
            self.logger.error(f"Error listing pods: {e}")
            return issues

        for pod in pods:
            pod_issues = self._detect_pod_issues(pod, namespace)
            issues.extend(pod_issues)

        return issues

    def _detect_pod_issues(self, pod, namespace: str) -> List[PodIssue]:
        """Detect issues for a specific pod."""
        issues = []
        pod_name = pod.metadata.name
        status = get_pod_status(pod)

        self.logger.debug(f"Checking pod {pod_name}, status: {status}")

        # Check for different issue types
        if status == "Pending":
            issue = self._check_pending(pod, namespace)
            if issue:
                issues.append(issue)

        elif status == "Failed":
            issue = self._check_failed(pod, namespace)
            if issue:
                issues.append(issue)

        elif status == "Running":
            # Check for OOMKilled and other container issues
            container_issues = self._check_running_pod_containers(pod, namespace)
            issues.extend(container_issues)

        elif status == "Unknown":
            issues.append(PodIssue(
                pod_name, namespace, "Unknown",
                "Unknown status", "Pod status could not be determined"
            ))

        return issues

    def _check_pending(self, pod, namespace: str) -> Optional[PodIssue]:
        """Check for pending pod issues."""
        pod_name = pod.metadata.name

        # Check conditions
        if pod.status and pod.status.conditions:
            for condition in pod.status.conditions:
                if not condition.status and condition.reason:
                    return PodIssue(
                        pod_name, namespace, "Pending",
                        condition.reason,
                        condition.message or "Pod is pending",
                        condition.reason
                    )

        # Check events for scheduling issues
        events = get_pod_events(self.core_v1, namespace, pod_name)
        for event in events:
            if event.get('reason') in ['FailedScheduling', 'Unschedulable']:
                return PodIssue(
                    pod_name, namespace, "Pending",
                    event.get('reason'),
                    event.get('message', 'Pod could not be scheduled')
                )

        return None

    def _check_failed(self, pod, namespace: str) -> Optional[PodIssue]:
        """Check for failed pod issues."""
        pod_name = pod.metadata.name
        container_statuses = get_container_statuses(pod)

        for cs in container_statuses:
            state = cs.get('state', {})
            waiting = state.get('waiting') if isinstance(state, dict) else None

            if waiting:
                reason = waiting.get('reason', 'Unknown')
                message = waiting.get('message', '')

                if reason == 'ImagePullBackOff':
                    return PodIssue(
                        pod_name, namespace, "ImagePullBackOff",
                        reason, message, cs.get('name')
                    )
                elif reason == 'CrashLoopBackOff':
                    return PodIssue(
                        pod_name, namespace, "CrashLoopBackOff",
                        reason, message, cs.get('name')
                    )
                elif reason == 'ErrImagePull':
                    return PodIssue(
                        pod_name, namespace, "ImagePullBackOff",
                        reason, message, cs.get('name')
                    )

        return PodIssue(
            pod_name, namespace, "Failed",
            "PodFailed", "Pod has failed"
        )

    def _check_running_pod_containers(self, pod, namespace: str) -> List[PodIssue]:
        """Check containers in running pods for issues like OOMKilled."""
        issues = []
        pod_name = pod.metadata.name
        container_statuses = get_container_statuses(pod)

        for cs in container_statuses:
            restart_count = cs.get('restart_count', 0)
            state = cs.get('state', {})

            if isinstance(state, dict):
                terminated = state.get('terminated')
                if terminated:
                    exit_code = terminated.get('exit_code', 0)

                    # Check for OOMKilled (exit code 137 = SIGKILL, often OOM)
                    if exit_code == 137 or 'OOMKilled' in terminated.get('reason', ''):
                        issues.append(PodIssue(
                            pod_name, namespace, "OOMKilled",
                            "OOMKilled", terminated.get('message', 'Container killed due to OOM'),
                            cs.get('name')
                        ))

                    # Check for frequent restarts
                    elif restart_count > 0 and exit_code != 0:
                        issues.append(PodIssue(
                            pod_name, namespace, "CrashLoopBackOff",
                            f"ExitCode{exit_code}",
                            terminated.get('message', f'Container exited with code {exit_code}'),
                            cs.get('name')
                        ))

            # Check for waiting state in supposedly running pod
            waiting = state.get('waiting') if isinstance(state, dict) else None
            if waiting:
                reason = waiting.get('reason', '')
                if reason in ['ImagePullBackOff', 'CrashLoopBackOff']:
                    issues.append(PodIssue(
                        pod_name, namespace, reason,
                        reason, waiting.get('message', ''),
                        cs.get('name')
                    ))

        return issues

    def diagnose_issue(self, issue: PodIssue) -> str:
        """Diagnose the root cause of an issue."""
        self.logger.info(f"Diagnosing issue: {issue.issue_type} for pod {issue.pod_name}")

        # Get pod events
        events = get_pod_events(self.core_v1, issue.namespace, issue.pod_name)

        # Get pod logs if container specified
        logs = ""
        if issue.container:
            logs = get_pod_logs(self.core_v1, issue.namespace, issue.pod_name, issue.container)

        # Build diagnosis
        diagnosis = f"Issue: {issue.issue_type}\n"
        diagnosis += f"Reason: {issue.reason}\n"
        diagnosis += f"Message: {issue.message}\n"

        if events:
            diagnosis += f"Events: {len(events)} related events found\n"
            for event in events[-3:]:
                diagnosis += f"  - {event.get('reason')}: {event.get('message')}\n"

        if logs:
            diagnosis += f"Recent logs:\n{logs[-500:]}\n"

        return diagnosis

    def fix_issue(self, issue: PodIssue) -> bool:
        """Fix a detected issue."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would fix {issue.issue_type} for {issue.pod_name}")
            return True

        if not self.auto_fix:
            self.logger.warning(f"Auto-fix disabled, skipping {issue.pod_name}")
            return False

        self.logger.info(f"Attempting to fix {issue.issue_type} for pod {issue.pod_name}")

        fix_strategies = self.config.get('fix_strategies', {})

        if issue.issue_type == "ImagePullBackOff":
            return self._fix_image_pull_backoff(issue, fix_strategies)
        elif issue.issue_type == "CrashLoopBackOff":
            return self._fix_crashloopbackoff(issue, fix_strategies)
        elif issue.issue_type == "OOMKilled":
            return self._fix_oomkilled(issue, fix_strategies)
        elif issue.issue_type == "Pending":
            return self._fix_pending(issue, fix_strategies)
        elif issue.issue_type == "Evicted":
            return self._fix_evicted(issue, fix_strategies)
        else:
            self.logger.warning(f"No fix strategy for issue type: {issue.issue_type}")
            return False

    def _fix_image_pull_backoff(self, issue: PodIssue, strategies: Dict) -> bool:
        """Fix ImagePullBackOff issue."""
        self.logger.info(f"Fixing ImagePullBackOff for {issue.pod_name}")

        strategy = strategies.get('image_pull_backoff', {})
        fallback_image = strategy.get('fallback_image', 'nginx:latest')

        # Find deployment
        deployment_name = issue.pod_name
        if '-' in deployment_name:
            # Try to find parent deployment
            deployment_name = deployment_name.rsplit('-', 1)[0]

        # Look for deployment file
        deployment_dir = self.config.get('deployment', {}).get('deployment_dir', './deployments')
        deploy_file = find_deployment_file(deployment_name, deployment_dir)

        if deploy_file:
            self.logger.info(f"Found deployment file: {deploy_file}")
            backup_file(deploy_file, self.config.get('deployment', {}).get('backup_dir', './backups'))

            data = load_deployment_yaml(deploy_file)
            spec = data.get('spec', {})
            template = spec.get('template', {})
            containers = template.get('spec', {}).get('containers', [])

            for container in containers:
                if issue.container and container.get('name') != issue.container:
                    continue

                current_image = container.get('image', '')
                self.logger.info(f"Current image: {current_image}")

                # Try to fix image
                new_image = self._resolve_image(current_image, fallback_image)
                container['image'] = new_image
                self.logger.info(f"Updated image to: {new_image}")

            save_deployment_yaml(deploy_file, data)

            # Redeploy
            return self._redeploy(deploy_file, issue.namespace)

        else:
            # Try to update image directly via API
            self.logger.info("No deployment file found, attempting direct fix")
            return self._fix_image_direct(issue, fallback_image)

    def _resolve_image(self, current_image: str, fallback: str) -> str:
        """Resolve image to a working version."""
        # If current image has a tag, try latest
        if ':' in current_image:
            base = current_image.rsplit(':', 1)[0]
            return f"{base}:latest"

        return fallback

    def _fix_image_direct(self, issue: PodIssue, fallback_image: str) -> bool:
        """Fix image directly via Kubernetes API."""
        try:
            # Get the pod to find its deployment
            pod = self.core_v1.read_namespaced_pod(issue.pod_name, issue.namespace)

            # Find owner reference (usually the deployment)
            owner_refs = pod.metadata.owner_references
            if owner_refs:
                for owner in owner_refs:
                    if owner.kind == 'Deployment':
                        deployment_name = owner.name

                        # Get deployment
                        deploy = self.apps_v1.read_namespaced_deployment(
                            deployment_name, issue.namespace
                        )

                        # Update image
                        containers = deploy.spec.template.spec.containers
                        for container in containers:
                            if issue.container and container.name != issue.container:
                                continue
                            container.image = fallback_image

                        # Apply
                        self.apps_v1.patch_namespaced_deployment(
                            deployment_name, issue.namespace,
                            {'spec': {'template': {'spec': {'containers': containers}}}}
                        )

                        self.logger.info(f"Updated deployment {deployment_name} image to {fallback_image}")
                        return True

            self.logger.warning("Could not find owner deployment")
            return False

        except ApiException as e:
            self.logger.error(f"Error fixing image directly: {e}")
            return False

    def _fix_crashloopbackoff(self, issue: PodIssue, strategies: Dict) -> bool:
        """Fix CrashLoopBackOff issue."""
        self.logger.info(f"Fixing CrashLoopBackOff for {issue.pod_name}")

        # Get logs to understand the crash
        logs = get_pod_logs(self.core_v1, issue.namespace, issue.pod_name, issue.container)
        self.logger.debug(f"Container logs:\n{logs[-1000:]}")

        # Find deployment
        deployment_name = issue.pod_name.rsplit('-', 1)[0]
        deployment_dir = self.config.get('deployment', {}).get('deployment_dir', './deployments')
        deploy_file = find_deployment_file(deployment_name, deployment_dir)

        if deploy_file:
            backup_file(deploy_file, self.config.get('deployment', {}).get('backup_dir', './backups'))

            data = load_deployment_yaml(deploy_file)
            spec = data.get('spec', {})
            template = spec.get('template', {})
            containers = template.get('spec', {}).get('containers', [])

            for container in containers:
                if issue.container and container.get('name') != issue.container:
                    continue

                # Add common fixes for CrashLoopBackOff
                # 1. Add startup probe
                if 'startupProbe' not in container:
                    container['startupProbe'] = {
                        'httpGet': {
                            'path': '/healthz',
                            'port': 8080
                        },
                        'failureThreshold': 30,
                        'periodSeconds': 10
                    }

                # 2. Add resource limits if not present
                if 'resources' not in container:
                    container['resources'] = {
                        'requests': {'memory': '128Mi', 'cpu': '100m'},
                        'limits': {'memory': '256Mi', 'cpu': '500m'}
                    }

                self.logger.info("Added startup probe and resource limits")

            save_deployment_yaml(deploy_file, data)
            return self._redeploy(deploy_file, issue.namespace)

        return False

    def _fix_oomkilled(self, issue: PodIssue, strategies: Dict) -> bool:
        """Fix OOMKilled issue."""
        self.logger.info(f"Fixing OOMKilled for {issue.pod_name}")

        strategy = strategies.get('oom_killed', {})
        increase_factor = strategy.get('memory_increase_factor', 2.0)
        max_memory = strategy.get('max_memory_limit', '4Gi')

        # Find deployment
        deployment_name = issue.pod_name.rsplit('-', 1)[0]
        deployment_dir = self.config.get('deployment', {}).get('deployment_dir', './deployments')
        deploy_file = find_deployment_file(deployment_name, deployment_dir)

        if deploy_file:
            backup_file(deploy_file, self.config.get('deployment', {}).get('backup_dir', './backups'))

            data = load_deployment_yaml(deploy_file)
            spec = data.get('spec', {})
            template = spec.get('template', {})
            containers = template.get('spec', {}).get('containers', [])

            for container in containers:
                if issue.container and container.get('name') != issue.container:
                    continue

                resources = container.get('resources', {})
                limits = resources.get('limits', {})

                # Increase memory limit
                current_mem = limits.get('memory', '128Mi')
                current_bytes = parse_memory(current_mem)
                new_bytes = int(current_bytes * increase_factor)
                new_mem = format_memory(new_bytes)

                limits['memory'] = new_mem
                self.logger.info(f"Increased memory limit from {current_mem} to {new_mem}")

                # Also increase requests if lower than limits
                requests = resources.get('requests', {})
                req_mem = requests.get('memory', '64Mi')
                if parse_memory(req_mem) < new_bytes:
                    requests['memory'] = format_memory(int(new_bytes * 0.75))

                container['resources'] = {'limits': limits, 'requests': requests}

            save_deployment_yaml(deploy_file, data)
            return self._redeploy(deploy_file, issue.namespace)

        return False

    def _fix_pending(self, issue: PodIssue, strategies: Dict) -> bool:
        """Fix Pending issue."""
        self.logger.info(f"Fixing Pending status for {issue.pod_name}")

        # Get events to understand why pending
        events = get_pod_events(self.core_v1, issue.namespace, issue.pod_name)

        for event in events:
            reason = event.get('reason', '')
            message = event.get('message', '')

            if 'Insufficient' in message or 'NoNodesAvailable' in reason:
                self.logger.warning("Insufficient cluster resources - cannot auto-fix")
                return False

            if 'Unschedulable' in reason:
                # Try adding node selector or tolerations
                deployment_name = issue.pod_name.rsplit('-', 1)[0]
                deployment_dir = self.config.get('deployment', {}).get('deployment_dir', './deployments')
                deploy_file = find_deployment_file(deployment_name, deployment_dir)

                if deploy_file:
                    backup_file(deploy_file, self.config.get('deployment', {}).get('backup_dir', './backups'))

                    data = load_deployment_yaml(deploy_file)
                    spec = data.get('spec', {})
                    template = spec.get('template', {})
                    pod_spec = template.get('spec', {})

                    # Add tolerations for NoSchedule
                    tolerations = pod_spec.get('tolerations', [])
                    tolerations.append({
                        'key': 'node.kubernetes.io/not-ready',
                        'operator': 'Exists',
                        'effect': 'NoSchedule',
                        'tolerationSeconds': 300
                    })
                    pod_spec['tolerations'] = tolerations

                    save_deployment_yaml(deploy_file, data)
                    return self._redeploy(deploy_file, issue.namespace)

        return False

    def _fix_evicted(self, issue: PodIssue, strategies: Dict) -> bool:
        """Fix Evicted issue."""
        self.logger.info(f"Fixing Evicted status for {issue.pod_name}")

        # Just redeploy the pod
        deployment_name = issue.pod_name.rsplit('-', 1)[0]
        deployment_dir = self.config.get('deployment', {}).get('deployment_dir', './deployments')
        deploy_file = find_deployment_file(deployment_name, deployment_dir)

        if deploy_file:
            return self._redeploy(deploy_file, issue.namespace)

        return False

    def _redeploy(self, deploy_file: str, namespace: str) -> bool:
        """Redeploy using kubectl apply."""
        import subprocess

        self.logger.info(f"Redeploying {deploy_file}")

        try:
            result = subprocess.run(
                ['kubectl', 'apply', '-f', deploy_file],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info(f"Redeployment successful: {result.stdout}")
                return True
            else:
                self.logger.error(f"Redeployment failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error during redeploy: {e}")
            return False

    def wait_for_running(self, pod_name: str, namespace: str, timeout: int = None) -> bool:
        """Wait for pod to reach Running state."""
        timeout = timeout or self.timeout
        start_time = time.time()

        self.logger.info(f"Waiting for {pod_name} to reach Running state (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            try:
                pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
                status = get_pod_status(pod)

                if status == "Running":
                    # Check if all containers are ready
                    ready = all(
                        cs.ready for cs in (pod.status.container_statuses or [])
                    )
                    if ready:
                        self.logger.info(f"Pod {pod_name} is now Running!")
                        return True

                elif status in ["Failed", "Succeeded"]:
                    self.logger.warning(f"Pod {pod_name} is {status}, not Running")
                    return False

            except ApiException as e:
                self.logger.error(f"Error checking pod status: {e}")

            time.sleep(5)

        self.logger.warning(f"Timeout waiting for {pod_name} to become Running")
        return False

    def process_issue(self, issue: PodIssue) -> bool:
        """Process a single issue: diagnose, fix, verify."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Processing issue for {issue.pod_name}")
        self.logger.info(f"Issue type: {issue.issue_type}")
        self.logger.info(f"{'='*60}")

        # Diagnose
        diagnosis = self.diagnose_issue(issue)
        self.logger.info(f"Diagnosis:\n{diagnosis}")

        # Attempt fix
        success = self.fix_issue(issue)

        if success:
            issue.fixed = True
            self.fixed_issues.append(issue)
            self.logger.info(f"Fix applied successfully to {issue.pod_name}")

            # Wait for pod to become running
            if not self.dry_run:
                if self.wait_for_running(issue.pod_name, issue.namespace):
                    self.logger.info(f"Verified: {issue.pod_name} is now Running!")
                else:
                    self.logger.warning(f"Could not verify {issue.pod_name} is Running")
        else:
            self.failed_fixes.append(issue)
            self.logger.error(f"Failed to fix {issue.pod_name}")

        return success

    def run(self):
        """Main agent loop."""
        self.logger.info(f"Starting Kubernetes Agent - monitoring namespace: {self.namespace}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Auto-fix enabled: {self.auto_fix}")
        self.logger.info(f"Dry-run mode: {self.dry_run}")

        try:
            while True:
                issues = self.detect_issues()

                if issues:
                    self.logger.info(f"\nDetected {len(issues)} issue(s):")
                    for issue in issues:
                        self.logger.info(f"  - {issue.pod_name}: {issue.issue_type}")

                    # Process each issue
                    for issue in issues:
                        self.process_issue(issue)

                    # Summary
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info("Summary:")
                    self.logger.info(f"  Fixed: {len(self.fixed_issues)}")
                    self.logger.info(f"  Failed: {len(self.failed_fixes)}")
                    self.logger.info(f"{'='*60}\n")
                else:
                    self.logger.debug("No issues detected")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Agent error: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Kubernetes Agentic AI - Auto-fix pod issues"
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--namespace', '-n',
        default=None,
        help='Kubernetes namespace to monitor (default: from config)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (detect issues but do not fix)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once instead of continuous loop'
    )

    args = parser.parse_args()

    agent = KubernetesAgent(config_path=args.config, dry_run=args.dry_run)

    if args.namespace:
        agent.namespace = args.namespace

    if args.once:
        issues = agent.detect_issues()
        if issues:
            print(f"\nDetected {len(issues)} issue(s):")
            for issue in issues:
                print(f"  - {issue.pod_name}: {issue.issue_type}")
                print(f"    Reason: {issue.reason}")
                print(f"    Message: {issue.message}")
        else:
            print("No issues detected")
    else:
        agent.run()


if __name__ == "__main__":
    main()