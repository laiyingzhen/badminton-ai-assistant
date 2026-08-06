import os

from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
from pydantic import BaseModel, ValidationError

class GeminiService:
    def __init__(self):
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

        if not project_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable is not set."
            )

        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            http_options=HttpOptions(api_version="v1"),
        )

        self.model = "gemini-2.5-flash"

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel],
    ) -> BaseModel:

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
            raise RuntimeError("Gemini returned an empty response.")

        try:
            return response_schema.model_validate_json(
                response.text
            )
        except ValidationError as exc:
            raise RuntimeError(
                "Gemini returned an invalid response format."
            ) from exc