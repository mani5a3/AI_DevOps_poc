from dotenv import load_dotenv
import os

load_dotenv()  # this loads .env file

# Path to your YAML (can be passed dynamically later)
YAML_FILE_PATH = os.getenv("YAML_FILE_PATH", "./k8s/app.yaml")

# Kubernetes namespace (optional)
NAMESPACE = os.getenv("NAMESPACE", "default")

POD_NAME = os.getenv("POD_NAME", "test-pod")

# How many retries
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# Delay between checks
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", "3"))

LABEL_SELECTOR = os.getenv("LABEL_SELECTOR", "app=myapp")

