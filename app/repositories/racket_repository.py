from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.racket import Racket


class RacketRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_by_budget(
        self,
        budget: int,
    ) -> list[Racket]:

        statement = (
            select(Racket)
            .where(
                Racket.price <= budget,
                Racket.is_active.is_(True),
            )
            .order_by(Racket.price.desc())
        )

        return list(
            self.db.scalars(statement).all()
        )