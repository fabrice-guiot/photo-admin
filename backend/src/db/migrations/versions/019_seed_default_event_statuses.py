"""Seed default event statuses

Revision ID: 019_seed_default_event_statuses
Revises: 018_seed_default_categories
Create Date: 2026-01-12

Seeds the default event statuses for calendar events.
Part of Issue #39 - Calendar Events feature (Phase 12).

Statuses are user-editable after initial setup via Settings > Config.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '019_seed_default_event_statuses'
down_revision = '018_seed_default_categories'
branch_labels = None
depends_on = None


# Default event statuses with display order
# key: the status value used in code
# label: human-readable display name
# display_order: order in dropdowns/lists
DEFAULT_EVENT_STATUSES = [
    {'key': 'future', 'label': 'Future', 'display_order': 0},
    {'key': 'confirmed', 'label': 'Confirmed', 'display_order': 1},
    {'key': 'completed', 'label': 'Completed', 'display_order': 2},
    {'key': 'cancelled', 'label': 'Cancelled', 'display_order': 3},
]


def upgrade() -> None:
    """Seed default event statuses."""
    # Build the insert statement for configurations table
    configurations_table = sa.table(
        'configurations',
        sa.column('category', sa.String),
        sa.column('key', sa.String),
        sa.column('value_json', postgresql.JSONB),
        sa.column('description', sa.Text),
        sa.column('source', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    now = datetime.utcnow()

    # Insert each status
    for status in DEFAULT_EVENT_STATUSES:
        op.execute(
            configurations_table.insert().values(
                category='event_statuses',
                key=status['key'],
                value_json={'label': status['label'], 'display_order': status['display_order']},
                description=f"Event status: {status['label']}",
                source='database',
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    """Remove seeded event statuses."""
    configurations_table = sa.table(
        'configurations',
        sa.column('category', sa.String),
        sa.column('key', sa.String),
    )

    for status in DEFAULT_EVENT_STATUSES:
        op.execute(
            configurations_table.delete().where(
                sa.and_(
                    configurations_table.c.category == 'event_statuses',
                    configurations_table.c.key == status['key']
                )
            )
        )
