from decimal import Decimal

from pydantic import BaseModel, Field


class RacketRecommendationRequest(BaseModel):
    level: str = Field(
        description="使用者羽球程度，例如 beginner / intermediate / advanced"
    )

    playing_style: str = Field(
        description="使用者打法，例如 offensive / defensive / all_round"
    )

    budget: Decimal = Field(
        gt=0,
        description="預算，單位為新台幣"
    )


class RacketCandidate(BaseModel):
    id: int
    brand: str
    model: str
    price: Decimal
    distance: float
    similarity: float

    def to_prompt_dict(self) -> dict:
        return {
            "brand": self.brand,
            "model": self.model,
            "price": float(self.price),
            "similarity": round(
                self.similarity,
                4,
            ),
        }

class StringCandidate(BaseModel):
    id: int
    brand: str
    model: str
    price: Decimal
    distance: float
    similarity: float


class ShoeCandidate(BaseModel):
    id: int
    brand: str
    model: str
    price: Decimal
    distance: float
    similarity: float


class EquipmentRecommendationResponse(BaseModel):
    racket: RacketCandidate
    string: StringCandidate
    shoe: ShoeCandidate
    reason: str

class RacketFinalRecommendation(BaseModel):
    recommended_racket_id: int = Field(
        description=(
            "The ID of the recommended racket. "
            "Must be one of the candidate racket IDs."
        )
    )

    reason: str = Field(
        description="Reason why this racket is the best choice for the user."
    )


class RacketRecommendationResponse(BaseModel):
    racket: RacketCandidate = Field(
        description="AI 最終推薦的球拍"
    )

    reason: str = Field(
        description="AI 推薦理由"
    )

class ErrorResponse(BaseModel):
    code: str
    message: str

class EquipmentFinalRecommendation(BaseModel):

    recommended_racket_id: int

    recommended_string_id: int

    recommended_shoe_id: int

    reason: str

