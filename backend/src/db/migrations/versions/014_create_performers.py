"""Create performers table

Revision ID: 014_create_performers
Revises: 013_create_organizers
Create Date: 2026-01-11

Creates the performers table for event participants.
Part of Issue #39 - Calendar Events feature.

Performers are linked to events via the event_performers junction table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '014_create_performers'
down_revision = '013_create_organizers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create performers table with FK to categories.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - category_id: FK to categories (RESTRICT on delete)
    - name: Performer name
    - website: Website URL
    - instagram_handle: Instagram username (without @)
    - additional_info: Multiline notes
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'performers',
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
        sa.Column('instagram_handle', sa.String(length=100), nullable=True),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_performers_uuid', 'performers', ['uuid'], unique=True)
    op.create_index('ix_performers_category_id', 'performers', ['category_id'])


def downgrade() -> None:
    """Drop performers table."""
    op.drop_index('ix_performers_category_id', table_name='performers')
    op.drop_index('ix_performers_uuid', table_name='performers')
    op.drop_table('performers')
