from pydantic_ai import Agent, UnexpectedModelBehavior, capture_run_messages
from typing import Union, Literal, List
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from app.models import VerificationResult

import os

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'cogito:8b')



ollama_model = OpenAIModel(
            model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        )
agent = Agent(
            ollama_model,
            result_type=VerificationResult,
            instrument=True,
            system_prompt=(
                "You evaluate whether a claim is true or false based on provided news contexts. "
                "Respond with JSON matching VerificationResult."
            ),
        )

prompt = """
    Claim: {claim}\n
    Context: {context}\n
    Based on the above, is the claim True, False, or Undetermined?
    List up to three supporting evidence passages and reference them."
"""

result = agent.run_sync(prompt)
print(result.output)
print(result.usage())

core_agent = Agent(
    ollama_model,
    retries=5,
    instrument=True,
    output_type=Union[PokemonCore, Failed],
    system_prompt='Enable deep thinking subroutine. Generate a creative Pokémon name and its characteristics.'
)

types_agent = Agent(
    ollama_model,
    retries=5,
    instrument=True,
    output_type=Union[PokemonTypes, Failed],
    system_prompt='Enable deep thinking subroutine. Generate creative details for primary and secondary Pokémon types.'
)


def generate_pokemon():
    with capture_run_messages() as core_messages:
        try:
            core_result = core_agent.run_sync('Generate the Pokémon name and description.')
            if not isinstance(core_result.output, PokemonCore):
                print("Core generation failed:", core_result.data)
                return
        except UnexpectedModelBehavior as e:
            print('An error occurred in core generation:', e)
            print('cause:', repr(e.__cause__))
            print('messages:', core_messages)
            return

    with capture_run_messages() as types_messages:
        try:
            types_result = types_agent.run_sync('Generate the Pokémon main type and secondary type.')
            if not isinstance(types_result.output, PokemonTypes):
                print("Types generation failed:", types_result.data)
                return
        except UnexpectedModelBehavior as e:
            print('An error occurred in types generation:', e)
            print('cause:', repr(e.__cause__))
            print('messages:', types_messages)
            return

    pokemon = Pokemon(core=core_result.output, types=types_result.output)
    print("Generated Pokémon:")
    print(pokemon)
    print("\nUsage stats:")
    print("Core agent usage:", core_result.usage())
    print("Types agent usage:", types_result.usage())

if __name__ == "__main__":
    generate_pokemon()
