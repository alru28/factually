from pydantic_ai import Agent
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import os

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'cogito:3b')

class Pokemon(BaseModel):
    name: str
    pokedex_description: str
    main_type: str
    secondary_type: str


ollama_model = OpenAIModel(
    model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)
agent = Agent(ollama_model, retries=3, instrument=True, result_type=Pokemon, system_prompt='Enable deep thinking subroutine.')

result = agent.run_sync('Generate a cool pokemon that comes from space.')
print(result.data)
print(result.usage())