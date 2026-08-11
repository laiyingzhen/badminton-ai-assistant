import logging

from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.recommendation import DatabaseServiceError
from app.models.shoe import Shoe


logger = logging.getLogger(__name__)


class ShoeRepository:

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
                    Shoe,
                    Shoe.embedding.cosine_distance(
                        query_embedding
                    ).label("distance"),
                )
                .filter(
                    Shoe.price <= budget,
                    Shoe.embedding.isnot(None),
                )
                .order_by(
                    Shoe.embedding.cosine_distance(
                        query_embedding
                    )
                )
                .limit(limit)
                .all()
            )

        except SQLAlchemyError as exc:

            logger.exception(
                "Database query failed while searching shoes."
            )

            raise DatabaseServiceError(
                "Unable to search shoe database."
            ) from exc