import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions.recommendation import (
    DatabaseServiceError,
)
from app.models.racket import Racket


logger = logging.getLogger(__name__)


class RacketRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_similar(
        self,
        query_embedding: list[float],
        budget: float,
        limit: int,
    ):

        try:

            distance = Racket.embedding.cosine_distance(
                query_embedding
            )

            return (
                self.db.query(
                    Racket,
                    distance.label("distance"),
                )
                .filter(
                    Racket.price <= budget
                )
                .order_by(
                    distance
                )
                .limit(limit)
                .all()
            )

        except SQLAlchemyError as exc:

            logger.exception(
                "Database query failed while searching similar rackets."
            )

            raise DatabaseServiceError(
                "Unable to search racket database."
            ) from exc

