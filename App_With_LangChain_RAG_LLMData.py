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

    # Search top matches
    results = vectorstore.similarity_search_with_score(query, k=3)

    # Pick best match
    best_doc, best_score = results[0]

    print(f"\nBest Score: {best_score}")

    # Good match → Use RAG
    if best_score < 1.0:
        print(" Using RAG data")

        context = best_doc.page_content

        prompt = f"""
You are a helpful assistant.

Use the context below to answer the question.

Context:
{context}

Question:
{query}
"""

        response = llm.invoke(prompt)

    #  No good match → Use model knowledge
    else:
        print("Using model knowledge")

        response = llm.invoke(query)

    print("\n Bot:", response.content, "\n")