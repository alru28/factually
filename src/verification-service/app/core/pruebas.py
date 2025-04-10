from pydantic_ai import Agent, UnexpectedModelBehavior, capture_run_messages
from typing import Union, Literal
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import os

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'cogito:8b')

class PokemonCore(BaseModel):
    name: str = Field(..., description="Name of the Pokémon.")
    description: str = Field(..., description="Short text description of the Pokémon's characteristics.")

class PokemonTypes(BaseModel):
    main_type: str = Field(..., description="Primary type of the Pokémon (e.g., Fire).")
    secondary_type: str = Field(..., description="Secondary type of the Pokémon (e.g., Rock).")

class Pokemon(BaseModel):
    core: PokemonCore
    types: PokemonTypes

class Failed(BaseModel):
    message: str = Field(..., description="Failure reason.")


ollama_model = OpenAIModel(
    model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)

core_agent = Agent(
    ollama_model,
    retries=5,
    instrument=True,
    result_type=Union[PokemonCore, Failed],
    system_prompt='Enable deep thinking subroutine. Generate a creative Pokémon name and its characteristics.'
)

types_agent = Agent(
    ollama_model,
    retries=5,
    instrument=True,
    result_type=Union[PokemonTypes, Failed],
    system_prompt='Enable deep thinking subroutine. Generate creative details for primary and secondary Pokémon types.'
)


def generate_pokemon():
    with capture_run_messages() as core_messages:
        try:
            core_result = core_agent.run_sync('Generate the Pokémon name and description.')
            if not isinstance(core_result.data, PokemonCore):
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
            if not isinstance(types_result.data, PokemonTypes):
                print("Types generation failed:", types_result.data)
                return
        except UnexpectedModelBehavior as e:
            print('An error occurred in types generation:', e)
            print('cause:', repr(e.__cause__))
            print('messages:', types_messages)
            return

    pokemon = Pokemon(core=core_result.data, types=types_result.data)
    print("Generated Pokémon:")
    print(pokemon)
    print("\nUsage stats:")
    print("Core agent usage:", core_result.usage())
    print("Types agent usage:", types_result.usage())

if __name__ == "__main__":
    generate_pokemon()
