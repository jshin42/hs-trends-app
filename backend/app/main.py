from fastapi import FastAPI
from app.api.api import router as api_router
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up {settings.PROJECT_NAME}")
    logger.info(f"Application is running with the following settings:")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    logger.info(f"API prefix: /api")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.PROJECT_NAME} with Uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000)
