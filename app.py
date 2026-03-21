# download ollama from browser and install it on your machine
# pip install requests
# ollama pull gemma3:4b

import requests
import json

print("Ollama Chat (type 'exit' to quit)\n")

while True:
    query = input("Ask your question: ")

    if query.lower() == "exit":
        print("Exiting...")
        break

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:4b",
            "prompt": query,
            "stream": True
        },
        stream=True
    )

    print("Answer: ", end="", flush=True)

    # Read streaming response line by line
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))

                # Extract only the text part
                if "response" in data:
                    print(data["response"], end="", flush=True)

            except json.JSONDecodeError:
                continue

    print("\n")  # New line after answer
