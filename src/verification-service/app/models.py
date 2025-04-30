from pydantic import BaseModel
from typing import List


class SearchResult(BaseModel):
    Title: str
    Date: str
    Summary: str
    Source: str

class VerificationResult(BaseModel):
    claim: str
    verdict: str  # 'true', 'false', or 'undetermined'
    evidence: List[str]