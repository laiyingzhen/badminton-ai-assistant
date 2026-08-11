from app.core.database import SessionLocal
from app.models.shoe import Shoe
from app.services.embedding_service import EmbeddingService


def main():

    db = SessionLocal()
    embedding_service = EmbeddingService()

    try:

        shoes = (
            db.query(Shoe)
            .filter(
                Shoe.is_active.is_(True),
                Shoe.embedding.is_(None),
            )
            .all()
        )

        print(f"Found {len(shoes)} shoes.")

        for shoe in shoes:

            text = shoe.build_embedding_text()

            print(
                f"Embedding: "
                f"{shoe.brand} {shoe.model}"
            )

            vector = embedding_service.embed_document(
                text
            )

            shoe.embedding = vector

        db.commit()

        print("Embedding completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()