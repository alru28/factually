from pydantic import BaseModel
from typing import List


class SearchResult(BaseModel):
    Title: str
    Date: str
    Summary: str
    Source: str

class EvidenceItem(BaseModel):
    Title: str
    Source: str
    Date: str

class VerificationResult(BaseModel):
    Claim: str
    Verdict: str
    Evidence: List[EvidenceItem]