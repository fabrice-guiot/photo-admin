"""Create locations table

Revision ID: 012_create_locations
Revises: 011_create_categories
Create Date: 2026-01-11

Creates the locations table for event venues.
Part of Issue #39 - Calendar Events feature.

Locations include geocoded coordinates for timezone detection
and default logistics settings.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '012_create_locations'
down_revision = '011_create_categories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create locations table with FK to categories.

    Columns:
    - id: Primary key
    - uuid: UUIDv7 for external identification
    - category_id: FK to categories (RESTRICT on delete)
    - name: Location name
    - address, city, state, country, postal_code: Address components
    - latitude, longitude: Geocoded coordinates
    - timezone: IANA timezone identifier
    - rating: 1-5 rating
    - timeoff_required_default, travel_required_default: Logistics defaults
    - notes: Additional notes
    - is_known: Whether saved as "known location"
    - created_at/updated_at: Timestamps
    """
    op.create_table(
        'locations',
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
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('timeoff_required_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('travel_required_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_known', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('uuid')
    )

    # Create indexes
    op.create_index('ix_locations_uuid', 'locations', ['uuid'], unique=True)
    op.create_index('ix_locations_category_id', 'locations', ['category_id'])
    op.create_index('idx_locations_known_category', 'locations', ['is_known', 'category_id'])


def downgrade() -> None:
    """Drop locations table."""
    op.drop_index('idx_locations_known_category', table_name='locations')
    op.drop_index('ix_locations_category_id', table_name='locations')
    op.drop_index('ix_locations_uuid', table_name='locations')
    op.drop_table('locations')
