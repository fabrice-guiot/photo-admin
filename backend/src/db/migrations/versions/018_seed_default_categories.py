"""Seed default categories

Revision ID: 018_seed_default_categories
Revises: 017_create_event_performers
Create Date: 2026-01-11

Seeds the default categories for calendar events.
Part of Issue #39 - Calendar Events feature.

Categories are user-editable after initial setup.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid import uuid4
import uuid as uuid_module


# revision identifiers, used by Alembic.
revision = '018_seed_default_categories'
down_revision = '017_create_event_performers'
branch_labels = None
depends_on = None


# Default categories with icons and colors from data-model.md
DEFAULT_CATEGORIES = [
    {'name': 'Airshow', 'icon': 'plane', 'color': '#3B82F6', 'display_order': 0},
    {'name': 'Wildlife', 'icon': 'bird', 'color': '#22C55E', 'display_order': 1},
    {'name': 'Wedding', 'icon': 'heart', 'color': '#EC4899', 'display_order': 2},
    {'name': 'Sports', 'icon': 'trophy', 'color': '#F97316', 'display_order': 3},
    {'name': 'Portrait', 'icon': 'user', 'color': '#8B5CF6', 'display_order': 4},
    {'name': 'Concert', 'icon': 'music', 'color': '#EF4444', 'display_order': 5},
    {'name': 'Motorsports', 'icon': 'car', 'color': '#6B7280', 'display_order': 6},
]


def upgrade() -> None:
    """Seed default categories."""
    # Build the insert statement
    categories_table = sa.table(
        'categories',
        sa.column('uuid', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String),
        sa.column('icon', sa.String),
        sa.column('color', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('display_order', sa.Integer),
    )

    # Insert each category with a generated UUID
    for category in DEFAULT_CATEGORIES:
        op.execute(
            categories_table.insert().values(
                uuid=uuid4(),
                name=category['name'],
                icon=category['icon'],
                color=category['color'],
                is_active=True,
                display_order=category['display_order'],
            )
        )


def downgrade() -> None:
    """Remove seeded categories (only if no dependent records exist)."""
    # Delete categories by name - will fail if any have dependent records
    # due to RESTRICT foreign keys, which is the desired behavior
    categories_table = sa.table(
        'categories',
        sa.column('name', sa.String),
    )

    for category in DEFAULT_CATEGORIES:
        op.execute(
            categories_table.delete().where(
                categories_table.c.name == category['name']
            )
        )
