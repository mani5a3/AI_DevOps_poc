import os
from dotenv import load_dotenv

load_dotenv()

YAML_FILE_PATH = os.getenv("YAML_FILE_PATH")
NAMESPACE = os.getenv("NAMESPACE", "default")
LABEL_SELECTOR = os.getenv("LABEL_SELECTOR")
POD_NAME = os.getenv("POD_NAME")

MAX_ITERATIONS = 10
SLEEP_SECONDS = 5