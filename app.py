# download ollama from browser and install it on your machine
# pip install requests
# ollama pull gemma3:4b
# ollama is engine or server that calls model gemma
# Python → Ollama → gemma3 → response
# Python → OpenAI API → GPT-4 → response

# | Role              | Meaning                          |
# | ------------------| -------------------------------- |
# | user              | You (the human asking questions) |
# | assistant         | AI model’s previous answers      |
# | system(optional)  | Instructions to control behavior |

# if you miss role assistant, Model doesn’t know what it answered before so context breaks
# role assistant Storing model’s previous answers and Maintaining chat history
# system assistant using this Set tone / personality and if You want to control behavior
# with roles, Model behaves like real chat


import requests
import json

print("Ollama Chatbot (type 'exit' to quit)\n")

# Store conversation history
messages = [
{
    "role": "system",
    "content": "You are a helpful and accurate assistant. Answer all questions clearly. For math or logic questions, be precise. If asked about external links (like GitHub), and you cannot access them, say so honestly and do not hallucinate."
}
]
while True:
    query = input("Ask you Question: ")

    if query.lower() == "exit":
        print("Exiting...")
        break

    # Add user message to history
    messages.append({
        "role": "user",
        "content": query
    })
    
    # /api/chat --> it maintains conversation
    # /api/generate -> One-time questions, no chat history
    # /api/pull → Download model
    # /api/embeddings → Convert text to vectors --> used for RAG
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gemma3:4b",
            "messages": messages,
            "stream": True
        },
        stream=True
    )

    print("Bot: ", end="", flush=True)

    full_response = ""

    # Read streaming response
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))

                if "message" in data and "content" in data["message"]:
                    chunk = data["message"]["content"]
                    print(chunk, end="", flush=True)
                    full_response += chunk

            except json.JSONDecodeError:
                continue

    print("\n")

    # Save assistant response to history
    messages.append({
        "role": "assistant",
        "content": full_response
    })
