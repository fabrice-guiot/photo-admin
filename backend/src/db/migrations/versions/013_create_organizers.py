"""Create organizers table

Revision ID: 013_create_organizers
Revises: 012_create_locations
Create Date: 2026-01-11

Creates the organizers table for event hosts.
Part of Issue #39 - Calendar Events feature.

Organizers have default ticket settings and ratings.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '013_create_organizers'
down_revision = '012_create_locations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create organizers table with FK to categories.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - category_id: FK to categories (RESTRICT on delete)
    - name: Organizer name
    - website: Website URL
    - rating: 1-5 rating
    - ticket_required_default: Pre-select ticket for new events
    - notes: Additional notes
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'organizers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'uuid',
            postgresql.UUID(as_uuid=True).with_variant(
                sa.LargeBinary(16), 'sqlite'
            ),
            nullable=False
        ),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('ticket_required_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_organizers_uuid', 'organizers', ['uuid'], unique=True)
    op.create_index('ix_organizers_category_id', 'organizers', ['category_id'])


def downgrade() -> None:
    """Drop organizers table."""
    op.drop_index('ix_organizers_category_id', table_name='organizers')
    op.drop_index('ix_organizers_uuid', table_name='organizers')
    op.drop_table('organizers')
