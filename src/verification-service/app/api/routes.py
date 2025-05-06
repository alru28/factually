from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from typing import List
from app.utils.logger import DefaultLogger
from app.models import VerificationResult
from app.core.verifier import ClaimVerifier

router = APIRouter()
logger = DefaultLogger("VerificationService").get_logger()


@router.get("/test", response_model=VerificationResult)
async def test_claim(claim: str = Query(..., description="The claim string to verify")):
    result = await ClaimVerifier.get_verifier().verify(claim)
    return result