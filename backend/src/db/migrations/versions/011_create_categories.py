"""Create categories table

Revision ID: 011_create_categories
Revises: 010_add_uuid_columns
Create Date: 2026-01-11

Creates the categories table for event classification.
Part of Issue #39 - Calendar Events feature.

Categories are foundational - Events, Locations, Organizers, and Performers
all reference categories to ensure consistent grouping.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid_extensions import uuid7


# revision identifiers, used by Alembic.
revision = '011_create_categories'
down_revision = '010_add_uuid_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create categories table.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - name: Category name (unique)
    - color: Hex color code (#RRGGBB)
    - icon: Lucide icon name
    - is_active: Whether category is available
    - display_order: Sort order in UI
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'uuid',
            postgresql.UUID(as_uuid=True).with_variant(
                sa.LargeBinary(16), 'sqlite'
            ),
            nullable=False
        ),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_categories_uuid', 'categories', ['uuid'], unique=True)
    op.create_index('ix_categories_name', 'categories', ['name'], unique=True)
    op.create_index('idx_categories_active_order', 'categories', ['is_active', 'display_order'])


def downgrade() -> None:
    """Drop categories table."""
    op.drop_index('idx_categories_active_order', table_name='categories')
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_index('ix_categories_uuid', table_name='categories')
    op.drop_table('categories')
