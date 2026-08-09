from app.core.database import SessionLocal
from app.repositories.racket_repository import RacketRepository
from app.schemas.recommendation import RacketRecommendationRequest
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_service import RecommendationService
from dotenv import load_dotenv
load_dotenv()

def main():

    db = SessionLocal()

    try:
        request = RacketRecommendationRequest(
            level="intermediate",
            playing_style="offensive",
            budget=5000,
        )
        # request = RacketRecommendationRequest(
        #     level="intermediate",
        #     playing_style="offensive",
        #     budget=4000,
        # )        

        embedding_service = EmbeddingService()

        racket_repository = RacketRepository(db)

        recommendation_service = RecommendationService(
            embedding_service=embedding_service,
            racket_repository=racket_repository,
        )

        print("User Request:")
        print("--------------------")
        print(f"Level: {request.level}")
        print(f"Playing Style: {request.playing_style}")
        print(f"Budget: {request.budget}")

        print("\nSearching rackets...")

        results = recommendation_service.search_rackets(
            request=request,
            limit=5,
        )

        print("\nRecommendation Candidates:")
        print("--------------------")

        if not results:
            print("No rackets found.")
            return

        for index, (racket, distance) in enumerate(
            results,
            start=1,
        ):
            print(
                f"{index}. "
                f"{racket.brand} {racket.model} "
                f"| Price: {racket.price} "
                f"| Distance: {distance:.6f}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()