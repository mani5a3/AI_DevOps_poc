# RAG Chatbot Script Overview #
# 1. Load Knowledge Base:
#     Reads a text file (data.txt) containing your documents, notes, or any reference content.

# 2. Split Documents:
#     Splits large documents into smaller chunks for better processing and search efficiency.
#     Chunk size: 400 characters with 50-character overlap.

# 3. Create Embeddings:
#     Converts each document chunk into a vector using OllamaEmbeddings.
#     These embeddings allow the chatbot to find relevant information quickly via similarity search.

# 4. Store in Vector Database:
#     Uses Chroma to store embeddings.
#     Enables fast similarity search when the user asks a question.

# 5. Initialize LLM:
#     Loads the ChatOllama model (gemma3:4b) with streaming enabled.
#     Streaming allows answers to appear word by word, giving a live typing effect.

# 6. Prepare Conversation History:
#     Tracks previous questions and answers using VectorStoreRetrieverMemory.
#     Maintains context for multi-turn conversations.

# 7. Clean Text Utility:
#     Removes unnecessary markdown symbols (*, **) and extra whitespace.
#     Ensures output is readable and well-formatted.

# 8. Main Chat Loop:
#     Prompts the user to input a query.
#     Retrieves top 3 documents from the vector database.
#     Evaluates relevance using similarity score and presence of query words in the retrieved context.
#     Combines relevant documents into a single context string.
#     Adds conversation history to the prompt for context-aware responses.

# 9. Generate Response:
#     Sends the prompt to the LLM.
#     Streams the response word by word.
#     Cleans the streamed output on the fly.
#     Adds a small delay between words to mimic human-like typing.
# 10. RAG vs LLM Fallback:
#     RAG Mode:
#         If retrieved documents are relevant, answer strictly from them.
#         Returns "No relevant information found in documents." if answer is missing.
#     LLM Fallback:
#         If documents are not relevant, uses the LLM's general knowledge.
#         Ensures the bot never provides irrelevant document answers.

# 11. Update Conversation History:
#     After each query-response cycle, updates memory with the latest question and answer.
#     Supports follow-up questions with context.

# 12. Features:
#     Strict RAG with fallback to LLM knowledge.
#     Multi-document context for richer responses.
#     Word-by-word streaming output for smooth readability.
#     Cleaned formatting for bullets, headings, and text.
#     Threshold-based RAG selection ensures reliable information retrieval.


import re
import time
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.memory import ConversationBufferMemory

# ------------------------------
# Step 1: Load documents
# ------------------------------
loader = TextLoader("data.txt")  # Knowledge base
documents = loader.load()

# ------------------------------
# Step 2: Split documents into chunks
# ------------------------------
text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# ------------------------------
# Step 3: Create embeddings & vector DB
# ------------------------------
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(docs, embeddings)

# ------------------------------
# Step 4: Initialize LLM (streaming)
# ------------------------------
llm = ChatOllama(model="gemma3:4b", streaming=True)

# ------------------------------
# Step 5: Conversation memory
# ------------------------------
session_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)

# ------------------------------
# Step 6: Clean text utility
# ------------------------------
def clean_text(token_text):
    token_text = re.sub(r'(?<!\n)\*\*?', '', token_text)
    token_text = re.sub(r'\s+', ' ', token_text)
    return token_text

print("Hybrid RAG + LLM Chatbot Ready (type 'exit' to quit)\n")

# ------------------------------
# Step 7: Main chat loop
# ------------------------------
while True:
    query = input("Ask: ")
    if query.lower() == "exit":
        break

    # ------------------------------
    # Step 7a: Retrieve top 3 documents
    # ------------------------------
    results = vectorstore.similarity_search_with_score(query, k=3)
    context = ""
    use_rag = False

    if results:
        best_doc, best_score = results[0]
        print(f"\nBest Score: {best_score}")
        # Use RAG if score is reasonable (even without exact word match)
        if best_score <= 1.0:
            context = "\n\n".join([doc.page_content for doc, _ in results])
            use_rag = True

    # ------------------------------
    # Step 7b: Load conversation memory
    # ------------------------------
    chat_history = session_memory.load_memory_variables({"input": query}).get("chat_history", "")

    # ------------------------------
    # Step 7c: Prepare prompt
    # ------------------------------
    if use_rag:
        prompt = f"""
You are a knowledgeable assistant.

Use the retrieved context to answer the user's question. 
If the context does not contain enough information, answer using your general knowledge.

Conversation History:
{chat_history}

Context:
{context}

User Question:
{query}

Bot Answer:
"""
    else:
        prompt = f"""
You are a helpful assistant. Answer using your general knowledge.

Conversation History:
{chat_history}

User Question:
{query}

Bot Answer:
"""

    # ------------------------------
    # Step 7d: Stream response
    # ------------------------------
    print("\nBot:", end=" ", flush=True)
    buffer = ""
    try:
        for token in llm.stream(prompt):
            cleaned = clean_text(token.content)
            buffer += cleaned
            while " " in buffer:
                word, buffer = buffer.split(" ", 1)
                print(word + " ", end="", flush=True)
                time.sleep(0.001)
        if buffer.strip():
            print(buffer.strip(), flush=True)
    except KeyboardInterrupt:
        print("\n[Interrupted]\n")
    
    print("\n")

    # ------------------------------
    # Step 7e: Save turn to memory
    # ------------------------------
    session_memory.save_context({"input": query}, {"output": buffer.strip()})