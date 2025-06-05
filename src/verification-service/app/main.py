from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from app.api.routes import router
import uvicorn
from app.utils.logger import DefaultLogger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.verifier import ClaimVerifier
import os
import requests

OLLAMA_CONNECTION_STRING = os.getenv('OLLAMA_CONNECTION_STRING', 'http://ollama:11434')
logger = DefaultLogger().get_logger()


def check_and_pull_model():
    try:
        response = requests.get(f"{OLLAMA_CONNECTION_STRING}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if "qwen3:4b" not in models:
                pull_response = requests.post(f"{OLLAMA_CONNECTION_STRING}/api/pull", json={"name": "qwen3:4b"})
                if pull_response.status_code != 200:
                    raise Exception("Failed to pull llama2 model")
        else:
            raise Exception("Failed to retrieve models from Ollama")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing VerificationService")
    logger.info("Startup event: Initializing Verifier")
    await ClaimVerifier.init_verifier()
    logger.info("Startup event: Initializing Ollama models")
    check_and_pull_model()
    
    yield

app = FastAPI(lifespan=lifespan, title="VerificationService", openapi_url="/openapi.json")

FastAPIInstrumentor.instrument_app(app)

app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting Verification Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
