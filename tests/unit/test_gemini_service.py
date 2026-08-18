from unittest.mock import Mock, patch

from app.services.gemini_service import (
    BADMINTON_TRANSCRIPTION_PROMPT,
    GeminiService,
)


def create_gemini_service(response_text: str):
    service = object.__new__(GeminiService)
    service.model = "gemini-test-model"
    service.client = Mock()
    service.client.models.generate_content.return_value = Mock(
        text=response_text,
    )
    return service


def test_transcribe_audio_uses_badminton_context_prompt():
    service = create_gemini_service(
        "OK 我很喜歡殺球推薦我一隻暴力殺的球拍"
    )

    audio_part = Mock()

    with patch(
        "app.services.gemini_service.Part.from_bytes",
        return_value=audio_part,
    ) as from_bytes:
        transcript = service.transcribe_audio(
            audio_data=b"fake audio",
            mime_type="audio/webm",
        )

    assert transcript == (
        "OK 我很喜歡殺球推薦我一隻暴力殺的球拍"
    )

    from_bytes.assert_called_once_with(
        data=b"fake audio",
        mime_type="audio/webm",
    )

    call = service.client.models.generate_content.call_args
    contents = call.kwargs["contents"]

    assert contents[0] is audio_part
    assert contents[1] == BADMINTON_TRANSCRIPTION_PROMPT
    assert "羽球器材推薦" in contents[1]
    assert "沙丘" in contents[1]
    assert "殺球" in contents[1]
    assert "暴力沙" in contents[1]
    assert "暴力殺" in contents[1]


def test_transcribe_audio_strips_surrounding_whitespace():
    service = create_gemini_service(
        "  我想找適合殺球的球拍  \n"
    )

    with patch(
        "app.services.gemini_service.Part.from_bytes",
    ):
        transcript = service.transcribe_audio(
            audio_data=b"fake audio",
            mime_type="audio/webm",
        )

    assert transcript == "我想找適合殺球的球拍"
