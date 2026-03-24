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

def clean_token_text(text):
    """
    Remove unwanted Markdown '*' in the middle of sentences.
    Keeps basic readability like headings or newlines.
    """
    # Remove '**' and '*' except at start of line (for bullets)
    text = re.sub(r'(?<!\n)\*\*?', '', text)
    # Optional: collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text

while True:
    query = input("Ask: ")
    if query.lower() == "exit":
        break

    # Search top matches
    results = vectorstore.similarity_search_with_score(query, k=3)
    best_doc, best_score = results[0]
    print(f"\nBest Score: {best_score}")

    # Build prompt
    if best_score < 1.0:
        print("Using RAG data")
        context = best_doc.page_content
        prompt = f"""
You are a helpful assistant.
Prefer the provided context if relevant. If insufficient, use general knowledge.

Context:
{context}

Question:
{query}
"""
    else:
        print("Using model knowledge")
        prompt = query

    # Stream the response token by token and clean it
    print("\nBot:", end=" ", flush=True)
    for token in llm.stream(prompt):
        cleaned_text = clean_token_text(token.content)
        print(cleaned_text, end="", flush=True)
    print("\n")