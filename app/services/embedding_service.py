import os

from google import genai
from google.genai.types import EmbedContentConfig, HttpOptions


class EmbeddingService:

    MODEL = "gemini-embedding-001"
    OUTPUT_DIMENSIONALITY = 768

    def __init__(self):
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv(
            "GOOGLE_CLOUD_LOCATION",
            "global",
        )

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

    def embed_document(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=text,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.OUTPUT_DIMENSIONALITY,
            ),
        )

        if not response.embeddings:
            raise RuntimeError(
                "Embedding API returned an empty response."
            )

        return response.embeddings[0].values

    def embed_query(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=self.MODEL,
            contents=text,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.OUTPUT_DIMENSIONALITY,
            ),
        )

        if not response.embeddings:
            raise RuntimeError(
                "Embedding API returned an empty response."
            )

        return response.embeddings[0].values