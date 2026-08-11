"""add strings and shoes

Revision ID: 2f051ab3f330
Revises: a217395cc2db
Create Date: 2026-08-09 17:19:38.780905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
# revision: str = '2f051ab3f330'
# down_revision: Union[str, Sequence[str], None] = 'a217395cc2db'
# branch_labels: Union[str, Sequence[str], None] = None
# depends_on: Union[str, Sequence[str], None] = None
revision = "add_strings_and_shoes"
down_revision: Union[str, Sequence[str], None] = 'a217395cc2db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# def upgrade() -> None:
#     """Upgrade schema."""
#     pass


# def downgrade() -> None:
#     """Downgrade schema."""
#     pass

def upgrade():

    op.create_table(
        "strings",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "brand",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "model",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            Vector(768),
            nullable=True,
        ),
    )

    op.create_table(
        "shoes",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "brand",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "model",
            sa.String(200),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            Vector(768),
            nullable=True,
        ),
    )


def downgrade():

    op.drop_table("shoes")
    op.drop_table("strings")