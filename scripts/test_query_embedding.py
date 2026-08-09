from app.schemas.recommendation import RacketRecommendationRequest
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_service import RecommendationService
from dotenv import load_dotenv
load_dotenv()

def main():

    request = RacketRecommendationRequest(
        level="intermediate",
        playing_style="offensive",
        budget=5000,
    )

    embedding_service = EmbeddingService()

    recommendation_service = RecommendationService(
        embedding_service=embedding_service,
    )

    query_text = recommendation_service.build_query_text(
        request
    )

    print("Query Text:")
    print("--------------------")
    print(query_text)

    print("\nGenerating query embedding...")

    query_embedding = (
        recommendation_service.create_query_embedding(
            request
        )
    )

    print(
        f"\nVector dimension: "
        f"{len(query_embedding)}"
    )

    print("\nFirst 10 values:")
    print(query_embedding[:10])


if __name__ == "__main__":
    main()