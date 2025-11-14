from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-2.5-pro',
    name='Genghis_khan',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
