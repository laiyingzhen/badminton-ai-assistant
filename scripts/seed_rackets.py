from decimal import Decimal

from app.core.database import SessionLocal
from app.models.racket import Racket


def seed():
    db = SessionLocal()

    try:
        rackets = [
            Racket(
                brand="Yonex",
                model="Astrox 88D Pro",
                price=Decimal("4990"),
                weight="4U",
                balance="Head Heavy",
                flexibility="Stiff",
                suitable_level="intermediate",
                playing_style="offensive",
                description="偏進攻型，適合後場進攻與雙打後排球員。",
            ),
            Racket(
                brand="Yonex",
                model="Astrox 7 DG",
                price=Decimal("2990"),
                weight="4U",
                balance="Head Heavy",
                flexibility="Medium",
                suitable_level="beginner",
                playing_style="offensive",
                description="較容易上手的進攻型球拍。",
            ),
            Racket(
                brand="Yonex",
                model="Nanoflare 700",
                price=Decimal("4500"),
                weight="4U",
                balance="Even",
                flexibility="Medium",
                suitable_level="intermediate",
                playing_style="all_round",
                description="偏向快速揮拍與攻守平衡。",
            ),
        ]

        db.add_all(rackets)
        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed()