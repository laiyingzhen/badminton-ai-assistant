from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_racket_service
from app.schemas.racket import (
    RacketBrand,
    RacketPlayingStyle,
    RacketQueryResponse,
)
from app.schemas.recommendation import ErrorResponse
from app.services.racket_service import RacketService


router = APIRouter(
    prefix="/rackets",
    tags=["Rackets"],
)


@router.get(
    "",
    response_model=list[RacketQueryResponse],
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Request validation failed.",
        },
        503: {
            "model": ErrorResponse,
            "description": "Database service failed.",
        },
    },
)
def query_rackets(
    budget: Annotated[
        Decimal,
        Query(
            gt=0,
            description="最高預算，必須大於 0。",
        ),
    ],
    playing_style: Annotated[
        RacketPlayingStyle,
        Query(
            description=(
                "打法：offensive、defensive 或 all_round。"
            ),
        ),
    ],
    service: Annotated[
        RacketService,
        Depends(get_racket_service),
    ],
    brand: Annotated[
        RacketBrand | None,
        Query(
            description=(
                "品牌：YONEX、VICTOR、LI-NING 或 JNICE。"
            ),
        ),
    ] = None,
) -> list[RacketQueryResponse]:
    rackets = service.query_rackets(
        budget=budget,
        playing_style=playing_style,
        brand=brand,
    )

    return [
        RacketQueryResponse.model_validate(racket)
        for racket in rackets
    ]