"""Add instagram_handle to locations and organizers tables

Revision ID: 020_add_instagram_handle
Revises: 019_seed_default_event_statuses
Create Date: 2026-01-14

Adds instagram_handle field to locations and organizers tables,
matching the existing implementation in performers.

Issue #78 - Instagram Handle for Locations and Organizers
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020_add_instagram_handle'
down_revision = '019_seed_default_event_statuses'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add instagram_handle column to locations and organizers tables.

    Column spec:
    - instagram_handle: String(100), nullable, stores Instagram username without @
    """
    # Add instagram_handle to locations table
    op.add_column(
        'locations',
        sa.Column('instagram_handle', sa.String(length=100), nullable=True)
    )

    # Add instagram_handle to organizers table
    op.add_column(
        'organizers',
        sa.Column('instagram_handle', sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    """Remove instagram_handle column from locations and organizers tables."""
    op.drop_column('organizers', 'instagram_handle')
    op.drop_column('locations', 'instagram_handle')
