from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


RacketLevel = Literal[
    "beginner",
    "intermediate",
    "advanced",
]

RacketPlayingStyle = Literal[
    "offensive",
    "defensive",
    "all_round",
]

RacketBrand = Literal[
    "YONEX",
    "VICTOR",
    "LI-NING",
    "JNICE",
]


class RacketRecommendationRequest(BaseModel):
    level: RacketLevel = Field(
        description=(
            "使用者能力：beginner / intermediate / advanced"
        )
    )

    playing_style: RacketPlayingStyle = Field(
        description=(
            "偏好打法：offensive / defensive / all_round"
        )
    )

    budget: Decimal = Field(
        gt=0,
        description="預算，必須大於 0。",
    )

    brand: RacketBrand | None = Field(
        default=None,
        description=(
            "偏好品牌：YONEX / VICTOR / LI-NING / JNICE"
        ),
    )


class RacketCandidate(BaseModel):
    id: int
    brand: str
    model: str
    price: Decimal
    distance: float | None = None
    similarity: float | None = None

    def to_prompt_dict(self) -> dict:
        return {
            "id": self.id,
            "brand": self.brand,
            "model": self.model,
            "price": float(self.price),
            "similarity": (
                round(self.similarity, 4)
                if self.similarity is not None
                else None
            ),
        }


class RacketFinalRecommendation(BaseModel):
    recommended_racket_id: int = Field(
        description=(
            "推薦球拍的 ID，必須是候選球拍 ID 之一。"
        )
    )

    reason: str = Field(
        description="推薦這支球拍的原因。",
    )


class RacketRecommendationResponse(BaseModel):
    racket: RacketCandidate
    reason: str


class ErrorResponse(BaseModel):
    code: str
    message: str