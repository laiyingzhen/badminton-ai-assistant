import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.exception_handlers import (
    database_service_error_handler,
    gemini_service_error_handler,
    invalid_racket_candidate_handler,
    no_racket_candidate_handler,
    validation_error_handler,
)
from app.api.v1 import chat, recommendations
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.exceptions.recommendation import (
    DatabaseServiceError,
    GeminiServiceError,
    InvalidRacketCandidateError,
    NoRacketCandidateError,
)
from fastapi.middleware.cors import CORSMiddleware

setup_logging()

logger = logging.getLogger(__name__)
settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     "http://127.0.0.1:5500",
    #     "http://localhost:5500",
    # ],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,
)

app.add_exception_handler(
    NoRacketCandidateError,
    no_racket_candidate_handler,
)

app.add_exception_handler(
    InvalidRacketCandidateError,
    invalid_racket_candidate_handler,
)

app.add_exception_handler(
    GeminiServiceError,
    gemini_service_error_handler,
)

app.add_exception_handler(
    DatabaseServiceError,
    database_service_error_handler,
)


app.include_router(
    recommendations.router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat.router,
    prefix=settings.api_v1_prefix,
)


@app.get("/health")
def health():
    return {"status": "ok"}


logger.info(
    "Application started: %s",
    settings.app_name,
)