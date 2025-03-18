from typing import List
from uuid import UUID
from app.utils.logger import DefaultLogger

logger = DefaultLogger("OrchestrationService").get_logger()

# Memory storage for Pipeline executions, change to DB ?
pipeline_executions = {}

class PipelineExecution:
    def __init__(self, tasks: List[str]):
        self.tasks = tasks
        self.current_index = 0
        logger.info(f"PipelineExecution created with tasks: {tasks}")

    def current_task(self) -> str:
        if self.current_index < len(self.tasks):
            current = self.tasks[self.current_index]
            logger.debug(f"Current task for pipeline: {current}")
            return current
        logger.debug("No current task; pipeline is complete")
        return None

    def advance(self) -> str:
        self.current_index += 1
        current = self.current_task()
        return current

def start_pipeline(correlation_id: UUID, tasks: List[str]) -> None:
    pipeline_executions[str(correlation_id)] = PipelineExecution(tasks)
    logger.info(f"Started pipeline for correlation_id {correlation_id}")

def get_current_task(correlation_id: UUID) -> str:
    exec_obj = pipeline_executions.get(str(correlation_id))
    if exec_obj:
        current = exec_obj.current_task()
        logger.debug(f"Retrieved current task for pipeline with correlation_id {correlation_id}: [{current}]")
        return current
    logger.warning(f"No pipeline found for correlation_id {correlation_id}")
    return None

def advance_pipeline(correlation_id: UUID) -> str:
    exec_obj = pipeline_executions.get(str(correlation_id))
    if exec_obj:
        next_task = exec_obj.advance()
        logger.info(f"Advanced to task [{next_task}] for pipeline with correlation_id {correlation_id}")
        return next_task
    logger.warning(f"No pipeline found for correlation_id {correlation_id}")
    return None

def remove_pipeline(correlation_id: UUID) -> None:
    if pipeline_executions.pop(str(correlation_id), None):
        logger.info(f"Pipeline with correlation_id {correlation_id} removed")
    else:
        logger.warning(f"No pipeline found for correlation_id {correlation_id}")
