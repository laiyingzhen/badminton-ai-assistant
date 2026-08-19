"""add racket image and affiliate urls

Revision ID: c842a31d8e20
Revises: b7c52ae41f10
Create Date: 2026-08-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c842a31d8e20"
down_revision: Union[str, Sequence[str], None] = (
    "b7c52ae41f10"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rackets",
        sa.Column(
            "image_url",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "rackets",
        sa.Column(
            "affiliate_url",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("rackets", "affiliate_url")
    op.drop_column("rackets", "image_url")