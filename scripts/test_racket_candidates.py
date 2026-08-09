from app.core.database import SessionLocal
from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import RacketRecommendationRequest
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_service import RecommendationService


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

        recommendation_service = RecommendationService(
            embedding_service=embedding_service,
            racket_repository=racket_repository,
        )

        candidates = (
            recommendation_service.search_racket_candidates(
                request=request,
                limit=3,
            )
        )

        print("\n## Racket Candidates")

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            print(
                f"\n{index}. "
                f"{candidate.brand} "
                f"{candidate.model}"
            )

            print(
                f"   ID: {candidate.id}"
            )

            print(
                f"   Price: {candidate.price}"
            )

            print(
                f"   Distance: "
                f"{candidate.distance:.6f}"
            )

            print(
                f"   Similarity: "
                f"{candidate.similarity:.6f}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()