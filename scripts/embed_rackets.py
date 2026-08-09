from app.core.database import SessionLocal
from app.models.racket import Racket
from app.services.embedding_service import EmbeddingService


def main():
    db = SessionLocal()
    embedding_service = EmbeddingService()

    try:
        rackets = (
            db.query(Racket)
            .filter(
                Racket.is_active.is_(True),
                Racket.embedding.is_(None),
            )
            .all()
        )

        total = len(rackets)

        print(f"Found {total} rackets to process.")

        for index, racket in enumerate(rackets, start=1):

            print(
                f"[{index}/{total}] "
                f"Processing: {racket.brand} {racket.model}"
            )

            embedding_text = racket.build_embedding_text()

            vector = embedding_service.embed_document(
                embedding_text
            )

            # racket.embedding_text = embedding_text
            # racket.embedding_model = embedding_service.MODEL
            racket.embedding = vector

        db.commit()

        print("All racket embeddings generated successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()