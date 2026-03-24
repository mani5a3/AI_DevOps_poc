import re
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

# Initialize LLM with streaming enabled
llm = ChatOllama(model="gemma3:4b", streaming=True)

print("RAG Chatbot Ready (type 'exit' to quit)\n")

def clean_text(token_text):
    """
    Clean Markdown artifacts like '*' or '**' in the middle of sentences
    while preserving line-start bullets.
    """
    # Remove '**' and '*' that are not at the start of a line
    token_text = re.sub(r'(?<!\n)\*\*?', '', token_text)
    # Optional: collapse multiple spaces
    token_text = re.sub(r'\s+', ' ', token_text)
    return token_text

while True:
    query = input("Ask: ")
    if query.lower() == "exit":
        break

    # Search top 3 matches
    results = vectorstore.similarity_search_with_score(query, k=3)
    best_doc, best_score = results[0]
    print(f"\nBest Score: {best_score}")

    if best_score > 1.2:
        print("\nNo relevant information found in documents.\n")
        continue

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

    # Stream the response and clean each token
    print("\nBot:", end=" ", flush=True)
    for token in llm.stream(prompt):
        print(clean_text(token.content), end="", flush=True)
    print("\n")