import logging

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.recommendation import DatabaseServiceError
from app.models.string import String


logger = logging.getLogger(__name__)


class StringRepository:

    def __init__(self, db):
        self.db = db

    def find_similar(
        self,
        query_embedding: list[float],
        budget,
        limit: int,
    ):

        try:
            return (
                self.db.query(
                    String,
                    String.embedding.cosine_distance(
                        query_embedding
                    ).label("distance"),
                )
                .filter(
                    String.price <= budget,
                    String.embedding.isnot(None),
                )
                .order_by(
                    String.embedding.cosine_distance(
                        query_embedding
                    )
                )
                .limit(limit)
                .all()
            )

        except SQLAlchemyError as exc:

            logger.exception(
                "Database query failed while searching strings."
            )

            raise DatabaseServiceError(
                "Unable to search string database."
            ) from exc