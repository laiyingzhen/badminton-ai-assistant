import logging
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions.recommendation import DatabaseServiceError
from app.models.racket import Racket


logger = logging.getLogger(__name__)


class RacketRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(
        self,
        racket_id: int,
    ) -> Racket | None:
        try:
            return (
                self.db.query(Racket)
                .filter(
                    Racket.id == racket_id,
                    Racket.is_active.is_(True),
                )
                .first()
            )

        except SQLAlchemyError as exc:
            logger.exception(
                "Database query failed while querying racket id %s.",
                racket_id,
            )

            raise DatabaseServiceError(
                "Unable to query racket database."
            ) from exc

    def find_similar(
        self,
        query_embedding: list[float],
        budget: Decimal,
        limit: int,
        brand: str | None = None,
    ):
        try:
            distance = Racket.embedding.cosine_distance(
                query_embedding
            )

            query = (
                self.db.query(
                    Racket,
                    distance.label("distance"),
                )
                .filter(
                    Racket.is_active.is_(True),
                    Racket.embedding.is_not(None),
                    Racket.price <= budget,
                )
            )

            if brand:
                query = query.filter(
                    Racket.brand.ilike(brand)
                )

            return (
                query
                .order_by(distance)
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

    def find_by_partial_conditions(
        self,
        playing_style: str | None,
        level: str | None,
        budget: Decimal | None,
        brand: str | None,
        limit: int = 3,
    ) -> list[Racket]:
        try:
            query = self.db.query(Racket).filter(
                Racket.is_active.is_(True)
            )

            if playing_style:
                query = query.filter(
                    Racket.playing_style == playing_style
                )

            if level:
                query = query.filter(
                    Racket.suitable_level == level
                )

            if budget is not None:
                query = query.filter(
                    Racket.price <= budget
                )

            if brand:
                query = query.filter(
                    Racket.brand.ilike(brand)
                )

            return (
                query
                .order_by(
                    Racket.price.asc(),
                    Racket.id.asc(),
                )
                .limit(limit)
                .all()
            )

        except SQLAlchemyError as exc:
            logger.exception(
                "Database query failed while searching "
                "partial racket conditions."
            )

            raise DatabaseServiceError(
                "Unable to search racket database."
            ) from exc

    def find_by_query_conditions(
        self,
        budget: Decimal,
        playing_style: str,
        page: int,
        page_size: int,
        brand: str | None = None,
    ) -> tuple[list[Racket], int]:
        try:
            query = self.db.query(Racket).filter(
                Racket.is_active.is_(True),
                Racket.price <= budget,
                Racket.playing_style == playing_style,
            )

            if brand is not None:
                query = query.filter(
                    Racket.brand.ilike(brand)
                )

            total_items = query.count()
            offset = (page - 1) * page_size

            rackets = (
                query
                .order_by(
                    Racket.price.asc(),
                    Racket.id.asc(),
                )
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return rackets, total_items

        except SQLAlchemyError as exc:
            logger.exception(
                "Database query failed while querying rackets."
            )

            raise DatabaseServiceError(
                "Unable to query racket database."
            ) from exc