# ChatOllama is Bridge between LangChain and Ollama chat models
# LangChain: Talks to Ollama internally and Handles API calls for you
# What it gives you
#     ✔ Built-in chat handling
#     ✔ Memory management
#     ✔ Prompt templates
#     ✔ Easy RAG integration
#     ✔ Tool integration (GitHub, APIs, DBs)
#     ✔ Clean architecture

from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

print("Ollama Chatbot with LangChain (type 'exit' to quit)\n")

# Enable streaming output
callbacks = [StreamingStdOutCallbackHandler()]

# Initialize model
llm = ChatOllama(
    model="gemma3:4b",
    streaming=True,
    callbacks=callbacks
)

# Store conversation history
messages = [
    SystemMessage(
        content="You are a helpful and accurate assistant. Answer all questions clearly. For math or logic questions, be precise. If asked about external links (like GitHub), and you cannot access them, say so honestly and do not hallucinate."
    )
]

while True:
    query = input("Ask you Question: ")

    if query.lower() == "exit":
        print("Exiting...")
        break

    # Add user message
    messages.append(HumanMessage(content=query))

    print("Bot: ", end="", flush=True)

    # Invoke model (streaming happens automatically)
    response = llm.invoke(messages)

    print("\n")

    # Save AI response
    messages.append(AIMessage(content=response.content))