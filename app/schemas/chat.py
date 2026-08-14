from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.recommendation import (
    RacketBrand,
    RacketCandidate,
    RacketLevel,
    RacketPlayingStyle,
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="使用者輸入的自然語言訊息。",
    )

    session_id: UUID | None = Field(
        default=None,
        description=(
            "對話識別碼。第一次對話不需提供，"
            "之後必須帶回 API 回傳的 session_id。"
        ),
    )


class ExtractedRacketCriteria(BaseModel):
    playing_style: RacketPlayingStyle | None = None
    brand: RacketBrand | None = None
    level: RacketLevel | None = None
    budget: Decimal | None = Field(
        default=None,
        gt=0,
    )


class CriteriaExtractionResult(BaseModel):
    playing_style: RacketPlayingStyle | None = None
    brand: RacketBrand | None = None
    level: RacketLevel | None = None
    budget: Decimal | None = Field(
        default=None,
        gt=0,
    )

    clear_brand: bool = Field(
        default=False,
        description=(
            "使用者明確表示沒有品牌偏好時設為 true。"
        ),
    )


class ChatGuidanceResult(BaseModel):
    message: str = Field(
        description=(
            "根據目前已知條件、缺少條件和候選球拍，"
            "產生的繁體中文回覆。"
        )
    )


class ChatResponse(BaseModel):
    session_id: UUID
    status: Literal[
        "collecting",
        "recommended",
        "no_match",
    ]
    message: str
    criteria: ExtractedRacketCriteria
    missing_fields: list[str]
    recommendation: RacketCandidate | None = None


class ChatMessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: UUID
    criteria: ExtractedRacketCriteria
    messages: list[ChatMessageResponse]