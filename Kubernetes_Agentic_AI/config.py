"""
Configuration Module - Environment and Agent Settings

Loads configuration from .env and provides defaults.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Kubernetes Configuration
NAMESPACE = os.getenv("NAMESPACE", "default")
LABEL_SELECTOR = os.getenv("LABEL_SELECTOR", "app=test")
POD_NAME = os.getenv("POD_NAME")
YAML_FILE_PATH = os.getenv("YAML_FILE_PATH", "test-pod.yaml")

# Agent Configuration
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "20"))
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", "10"))
WAIT_BETWEEN_RETRIES = int(os.getenv("WAIT_BETWEEN_RETRIES", "5"))

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Fix Configuration
AUTO_FIX_ENABLED = os.getenv("AUTO_FIX_ENABLED", "true").lower() == "true"
BACKUP_YAML = os.getenv("BACKUP_YAML", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
VERBOSE = os.getenv("VERBOSE", "false").lower() == "true"

# Documentation
AUTO_UPDATE_DOCS = os.getenv("AUTO_UPDATE_DOCS", "true").lower() == "true"

# Health Check
HEALTHY_RESTART_THRESHOLD = int(os.getenv("HEALTHY_RESTART_THRESHOLD", "3"))
HEALTHY_CONTAINER_TIMEOUT = int(os.getenv("HEALTHY_CONTAINER_TIMEOUT", "60"))

# Print config on import
def print_config():
    """Print current configuration."""
    print("=" * 50)
    print("AGENTIC AI CONFIGURATION")
    print("=" * 50)
    print(f"Namespace: {NAMESPACE}")
    print(f"Pod Name: {POD_NAME}")
    print(f"YAML File: {YAML_FILE_PATH}")
    print(f"Max Iterations: {MAX_ITERATIONS}")
    print(f"Sleep Seconds: {SLEEP_SECONDS}")
    print(f"LLM Model: {LLM_MODEL}")
    print(f"Auto Fix: {AUTO_FIX_ENABLED}")
    print(f"Auto Update Docs: {AUTO_UPDATE_DOCS}")
    print("=" * 50)


if __name__ == "__main__":
    print_config()