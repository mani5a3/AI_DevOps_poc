# Creates AI agent
# Connects LLM + tools
# Read input
# Apply SYSTEM_PROMPT rules
# Decide action
# Call tool
# Get result
# Repeat if needed


from langchain.agents import initialize_agent, AgentType
from langchain_ollama import OllamaLLM
from tools import tools
from prompt import SYSTEM_PROMPT

def create_agent():
    llm = OllamaLLM(model="gemma3:4b")  # faster & stable

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs={"system_message": SYSTEM_PROMPT}
    )

    return agent