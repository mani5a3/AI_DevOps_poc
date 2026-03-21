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
