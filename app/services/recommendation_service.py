from app.exceptions.recommendation import (
    InvalidRacketCandidateError,
    NoRacketCandidateError,
)
from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import (
    RacketCandidate,
    RacketFinalRecommendation,
    RacketRecommendationRequest,
)
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.recommendation_prompt import (
    RecommendationPromptBuilder,
)


LEVEL_LABELS = {
    "beginner": "初學者",
    "intermediate": "中階",
    "advanced": "進階",
}

PLAYING_STYLE_LABELS = {
    "offensive": "進攻型",
    "defensive": "防守型",
    "all_round": "全能型",
}


class RecommendationService:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        racket_repository: RacketRepository,
        gemini_service: GeminiService,
        prompt_builder: RecommendationPromptBuilder,
    ):
        self.embedding_service = embedding_service
        self.racket_repository = racket_repository
        self.gemini_service = gemini_service
        self.prompt_builder = prompt_builder

    def build_query_text(
        self,
        request: RacketRecommendationRequest,
    ) -> str:
        level = LEVEL_LABELS.get(
            request.level,
            request.level,
        )

        playing_style = PLAYING_STYLE_LABELS.get(
            request.playing_style,
            request.playing_style,
        )

        brand = request.brand or "無品牌偏好"

        return (
            f"使用者程度：{level}\n"
            f"打法：{playing_style}\n"
            f"品牌：{brand}\n"
            f"預算：{request.budget} 元"
        )

    def create_query_embedding(
        self,
        request: RacketRecommendationRequest,
    ) -> list[float]:
        query_text = self.build_query_text(request)

        return self.embedding_service.embed_query(
            query_text
        )

    def search_rackets(
        self,
        request: RacketRecommendationRequest,
        limit: int = 5,
    ):
        query_embedding = self.create_query_embedding(
            request
        )

        return self.racket_repository.find_similar(
            query_embedding=query_embedding,
            budget=request.budget,
            brand=request.brand,
            limit=limit,
        )

    def search_racket_candidates(
        self,
        request: RacketRecommendationRequest,
        limit: int = 5,
    ) -> list[RacketCandidate]:
        results = self.search_rackets(
            request=request,
            limit=limit,
        )

        return [
            RacketCandidate(
                id=racket.id,
                brand=racket.brand,
                model=racket.model,
                price=racket.price,
                distance=distance,
                similarity=1 - distance,
            )
            for racket, distance in results
        ]

    def recommend_racket(
        self,
        request: RacketRecommendationRequest,
        limit: int = 5,
    ) -> tuple[RacketCandidate, str]:
        candidates = self.search_racket_candidates(
            request=request,
            limit=limit,
        )

        if not candidates:
            raise NoRacketCandidateError(
                budget=float(request.budget)
            )

        prompt = self.prompt_builder.build_racket_prompt(
            request=request,
            candidates=candidates,
        )

        result = self.gemini_service.generate_structured(
            prompt=prompt,
            response_schema=RacketFinalRecommendation,
        )

        candidate_map = {
            candidate.id: candidate
            for candidate in candidates
        }

        selected_candidate = candidate_map.get(
            result.recommended_racket_id
        )

        if selected_candidate is None:
            raise InvalidRacketCandidateError(
                racket_id=result.recommended_racket_id
            )

        return selected_candidate, result.reason