from __future__ import annotations
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("setify")
logger.info("Logging initialized.")


def create_app() -> FastAPI:
    settings = get_settings()
    logger.info("Creating FastAPI app...")

    app = FastAPI(title="Setify API")

    # Combine localhost origins with environment-configured origins
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    if settings.api_allowed_origins:
        allowed_origins.extend(settings.api_allowed_origins)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.app.api.routes import router
    logger.info("Including API router...")
    app.include_router(router)

    return app


API = create_app()
logger.info("Application created successfully.")
