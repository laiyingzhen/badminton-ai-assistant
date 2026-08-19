from decimal import Decimal

from app.models.racket import Racket
from app.repositories.racket_repository import RacketRepository


class RacketService:

    def __init__(
        self,
        racket_repository: RacketRepository,
    ):
        self.racket_repository = racket_repository

    def query_rackets(
        self,
        budget: Decimal,
        playing_style: str,
        page: int,
        page_size: int,
        brand: str | None = None,
    ) -> tuple[list[Racket], int]:
        return self.racket_repository.find_by_query_conditions(
            budget=budget,
            playing_style=playing_style,
            brand=brand,
            page=page,
            page_size=page_size,
        )