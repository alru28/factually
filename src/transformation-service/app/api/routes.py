from fastapi import APIRouter, BackgroundTasks, HTTPException
from uuid import UUID
from app.models import 
from app.rabbitmq.operations import publish_message
from app.utils.logger import DefaultLogger


logger = DefaultLogger("OrchestrationService").get_logger()

router = APIRouter()