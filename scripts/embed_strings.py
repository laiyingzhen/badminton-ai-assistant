from app.core.database import SessionLocal
from app.models.string import StringProduct
from app.services.embedding_service import EmbeddingService


def main():

    db = SessionLocal()
    embedding_service = EmbeddingService()

    try:

        strings = (
            db.query(StringProduct)
            .filter(
                StringProduct.is_active.is_(True),
                StringProduct.embedding.is_(None),
            )
            .all()
        )

        print(f"Found {len(strings)} strings.")

        for string in strings:

            text = string.build_embedding_text()

            print(
                f"Embedding: "
                f"{string.brand} {string.model}"
            )

            vector = embedding_service.embed_document(
                text
            )

            string.embedding = vector

        db.commit()

        print("Embedding completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()