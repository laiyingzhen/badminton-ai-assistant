from enum import Enum

from pydantic import BaseModel, Field


class PlayerLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlayingStyle(str, Enum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    ALL_ROUND = "all_round"


class RacketRecommendationRequest(BaseModel):
    level: PlayerLevel = Field(
        ...,
        description="使用者程度"
    )

    playing_style: PlayingStyle = Field(
        ...,
        description="使用者打法"
    )

    budget: int = Field(
        ...,
        gt=0,
        description="預算，單位：新台幣"
    )


class RacketRecommendation(BaseModel):
    name: str = Field(
        ...,
        description="羽球拍名稱"
    )

    reason: str = Field(
        ...,
        description="推薦這把球拍的原因"
    )


class RacketRecommendationResponse(BaseModel):
    recommendations: list[RacketRecommendation] = Field(
        ...,
        description="推薦的羽球拍清單"
    )