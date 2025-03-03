from fastapi import APIRouter, BackgroundTasks, HTTPException
import uuid
from uuid import UUID
from app.models import WorkflowRequest, WorkflowResponse, MessagePayload
from app.rabbitmq.publisher import publish_message
from app.utils.pipeline_manager import start_pipeline, advance_pipeline, remove_pipeline
from app.utils.logger import DefaultLogger

logger = DefaultLogger("OrchestrationService").get_logger()

router = APIRouter()

@router.post("/workflows", response_model=WorkflowResponse)
async def start_workflow(workflow_request: WorkflowRequest, background_tasks: BackgroundTasks):
    correlation_id = uuid.uuid4()
    logger.info(f"Received new workflow request. Assigned correlation_id: {correlation_id}")
    
    if workflow_request.pipeline:
        tasks = [task.name for task in workflow_request.pipeline.tasks]
        if not tasks:
            logger.error("Pipeline provided but contains no tasks")
            raise HTTPException(status_code=400, detail="Pipeline provided but contains no tasks.")
        
        start_pipeline(correlation_id, tasks)
        first_task = tasks[0]
        logger.info(f"Initialized pipeline with tasks: {tasks}")
    else:
        first_task = workflow_request.workflow_type
        logger.info(f"No pipeline provided, using default workflow type: {first_task}")

    message = MessagePayload(
        correlation_id=correlation_id,
        task=first_task,
        payload=workflow_request.dict()
    )
    # Publish the first task message with RabbitMQ
    background_tasks.add_task(publish_message, message.dict(), first_task)
    logger.info(f"Published initial task '{first_task}' with correlation_id: {correlation_id}")

    return WorkflowResponse(correlation_id=correlation_id, message="Workflow started successfully")

@router.post("/workflows/{correlation_id}/complete")
async def complete_task(correlation_id: str, task_completion: dict, background_tasks: BackgroundTasks):
    """
    This endpoint is meant to be called by downstream services when they complete their task.
    The payload can contain additional data from the task. The orchestration service then
    triggers the next task in the pipeline if available.
    """
    logger.info(f"Received task completion callback for correlation_id: {correlation_id}")
    try:
        cid = UUID(correlation_id)
    except Exception as e:
        logger.error(f"Invalid correlation_id format: {correlation_id}. Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid correlation_id format.")

    next_task = advance_pipeline(cid)
    if next_task:
        message = MessagePayload(
            correlation_id=cid,
            task=next_task,
            payload=task_completion # Task_completion payload might change, leave like dict for now
        )
        background_tasks.add_task(publish_message, message.dict(), next_task)
        logger.info(f"Triggered next task '{next_task}' for correlation_id: {cid}")
        return {"message": f"Next task '{next_task}' triggered."}
    else:
        remove_pipeline(cid)
        logger.info(f"Pipeline completed for correlation_id: {cid}")
        return {"message": "Pipeline completed successfully."}
