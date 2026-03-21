Download ollama from browser and install it on your machine
pip install requests
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


using langchain install plugin using 

 pip install greenlet --only-binary :all:
 pip install langchain langchain-community