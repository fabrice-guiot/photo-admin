"""Create events table

Revision ID: 016_create_events
Revises: 015_create_event_series
Create Date: 2026-01-11

Creates the events table for calendar events.
Part of Issue #39 - Calendar Events feature.

Events can be standalone or part of an EventSeries.
Supports soft delete and extensive logistics tracking.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '016_create_events'
down_revision = '015_create_event_series'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create events table with all FKs and soft delete support.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - series_id: FK to event_series (CASCADE on delete)
    - sequence_number: Position in series (1, 2, 3...)
    - category_id: FK to categories (RESTRICT, can be NULL for series events)
    - location_id: FK to locations (SET NULL)
    - organizer_id: FK to organizers (SET NULL)
    - title, description: Event details (can be NULL for series events)
    - event_date: Date of event
    - start_time, end_time: Time range (NULL for all-day)
    - is_all_day: Whether event is all-day
    - input_timezone: IANA timezone for display
    - status: Event status (future, confirmed, completed, cancelled)
    - attendance: Attendance status (planned, attended, skipped)
    - ticket_*, timeoff_*, travel_*: Logistics fields
    - deadline_date: Workflow deadline
    - deleted_at: Soft delete timestamp
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'uuid',
            postgresql.UUID(as_uuid=True).with_variant(
                sa.LargeBinary(16), 'sqlite'
            ),
            nullable=False
        ),
        # Series relationship
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        # Core FKs
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('organizer_id', sa.Integer(), nullable=True),
        # Core fields
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        # Time fields
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=True),
        sa.Column('end_time', sa.Time(), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('input_timezone', sa.String(length=64), nullable=True),
        # Status fields
        sa.Column('status', sa.String(length=50), nullable=False, server_default='future'),
        sa.Column('attendance', sa.String(length=50), nullable=False, server_default='planned'),
        # Ticket logistics
        sa.Column('ticket_required', sa.Boolean(), nullable=True),
        sa.Column('ticket_status', sa.String(length=50), nullable=True),
        sa.Column('ticket_purchase_date', sa.Date(), nullable=True),
        # Time-off logistics
        sa.Column('timeoff_required', sa.Boolean(), nullable=True),
        sa.Column('timeoff_status', sa.String(length=50), nullable=True),
        sa.Column('timeoff_booking_date', sa.Date(), nullable=True),
        # Travel logistics
        sa.Column('travel_required', sa.Boolean(), nullable=True),
        sa.Column('travel_status', sa.String(length=50), nullable=True),
        sa.Column('travel_booking_date', sa.Date(), nullable=True),
        # Workflow
        sa.Column('deadline_date', sa.Date(), nullable=True),
        # Soft delete
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['series_id'], ['event_series.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organizer_id'], ['organizers.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_events_uuid', 'events', ['uuid'], unique=True)
    op.create_index('ix_events_event_date', 'events', ['event_date'])
    op.create_index('ix_events_series_id', 'events', ['series_id'])
    op.create_index('ix_events_category_id', 'events', ['category_id'])
    op.create_index('ix_events_location_id', 'events', ['location_id'])
    op.create_index('ix_events_organizer_id', 'events', ['organizer_id'])
    op.create_index('ix_events_deleted_at', 'events', ['deleted_at'])

    # Composite indexes for common queries
    op.create_index('idx_events_date_deleted', 'events', ['event_date', 'deleted_at'])


def downgrade() -> None:
    """Drop events table."""
    op.drop_index('idx_events_date_deleted', table_name='events')
    op.drop_index('ix_events_deleted_at', table_name='events')
    op.drop_index('ix_events_organizer_id', table_name='events')
    op.drop_index('ix_events_location_id', table_name='events')
    op.drop_index('ix_events_category_id', table_name='events')
    op.drop_index('ix_events_series_id', table_name='events')
    op.drop_index('ix_events_event_date', table_name='events')
    op.drop_index('ix_events_uuid', table_name='events')
    op.drop_table('events')
