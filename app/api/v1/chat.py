from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.api.dependencies import (
    get_gemini_service,
    get_racket_candidate_limit,
    get_racket_chat_service,
    get_voice_audio_max_bytes,
)
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    VoiceChatResponse,
)
from app.services.chat_service import (
    ChatSessionNotFoundError,
    RacketChatService,
)
from app.services.gemini_service import GeminiService


router = APIRouter(
    prefix="/recommendations/rackets/chat",
    tags=["Racket recommendation chat"],
)


SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/m4a",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
    "audio/x-flac",
}


def _raise_chat_session_not_found(
    exc: ChatSessionNotFoundError,
) -> None:
    raise HTTPException(
        status_code=404,
        detail={
            "code": "CHAT_SESSION_NOT_FOUND",
            "message": str(exc),
        },
    ) from exc


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
        _raise_chat_session_not_found(exc)


@router.post(
    "/voice",
    response_model=VoiceChatResponse,
    summary="使用語音進行羽球拍推薦對話",
)
def chat_about_rackets_by_voice(
    audio: UploadFile = File(
        ...,
        description="使用者錄製的語音檔案。",
    ),
    session_id: UUID | None = Form(
        default=None,
        description=(
            "第一次對話不需提供；後續對話請帶入"
            "前一次回傳的 session_id。"
        ),
    ),
    service: RacketChatService = Depends(
        get_racket_chat_service
    ),
    gemini_service: GeminiService = Depends(
        get_gemini_service
    ),
    candidate_limit: int = Depends(
        get_racket_candidate_limit
    ),
    max_audio_bytes: int = Depends(
        get_voice_audio_max_bytes
    ),
):
    mime_type = (
        audio.content_type.split(";", maxsplit=1)[0]
        .strip()
        .lower()
        if audio.content_type
        else ""
    )

    if mime_type not in SUPPORTED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "UNSUPPORTED_AUDIO_TYPE",
                "message": (
                    "Unsupported audio type. "
                    "Supported types include MP3, MP4/M4A, "
                    "WAV, WebM, OGG and FLAC."
                ),
            },
        )

    try:
        audio_data = audio.file.read(
            max_audio_bytes + 1
        )
    finally:
        audio.file.close()

    if not audio_data:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMPTY_AUDIO_FILE",
                "message": "The uploaded audio file is empty.",
            },
        )

    if len(audio_data) > max_audio_bytes:
        max_megabytes = max_audio_bytes / 1024 / 1024

        raise HTTPException(
            status_code=413,
            detail={
                "code": "AUDIO_FILE_TOO_LARGE",
                "message": (
                    "The uploaded audio file exceeds "
                    f"the {max_megabytes:g} MB limit."
                ),
            },
        )

    transcript = gemini_service.transcribe_audio(
        audio_data=audio_data,
        mime_type=mime_type,
    )

    if len(transcript) > 2000:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "TRANSCRIPT_TOO_LONG",
                "message": (
                    "The recognized transcript exceeds "
                    "the 2000 character chat-message limit."
                ),
            },
        )

    try:
        chat_response = service.chat(
            message=transcript,
            session_id=session_id,
            candidate_limit=candidate_limit,
        )

    except ChatSessionNotFoundError as exc:
        _raise_chat_session_not_found(exc)

    return VoiceChatResponse(
        transcript=transcript,
        **chat_response.model_dump(),
    )


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
        _raise_chat_session_not_found(exc)