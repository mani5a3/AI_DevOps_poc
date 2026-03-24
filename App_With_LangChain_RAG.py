from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader

# Load documents
loader = TextLoader("data.txt")
documents = loader.load()

# Split into chunks
text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# Create embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Store in vector DB
vectorstore = Chroma.from_documents(docs, embeddings)

# Initialize LLM
llm = ChatOllama(model="gemma3:4b")

print("RAG Chatbot Ready (type 'exit' to quit)\n")

while True:
    query = input("Ask: ")

    if query.lower() == "exit":
        break

    # Search top 3 matches
    results = vectorstore.similarity_search_with_score(query, k=3)

    """ print("\n--- Retrieval Debug ---")

    for doc, score in results:
        print(f"\nScore: {score}")
        print("Content:", doc.page_content) """

    #  Pick best match
    best_doc, best_score = results[0]

    print(f"\n Best Score: {best_score}") # vector closest match using cosine similarity

    #  If not relevant enough
    if best_score > 1.2:
        print("\nNo relevant information found in documents.\n")
        continue

    #  Use best context
    context = best_doc.page_content

    # Strict RAG prompt
    prompt = f"""
You are a strict RAG assistant.

Rules:
- Answer ONLY from the provided context
- If answer is not present, say:
  "No relevant information found in documents."

Context:
{context}

Question:
{query}
"""

    # Generate response
    response = llm.invoke(prompt)

    print("\n Bot:", response.content, "\n")