from sqlalchemy.orm import Session

from app.prompts.racket_recommendation import (
    build_racket_recommendation_prompt,
)
from app.schemas.recommendation import (
    RacketRecommendationRequest,
    RacketRecommendationResponse,
)
from app.services.gemini_service import GeminiService
from app.repositories.racket_repository import RacketRepository

class RecommendationService:

    def __init__(
        self,
        gemini_service: GeminiService,
        racket_repository: RacketRepository,
    ):
        self.gemini_service = gemini_service
        self.racket_repository = racket_repository

    def recommend_rackets(
        self,
        request: RacketRecommendationRequest,
    ) -> RacketRecommendationResponse:

        rackets = self.racket_repository.find_by_budget(
            request.budget
        )

        if not rackets:
            raise ValueError(
                "No rackets found within the user's budget."
            )

        racket_context = "\n".join(
            [
                (
                    f"- {racket.brand} {racket.model}, "
                    f"價格：NT$ {racket.price}, "
                    f"重量：{racket.weight}, "
                    f"平衡：{racket.balance}, "
                    f"硬度：{racket.flexibility}, "
                    f"適合程度：{racket.suitable_level}, "
                    f"適合打法：{racket.playing_style}, "
                    f"描述：{racket.description}"
                )
                for racket in rackets
            ]
        )

        prompt = build_racket_recommendation_prompt(
            level=request.level.value,
            playing_style=request.playing_style.value,
            budget=request.budget,
            racket_context=racket_context,
        )

        return self.gemini_service.generate_structured(
            prompt=prompt,
            response_schema=RacketRecommendationResponse,
        )
