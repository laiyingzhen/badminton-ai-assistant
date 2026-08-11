from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import (
    RacketCandidate,
    StringCandidate,
    ShoeCandidate,
    RacketFinalRecommendation,
    RacketRecommendationRequest,
    EquipmentFinalRecommendation,
    EquipmentRecommendationResponse,
)
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.recommendation_prompt import (
    RecommendationPromptBuilder,    
)
from app.exceptions.recommendation import (
    InvalidRacketCandidateError,
    NoRacketCandidateError,
    NoEquipmentCandidateError,
    InvalidEquipmentCandidateError,
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
        embedding_service,
        racket_repository,
        string_repository,
        shoe_repository,
        gemini_service,
        prompt_builder,
    ):
        self.embedding_service = embedding_service
        self.racket_repository = racket_repository
        self.string_repository = string_repository
        self.shoe_repository = shoe_repository
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

        return (
            f"羽球程度：{level}\n"
            f"打法：{playing_style}\n"
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

    def search_equipment_candidates(
        self,
        request: RacketRecommendationRequest,
        limit: int = 3,
    ):

        query_embedding = self.create_query_embedding(
            request
        )

        racket_results = (
            self.racket_repository.find_similar(
                query_embedding=query_embedding,
                budget=request.budget,
                limit=limit,
            )
        )

        string_results = (
            self.string_repository.find_similar(
                query_embedding=query_embedding,
                budget=request.budget,
                limit=limit,
            )
        )

        shoe_results = (
            self.shoe_repository.find_similar(
                query_embedding=query_embedding,
                budget=request.budget,
                limit=limit,
            )
        )

        return (
            self._to_racket_candidates(racket_results),
            self._to_string_candidates(string_results),
            self._to_shoe_candidates(shoe_results),
        )

    def _to_racket_candidates(
        self,
        results,
    ) -> list[RacketCandidate]:

        return [
            RacketCandidate(
                id=item.id,
                brand=item.brand,
                model=item.model,
                price=item.price,
                distance=float(distance),
                similarity=1 - float(distance),
            )
            for item, distance in results
        ]        

    def _to_string_candidates(
        self,
        results,
    ) -> list[StringCandidate]:

        return [
            StringCandidate(
                id=item.id,
                brand=item.brand,
                model=item.model,
                price=item.price,
                distance=float(distance),
                similarity=1 - float(distance),
            )
            for item, distance in results
        ]

    def _to_shoe_candidates(
        self,
        results,
    ) -> list[ShoeCandidate]:

        return [
            ShoeCandidate(
                id=item.id,
                brand=item.brand,
                model=item.model,
                price=item.price,
                distance=float(distance),
                similarity=1 - float(distance),
            )
            for item, distance in results
        ]

    def recommend_equipment(
        self,
        request: RacketRecommendationRequest,
        limit: int = 3,
    ) -> EquipmentRecommendationResponse:

        (
            rackets,
            strings,
            shoes,
        ) = self.search_equipment_candidates(
            request=request,
            limit=limit,
        )

        if not rackets:
            raise NoRacketCandidateError(
                budget=float(request.budget)
            )

        if not strings:
            raise NoEquipmentCandidateError(
                equipment_type="string",
                budget=float(request.budget),
            )

        if not shoes:
            raise NoEquipmentCandidateError(
                equipment_type="shoe",
                budget=float(request.budget),
            )

        prompt = self.prompt_builder.build_equipment_prompt(
            request=request,
            rackets=rackets,
            strings=strings,
            shoes=shoes,
        )

        result = self.gemini_service.generate_structured(
            prompt=prompt,
            response_schema=EquipmentFinalRecommendation,
        )

        racket_map = {
            item.id: item
            for item in rackets
        }

        string_map = {
            item.id: item
            for item in strings
        }

        shoe_map = {
            item.id: item
            for item in shoes
        }

        racket = racket_map.get(
            result.recommended_racket_id
        )

        string = string_map.get(
            result.recommended_string_id
        )

        shoe = shoe_map.get(
            result.recommended_shoe_id
        )

        if not racket:
            raise InvalidRacketCandidateError(
                racket_id=result.recommended_racket_id
            )

        if not string:
            raise InvalidEquipmentCandidateError(
                equipment_type="string",
                equipment_id=result.recommended_string_id,
            )

        if not shoe:
            raise InvalidEquipmentCandidateError(
                equipment_type="shoe",
                equipment_id=result.recommended_shoe_id,
            )

        return EquipmentRecommendationResponse(
            racket=racket,
            string=string,
            shoe=shoe,
            reason=result.reason,
        )        