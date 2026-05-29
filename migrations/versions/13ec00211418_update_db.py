"""update db

Revision ID: 13ec00211418
Revises: e4916b07d28a
Create Date: 2026-05-29 20:59:23.599886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '13ec00211418'
down_revision: Union[str, Sequence[str], None] = 'e4916b07d28a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
