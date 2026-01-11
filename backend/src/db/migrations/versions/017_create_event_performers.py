"""Create event_performers junction table

Revision ID: 017_create_event_performers
Revises: 016_create_events
Create Date: 2026-01-11

Creates the event_performers junction table linking performers to events.
Part of Issue #39 - Calendar Events feature.

This is a many-to-many junction table with performer status tracking.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017_create_event_performers'
down_revision = '016_create_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create event_performers junction table.

    Columns:
    - id: Primary key
    - event_id: FK to events (CASCADE on delete)
    - performer_id: FK to performers (RESTRICT on delete)
    - status: Performer status (confirmed, cancelled)
    - created_at: When performer was added

    Constraints:
    - Unique (event_id, performer_id) - performer can only be added once per event
    """
    op.create_table(
        'event_performers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('performer_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='confirmed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performer_id'], ['performers.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('event_id', 'performer_id', name='uq_event_performer')
    )

    # Create indexes for efficient lookups
    op.create_index('ix_event_performers_event_id', 'event_performers', ['event_id'])
    op.create_index('ix_event_performers_performer_id', 'event_performers', ['performer_id'])


def downgrade() -> None:
    """Drop event_performers table."""
    op.drop_index('ix_event_performers_performer_id', table_name='event_performers')
    op.drop_index('ix_event_performers_event_id', table_name='event_performers')
    op.drop_table('event_performers')
