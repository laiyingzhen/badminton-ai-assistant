import logging

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    HttpOptions,
    Part,
)
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.exceptions.recommendation import GeminiServiceError


logger = logging.getLogger(__name__)


class GeminiService:

    def __init__(self):
        settings = get_settings()

        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            http_options=HttpOptions(
                api_version="v1",
            ),
        )

        self.model = settings.gemini_model

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:
        try:
            logger.info(
                "Calling Gemini model: %s",
                self.model,
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

            if not response.text:
                raise GeminiServiceError(
                    "Gemini returned an empty response."
                )

            try:
                return response_schema.model_validate_json(
                    response.text
                )

            except ValidationError as exc:
                logger.exception(
                    "Gemini returned invalid structured response."
                )

                raise GeminiServiceError(
                    "Gemini returned an invalid response format."
                ) from exc

        except GeminiServiceError:
            raise

        except Exception as exc:
            logger.exception(
                "Gemini API call failed. "
                "model=%s schema=%s error=%r",
                self.model,
                response_schema.__name__,
                exc,
            )

            raise GeminiServiceError(
                "Gemini recommendation service is unavailable. "
                f"Cause: {type(exc).__name__}: {exc}"
            ) from exc

    def transcribe_audio(
        self,
        audio_data: bytes,
        mime_type: str,
    ) -> str:
        try:
            logger.info(
                "Calling Gemini for audio transcription: "
                "model=%s mime_type=%s bytes=%d",
                self.model,
                mime_type,
                len(audio_data),
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    Part.from_bytes(
                        data=audio_data,
                        mime_type=mime_type,
                    ),
                    (
                        "請將這段音訊完整轉錄成文字。"
                        "保留說話者原本使用的語言；"
                        "若內容是中文，請使用繁體中文。"
                        "只輸出逐字稿，不要加入說明、標題、"
                        "Markdown 或額外評論。"
                    ),
                ],
                config=GenerateContentConfig(
                    temperature=0,
                ),
            )

            transcript = (
                response.text.strip()
                if response.text
                else ""
            )

            if not transcript:
                raise GeminiServiceError(
                    "Gemini could not recognize speech "
                    "from the uploaded audio."
                )

            return transcript

        except GeminiServiceError:
            raise

        except Exception as exc:
            logger.exception(
                "Gemini audio transcription failed. "
                "model=%s mime_type=%s error=%r",
                self.model,
                mime_type,
                exc,
            )

            raise GeminiServiceError(
                "Gemini speech transcription service "
                "is unavailable. "
                f"Cause: {type(exc).__name__}: {exc}"
            ) from exc