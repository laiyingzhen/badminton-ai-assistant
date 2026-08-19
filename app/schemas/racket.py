from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


RacketPlayingStyle = Literal[
    "offensive",
    "defensive",
    "all_round",
]

RacketBrand = Literal[
    "YONEX",
    "VICTOR",
    "LI-NING",
    "JNICE",
]


class RacketQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand: str
    model: str
    price: Decimal
    weight: str | None
    balance: str | None
    flexibility: str | None
    suitable_level: str | None
    playing_style: str | None
    description: str | None
    image_url: str | None
    affiliate_url: str | None
    is_active: bool