from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from app.utils.logger import DefaultLogger
from app.models import VerificationResult, ClaimRequest
from app.core.verifier import ClaimVerifier

router = APIRouter()
logger = DefaultLogger().get_logger()


@router.post("/claim", response_model=VerificationResult)
async def verify_claim(request: ClaimRequest):
    logger.info(f"Received request to verify claim: {request.Claim}")
    result = await ClaimVerifier.get_verifier().verify(request.Claim)
    return result