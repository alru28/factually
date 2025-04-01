from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.utils.logger import DefaultLogger
from app.api.routes import router as auth_router
from app.db.database import engine
from app.db.schema import Base
import uvicorn

logger = DefaultLogger("AuthService").get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables declared successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    # App running
    yield


app = FastAPI(lifespan=lifespan, title="AuthService", openapi_url="/openapi.json")

app.include_router(auth_router, prefix="/api")

if __name__ == "__main__":
    logger.info("Starting Auth Service")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)