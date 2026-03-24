# ChatOllama is Bridge between LangChain and Ollama chat models
# LangChain: Talks to Ollama internally and Handles API calls for you
# What it gives you
#     ✔ Built-in chat handling
#     ✔ Memory management
#     ✔ Prompt templates
#     ✔ Easy RAG integration
#     ✔ Tool integration (GitHub, APIs, DBs)
#     ✔ Clean architecture

# User → ConversationChain → Memory → LLM → response

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

print("Ollama Chatbot (Streaming + Memory) - type 'exit' to quit\n")

# Initialize model connects Python → Ollama model and temperature=0.7 → slightly creative answers
llm = ChatOllama(
    model="gemma3:4b",
    temperature=0.7
) 

# Store session histories
store = {}

# Checks if user already has memory, If not → creates new memory and Returns memory object
def get_session_history(session_id: str):
    if session_id not in store: # check if user exists
        store[session_id] = InMemoryChatMessageHistory() # check if user exists
    return store[session_id] # return memory

# Wrap LLM with memory
chain = RunnableWithMessageHistory(
    llm,
    get_session_history
)

session_id = "user1"

while True:
    query = input("Ask your Question: ")

    if query.lower() == "exit":
        print("Exiting...")
        break

    print("Bot: ", end="", flush=True)

    # ✅ STREAMING RESPONSE
    for chunk in chain.stream(
        [HumanMessage(content=query)],
        config={"configurable": {"session_id": session_id}}
    ):
        if chunk.content:
            clean_text = chunk.content.replace("*", "")
            print(clean_text, end="", flush=True)

    print("\n")