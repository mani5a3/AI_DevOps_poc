AI Agent:
    Uses LLM every iteration
Agentic AI:
    Uses LLM only when needed
    
agent.invoke({"input": status})
            What it means:
                You delegate full control to LLM
                    LLM:
                    reads prompt
                    decides tool
                    executes tool
                    decides next step

LLM(prompt + tools description) → action:
            agent = initialize_agent(
                tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            )