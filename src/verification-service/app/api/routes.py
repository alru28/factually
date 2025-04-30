from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from typing import List
from app.utils.logger import DefaultLogger
from app.models import VerificationResult

router = APIRouter()
logger = DefaultLogger("VerificationService").get_logger()


@router.get("/test", response_model=VerificationResult)
async def test_claim(claim: str = Query(..., description="The claim string to verify")):
    



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
    return {"claim": claim}