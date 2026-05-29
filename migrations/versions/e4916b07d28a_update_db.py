"""update db

Revision ID: e4916b07d28a
Revises: 9f33b813bdc8
Create Date: 2026-05-29 20:58:06.880936

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e4916b07d28a'
down_revision: Union[str, Sequence[str], None] = '9f33b813bdc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
