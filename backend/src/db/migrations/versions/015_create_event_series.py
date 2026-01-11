"""Create event_series table

Revision ID: 015_create_event_series
Revises: 014_create_performers
Create Date: 2026-01-11

Creates the event_series table for multi-day event groupings.
Part of Issue #39 - Calendar Events feature.

EventSeries stores shared properties for events spanning multiple days.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '015_create_event_series'
down_revision = '014_create_performers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create event_series table with FKs to categories, locations, organizers.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - category_id: FK to categories (RESTRICT on delete)
    - location_id: FK to locations (SET NULL on delete)
    - organizer_id: FK to organizers (SET NULL on delete)
    - title: Series title
    - description: Series description
    - input_timezone: IANA timezone for input display
    - ticket_required, timeoff_required, travel_required: Logistics defaults
    - total_events: Number of events in series
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'event_series',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'uuid',
            postgresql.UUID(as_uuid=True).with_variant(
                sa.LargeBinary(16), 'sqlite'
            ),
            nullable=False
        ),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('organizer_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_timezone', sa.String(length=64), nullable=True),
        sa.Column('ticket_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timeoff_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('travel_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organizer_id'], ['organizers.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_event_series_uuid', 'event_series', ['uuid'], unique=True)
    op.create_index('ix_event_series_category_id', 'event_series', ['category_id'])
    op.create_index('ix_event_series_location_id', 'event_series', ['location_id'])
    op.create_index('ix_event_series_organizer_id', 'event_series', ['organizer_id'])


def downgrade() -> None:
    """Drop event_series table."""
    op.drop_index('ix_event_series_organizer_id', table_name='event_series')
    op.drop_index('ix_event_series_location_id', table_name='event_series')
    op.drop_index('ix_event_series_category_id', table_name='event_series')
    op.drop_index('ix_event_series_uuid', table_name='event_series')
    op.drop_table('event_series')
