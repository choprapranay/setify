from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .app.core.config import get_settings
from .app.interfaces.api.routes import router

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Setify API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins="http://localhost:5173/",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app

API = create_app()
