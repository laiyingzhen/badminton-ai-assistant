from app.core.database import SessionLocal
from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import (
    RacketFinalRecommendation,
    RacketRecommendationRequest,
)
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_prompt import (
    RecommendationPromptBuilder,
)
from app.services.recommendation_service import (
    RecommendationService,
)


class FakeGeminiService:

    def generate_structured(
        self,
        prompt: str,
        response_schema: type,
    ):
        # 故意回傳不存在的 Racket ID
        return RacketFinalRecommendation(
            recommended_racket_id=99999,
            reason="這是測試用的錯誤推薦。",
        )


def main():

    db = SessionLocal()

    try:
        request = RacketRecommendationRequest(
            level="intermediate",
            playing_style="offensive",
            budget=5000,
        )

        embedding_service = EmbeddingService()

        racket_repository = RacketRepository(db)

        fake_gemini_service = FakeGeminiService()

        prompt_builder = RecommendationPromptBuilder()

        recommendation_service = RecommendationService(
            embedding_service=embedding_service,
            racket_repository=racket_repository,
            gemini_service=fake_gemini_service,
            prompt_builder=prompt_builder,
        )

        recommendation_service.recommend_racket(
            request=request,
            limit=3,
        )

    except RuntimeError as exc:
        print("\nExpected error:")
        print(exc)

    finally:
        db.close()


if __name__ == "__main__":
    main()