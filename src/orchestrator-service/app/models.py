from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

class WorkflowRequest(BaseModel):
    workflow_type: str = Field(
        ...,
        description="Type of workflow, e.g. 'extraction_transformation'"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="List of source ids to process"
    )
    articles: Optional[List[str]] = Field(
        default=None,
        description="List of article ids to process"
    )
    date_base: date = Field(..., description="Start date for scraping")
    date_cutoff: date = Field(..., description="End date for scraping")

class WorkflowResponse(BaseModel):
    correlation_id: UUID
    message: str

class MessagePayload(BaseModel):
    correlation_id: UUID
    task: str
    payload: Dict[str, Any]
    version: str = "1.0"
