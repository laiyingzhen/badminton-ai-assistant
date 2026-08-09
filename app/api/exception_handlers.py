from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.recommendation import (
    DatabaseServiceError,
    GeminiServiceError,
    InvalidRacketCandidateError,
    NoRacketCandidateError,
)


def no_racket_candidate_handler(
    request: Request,
    exc: NoRacketCandidateError,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NO_RACKET_CANDIDATE",
                "message": str(exc),
            }
        },
    )


def invalid_racket_candidate_handler(
    request: Request,
    exc: InvalidRacketCandidateError,
):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INVALID_RACKET_CANDIDATE",
                "message": str(exc),
            }
        },
    )


def gemini_service_error_handler(
    request: Request,
    exc: GeminiServiceError,
):
    return JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "GEMINI_SERVICE_ERROR",
                "message": str(exc),
            }
        },
    )


def database_service_error_handler(
    request: Request,
    exc: DatabaseServiceError,
):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "DATABASE_SERVICE_ERROR",
                "message": str(exc),
            }
        },
    )


def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    details = []

    for error in exc.errors():
        location = error.get("loc", [])
        field = ".".join(
            str(item)
            for item in location
            if item != "body"
        )

        details.append(
            {
                "field": field,
                "message": error.get("msg", "Invalid value."),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": details,
            }
        },
    )
