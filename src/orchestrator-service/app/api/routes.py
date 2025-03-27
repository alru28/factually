from fastapi import APIRouter, BackgroundTasks, HTTPException
import uuid
from uuid import UUID
from app.models import WorkflowRequest, WorkflowResponse, MessagePayload
from app.rabbitmq.operations import publish_message
from app.utils.logger import DefaultLogger

logger = DefaultLogger("OrchestrationService").get_logger()

router = APIRouter()

@router.post("/workflows", response_model=WorkflowResponse)
async def start_workflow(workflow_request: WorkflowRequest, background_tasks: BackgroundTasks):
    correlation_id = uuid.uuid4()
    logger.info(f"Received new workflow request. Assigned correlation_id: {correlation_id}")
    
    initial_task = workflow_request.workflow_type
    if initial_task == "extraction_transformation":
        queue = "extraction"
    elif initial_task == "transformation":
        queue = "transformation"
    elif initial_task == "extraction":
        queue = "extraction"
    else:
        logger.error(f"Invalid workflow type: {initial_task}. Supported types are 'extraction_transformation', 'transformation', 'extraction'.")
        raise HTTPException(status_code=400, detail="Invalid workflow type. Supported types are 'extraction_transformation', 'transformation', 'extraction'.")

    payload = {
    "sources": workflow_request.sources,
    "articles": workflow_request.articles,
    "date_base": workflow_request.date_base.isoformat(),
    "date_cutoff": workflow_request.date_cutoff.isoformat()
    }

    message = MessagePayload(
        correlation_id=correlation_id,
        task=initial_task,
        payload=payload
    )

    # Publish the first task message with RabbitMQ
    await publish_message(message.dict(), queue)
    logger.info(f"Published initial task '{initial_task}' with correlation_id: {correlation_id}")

    return WorkflowResponse(correlation_id=correlation_id, message="Workflow started successfully")
