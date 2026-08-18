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


BADMINTON_TRANSCRIPTION_PROMPT = """
你是專門處理羽球器材推薦對話的繁體中文語音辨識員。

請將音訊完整轉錄成文字，並依照羽球語境校正發音相近的誤辨詞。
優先考慮羽球常用詞彙，例如：羽球、球拍、拍框、拍桿、拍線、磅數、
殺球、重殺、暴力殺、扣殺、吊球、切球、挑球、平抽擋、網前、後場、
進攻、防守、速度、控球、頭重、頭輕、平衡點、中桿、硬度、預算、
初階、中階、進階，以及 Yonex、Victor、Li-Ning 等品牌名稱。

校正原則：
1. 若同音或近音內容在羽球語境下有明確詞彙，請使用羽球用字。
   例如：「沙丘」應辨識為「殺球」，「暴力沙」應辨識為「暴力殺」。
2. 保留說話者原意、語氣、數字、品牌與型號，不要摘要或自行補充需求。
3. 無法由上下文確認的內容，保留最接近原始發音的文字，不要臆測。
4. 保留說話者原本使用的語言；中文一律使用繁體中文。
5. 只輸出校正後的逐字稿，不要加入標題、說明、Markdown 或引號。
""".strip()


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
                    BADMINTON_TRANSCRIPTION_PROMPT,
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
