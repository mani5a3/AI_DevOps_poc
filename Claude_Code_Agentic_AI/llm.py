"""
LLM Integration Module for Kubernetes Agentic AI

Supports:
- Ollama (local, free)
- OpenAI (optional)
- Anthropic (optional)
"""

import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("k8s-agent.llm")


class LLMClient:
    """LLM client for intelligent diagnosis and fixes."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('llm', {})
        self.enabled = self.config.get('enabled', True)
        self.provider = self.config.get('provider', 'ollama')
        self.model = self.config.get('model', 'llama3')
        self.temperature = self.config.get('temperature', 0.1)
        self.max_tokens = self.config.get('max_tokens', 1000)

        self.client = None
        if self.enabled:
            self._init_client()

    def _init_client(self):
        """Initialize the LLM client."""
        if self.provider == 'ollama':
            self._init_ollama()
        elif self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'anthropic':
            self._init_anthropic()
        else:
            logger.warning(f"Unknown LLM provider: {self.provider}, using rule-based only")
            self.enabled = False

    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            import ollama
            self.client = ollama
            # Verify connection
            try:
                ollama.list()
                logger.info(f"Ollama initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Ollama not running: {e}. Using rule-based only.")
                self.enabled = False
                self.client = None
        except ImportError:
            logger.warning("ollama package not installed. Run: pip install ollama")
            self.enabled = False

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            api_key = self.config.get('api_key') or self.config.get('OPENAI_API_KEY')
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.warning("openai package not installed")
            self.enabled = False

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            api_key = self.config.get('api_key') or self.config.get('ANTHROPIC_API_KEY')
            self.client = Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized")
        except ImportError:
            logger.warning("anthropic package not installed")
            self.enabled = False

    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.enabled and self.client is not None

    def chat(self, system: str, user: str) -> Optional[str]:
        """Send chat request to LLM."""
        if not self.is_available():
            return None

        try:
            if self.provider == 'ollama':
                return self._chat_ollama(system, user)
            elif self.provider == 'openai':
                return self._chat_openai(system, user)
            elif self.provider == 'anthropic':
                return self._chat_anthropic(system, user)
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return None

    def _chat_ollama(self, system: str, user: str) -> Optional[str]:
        """Send chat to Ollama."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user}
                ],
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    def _chat_openai(self, system: str, user: str) -> Optional[str]:
        """Send chat to OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get('openai_model', 'gpt-3.5-turbo'),
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    def _chat_anthropic(self, system: str, user: str) -> Optional[str]:
        """Send chat to Anthropic."""
        try:
            response = self.client.messages.create(
                model=self.config.get('anthropic_model', 'claude-3-haiku-20240307'),
                system=system,
                messages=[{'role': 'user', 'content': user}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            return None


# System prompts for Kubernetes diagnosis
K8S_DIAGNOSIS_SYSTEM = """You are an expert Kubernetes AI assistant. Your task is to diagnose ANY Kubernetes issue and provide fixes.

## Supported Issue Types:

### POD ISSUES:
- ImagePullBackOff, ErrImagePull - Image errors
- CrashLoopBackOff - Container crashes/restarts
- OOMKilled - Out of Memory kills (exit code 137)
- Evicted - Pod evicted due to node pressure
- Pending - Pod scheduling failures
- Terminating - Stuck in terminating state
- Unknown - Unclear status
- InitCrashLoopBackOff - Init container crashes

### DEPLOYMENT ISSUES:
- ReplicaSet failures
- Deployment rollout failures
- Scale issues

### SERVICE ISSUES:
- Service not reachable
- Endpoint not ready
- Port conflicts
- Service type issues

### INGRESS ISSUES:
- Ingress controller errors
- TLS/certificate issues
- Routing errors
- 404/502/503 errors

### CONFIGMAP/SECRET ISSUES:
- Mount errors
- Key not found
- Invalid data

### PVC/STORAGE ISSUES:
- Pending PVC
- Storage class issues
- Mount errors
- Volume mode issues

### RBAC/AUTH ISSUES:
- Forbidden errors
- Unauthorized access
- Role binding issues

### NETWORK ISSUES:
- DNS resolution failures
- Connection timeouts
- NetworkPolicy blocking

### NODE ISSUES:
- Node NotReady
- Disk pressure
- Memory pressure
- CPU pressure

## Your Task:
Analyze the provided Kubernetes resource information (events, logs, specs, status) and:
1. Identify the EXACT root cause
2. Determine the issue category
3. Suggest specific YAML fixes or kubectl commands
4. Provide confidence score

Respond ONLY in JSON format:
{
    "issue_category": "pod|deployment|service|ingress|configmap|pvc|rbac|network|node|unknown",
    "diagnosis": "Root cause in 1-2 sentences",
    "fix_type": "image_update|resource_increase|env_var_fix|config_fix|command_fix|security_context|volume_fix|service_fix|ingress_fix|rbac_fix|network_fix|storage_fix|redeploy|delete_and_recreate",
    "yaml_patch": {"path/to/field": "new_value"},
    "kubectl_commands": ["kubectl apply -f fix.yaml", "kubectl delete pod x"],
    "confidence": 0.0-1.0
}"""

K8S_FIX_SYSTEM = """You are a Kubernetes expert. Generate the exact YAML changes needed to fix ANY Kubernetes issue.

Current resource YAML:
{current_yaml}

Issue: {issue_type}
Diagnosis: {diagnosis}

Respond with ONLY the modified YAML (complete or partial). Include only the parts that need to change."""


def build_diagnosis_prompt(pod_name: str, namespace: str, issue_type: str,
                           events: List[Dict], logs: str, pod_spec: Dict) -> str:
    """Build diagnosis prompt for LLM."""
    prompt = f"""Pod: {pod_name}
Namespace: {namespace}
Issue Type: {issue_type}

Pod Events:
"""
    for event in events[:10]:
        prompt += f"- {event.get('reason')}: {event.get('message')}\n"

    if logs:
        prompt += f"\nContainer Logs (last 2000 chars):\n{logs[-2000:]}\n"

    prompt += f"\nPod Spec:\n{json.dumps(pod_spec, indent=2)[:3000]}"

    return prompt


def parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse LLM JSON response."""
    try:
        # Try to find JSON in response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: return raw response
    return {
        "diagnosis": response,
        "fix_type": "unknown",
        "confidence": 0.0
    }