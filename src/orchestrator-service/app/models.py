from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date

class PipelineTask(BaseModel):
    name: str = Field(
        ...,
        description="Name of the task (e.g., 'extraction', 'transformation', 'storage')"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task-specific parameters (overrides or additional data)"
    )

class Pipeline(BaseModel):
    tasks: List[PipelineTask] = Field(
        ...,
        description="Ordered list of tasks for the workflow"
    )

class WorkflowRequest(BaseModel):
    workflow_type: str = Field(
        ...,
        description="Type of workflow, e.g. 'extract_store_transform_store'"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="List of source ids to process"
    )
    articles: Optional[List[str]] = Field(
        default=None,
        description="List of article ids to process"
    )
    start_date: date = Field(..., description="Start date for scraping")
    end_date: date = Field(..., description="End date for scraping")
    pipeline: Optional[Pipeline] = Field(
        default=None,
        description="Optional pipeline of tasks. If provided, tasks in this list will be executed sequentially."
    )
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any extra parameters needed for the workflow"
    )

class WorkflowResponse(BaseModel):
    correlation_id: UUID
    message: str

class MessagePayload(BaseModel):
    correlation_id: UUID
    task: str
    payload: Dict[str, Any]
    version: str = "1.0"
