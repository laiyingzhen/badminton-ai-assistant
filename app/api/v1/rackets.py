from decimal import Decimal
from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_racket_service
from app.schemas.racket import (
    RacketBrand,
    RacketListResponse,
    RacketPaginationResponse,
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
    response_model=RacketListResponse,
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
            description="預算，必須大於 0。",
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
    page: Annotated[
        int,
        Query(
            ge=1,
            description="頁碼，從 1 開始。",
        ),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            alias="pageSize",
            ge=1,
            description="每頁筆數，預設為 10。",
        ),
    ] = 10,
) -> RacketListResponse:
    rackets, total_items = service.query_rackets(
        budget=budget,
        playing_style=playing_style,
        brand=brand,
        page=page,
        page_size=page_size,
    )

    total_pages = ceil(total_items / page_size)

    return RacketListResponse(
        data=[
            RacketQueryResponse.model_validate(racket)
            for racket in rackets
        ],
        pagination=RacketPaginationResponse(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )