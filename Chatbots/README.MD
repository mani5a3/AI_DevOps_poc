Download ollama from browser and install it on your machine
ollama pull gemma3:4b
ollama run gemma3:4b --> run a model
ollama is engine or server that calls model gemma
Python → Ollama → gemma3 → response
Python → OpenAI API → GPT-4 → response

| Role              | Meaning                          |
| ------------------| -------------------------------- |
| user              | You (the human asking questions) |
| assistant         | AI model’s previous answers      |
| system(optional)  | Instructions to control behavior |

if you miss role assistant, Model doesn’t know what it answered before so context breaks

role assistant Storing model’s previous answers and Maintaining chat history

system assistant using this Set tone / personality and if You want to control behavior

with roles, Model behaves like real chat

install dependencies using ollama: 
            download llm model: ollama pull gemma3:4b
                run llm model: ollama run gemma3:4b   
    download embedding model : ollama pull nomic-embed-text

install dependencies using pip:
        pip install requests
        pip install greenlet --only-binary :all:
        pip install langchain langchain-community
        pip install -U langchain-ollama
        pip install  chromadb pypdf
        pip install pyyaml

ChromaDB: it stores embeddings and retrieves most similar data based on meaning
pypdf: Library to read PDF files


What LangChain does: User → Chain → Memory → LLM → Response
    Stores conversation automatically
    Formats prompt internally
    Injects history into LLM
    Manages structure


To start and stop ollama in your local system:
    netstat -ano | findstr :11434
    wmic process where "ProcessId=<PID>" get ParentProcessId
    taskkill /F /T /PID <ParentPID>
    Start-Process ollama -ArgumentList "serve"