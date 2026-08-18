from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_gemini_service,
    get_racket_chat_service,
)
from app.main import app
from app.schemas.chat import (
    ChatResponse,
    ExtractedRacketCriteria,
)


client = TestClient(app)


def clear_dependency_overrides():
    app.dependency_overrides.clear()


def create_chat_response():
    return ChatResponse(
        session_id=uuid4(),
        status="collecting",
        message="請問您的預算是多少？",
        criteria=ExtractedRacketCriteria(
            playing_style="offensive",
        ),
        missing_fields=[
            "level",
            "budget",
        ],
        recommendation=None,
    )


def test_voice_chat_success():
    mock_gemini_service = Mock()
    mock_chat_service = Mock()

    mock_gemini_service.transcribe_audio.return_value = (
        "我喜歡進攻型球拍"
    )
    mock_chat_service.chat.return_value = (
        create_chat_response()
    )

    app.dependency_overrides[
        get_gemini_service
    ] = lambda: mock_gemini_service

    app.dependency_overrides[
        get_racket_chat_service
    ] = lambda: mock_chat_service

    try:
        response = client.post(
            "/api/v1/recommendations/rackets/chat/voice",
            files={
                "audio": (
                    "message.webm",
                    b"fake audio content",
                    "audio/webm",
                ),
            },
        )

        assert response.status_code == 200

        body = response.json()

        assert body["transcript"] == (
            "我喜歡進攻型球拍"
        )
        assert body["status"] == "collecting"
        assert body["message"] == "請問您的預算是多少？"

        mock_gemini_service.transcribe_audio.assert_called_once_with(
            audio_data=b"fake audio content",
            mime_type="audio/webm",
        )

        mock_chat_service.chat.assert_called_once_with(
            message="我喜歡進攻型球拍",
            session_id=None,
            candidate_limit=3,
        )

    finally:
        clear_dependency_overrides()


def test_voice_chat_with_existing_session():
    mock_gemini_service = Mock()
    mock_chat_service = Mock()

    session_id = uuid4()
    chat_response = create_chat_response()
    chat_response.session_id = session_id

    mock_gemini_service.transcribe_audio.return_value = (
        "預算五千元"
    )
    mock_chat_service.chat.return_value = chat_response

    app.dependency_overrides[
        get_gemini_service
    ] = lambda: mock_gemini_service

    app.dependency_overrides[
        get_racket_chat_service
    ] = lambda: mock_chat_service

    try:
        response = client.post(
            "/api/v1/recommendations/rackets/chat/voice",
            data={
                "session_id": str(session_id),
            },
            files={
                "audio": (
                    "message.wav",
                    b"fake wav content",
                    "audio/wav",
                ),
            },
        )

        assert response.status_code == 200

        mock_chat_service.chat.assert_called_once_with(
            message="預算五千元",
            session_id=session_id,
            candidate_limit=3,
        )

    finally:
        clear_dependency_overrides()


def test_voice_chat_rejects_unsupported_file_type():
    mock_gemini_service = Mock()
    mock_chat_service = Mock()

    app.dependency_overrides[
        get_gemini_service
    ] = lambda: mock_gemini_service

    app.dependency_overrides[
        get_racket_chat_service
    ] = lambda: mock_chat_service

    try:
        response = client.post(
            "/api/v1/recommendations/rackets/chat/voice",
            files={
                "audio": (
                    "document.txt",
                    b"not audio",
                    "text/plain",
                ),
            },
        )

        assert response.status_code == 415

        body = response.json()

        assert body["detail"]["code"] == (
            "UNSUPPORTED_AUDIO_TYPE"
        )

        mock_gemini_service.transcribe_audio.assert_not_called()
        mock_chat_service.chat.assert_not_called()

    finally:
        clear_dependency_overrides()


def test_voice_chat_rejects_empty_audio():
    mock_gemini_service = Mock()
    mock_chat_service = Mock()

    app.dependency_overrides[
        get_gemini_service
    ] = lambda: mock_gemini_service

    app.dependency_overrides[
        get_racket_chat_service
    ] = lambda: mock_chat_service

    try:
        response = client.post(
            "/api/v1/recommendations/rackets/chat/voice",
            files={
                "audio": (
                    "empty.webm",
                    b"",
                    "audio/webm",
                ),
            },
        )

        assert response.status_code == 400

        body = response.json()

        assert body["detail"]["code"] == (
            "EMPTY_AUDIO_FILE"
        )

        mock_gemini_service.transcribe_audio.assert_not_called()
        mock_chat_service.chat.assert_not_called()

    finally:
        clear_dependency_overrides()


def test_voice_chat_rejects_oversized_audio():
    mock_gemini_service = Mock()
    mock_chat_service = Mock()

    app.dependency_overrides[
        get_gemini_service
    ] = lambda: mock_gemini_service

    app.dependency_overrides[
        get_racket_chat_service
    ] = lambda: mock_chat_service

    try:
        response = client.post(
            "/api/v1/recommendations/rackets/chat/voice",
            files={
                "audio": (
                    "large.webm",
                    b"x" * (10 * 1024 * 1024 + 1),
                    "audio/webm",
                ),
            },
        )

        assert response.status_code == 413

        body = response.json()

        assert body["detail"]["code"] == (
            "AUDIO_FILE_TOO_LARGE"
        )

        mock_gemini_service.transcribe_audio.assert_not_called()
        mock_chat_service.chat.assert_not_called()

    finally:
        clear_dependency_overrides()