from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_racket_candidate_limit,
    get_racket_chat_service,
)
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import (
    ChatSessionNotFoundError,
    RacketChatService,
)


router = APIRouter(
    prefix="/recommendations/rackets/chat",
    tags=["Racket recommendation chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat_about_rackets(
    request: ChatRequest,
    service: RacketChatService = Depends(
        get_racket_chat_service
    ),
    candidate_limit: int = Depends(
        get_racket_candidate_limit
    ),
):
    try:
        return service.chat(
            message=request.message,
            session_id=request.session_id,
            candidate_limit=candidate_limit,
        )

    except ChatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CHAT_SESSION_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc


@router.get(
    "/{session_id}/history",
    response_model=ChatHistoryResponse,
)
def get_chat_history(
    session_id: UUID,
    service: RacketChatService = Depends(
        get_racket_chat_service
    ),
):
    try:
        return service.get_history(session_id)

    except ChatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CHAT_SESSION_NOT_FOUND",
                "message": str(exc),
            },
        ) from exc