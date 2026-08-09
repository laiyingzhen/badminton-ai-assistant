import logging

from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
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
                api_version="v1"
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
                "Gemini API call failed."
            )

            raise GeminiServiceError(
                "Gemini recommendation service is unavailable."
            ) from exc