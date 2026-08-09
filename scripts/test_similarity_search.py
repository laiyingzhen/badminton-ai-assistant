from app.core.database import SessionLocal
from app.repositories.racket_repository import RacketRepository
from app.services.embedding_service import EmbeddingService


def main():
    db = SessionLocal()

    try:
        embedding_service = EmbeddingService()
        repository = RacketRepository(db)

        query = """
        我是一名中階羽球球員，
        主要打法是進攻型，
        喜歡在後場殺球，
        希望球拍具有較好的攻擊力。
        """

        print("Generating query embedding...")

        query_embedding = embedding_service.embed_query(
            query
        )

        print(
            f"Query vector dimension: "
            f"{len(query_embedding)}"
        )

        print("\nSearching similar rackets...\n")

        results = repository.find_similar(
            query_embedding=query_embedding,
            limit=5,
        )

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