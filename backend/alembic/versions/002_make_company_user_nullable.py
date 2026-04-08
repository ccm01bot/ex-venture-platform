"""Make company user_id nullable

Revision ID: 002_make_company_user_nullable
Revises: 001_initial
Create Date: 2026-04-05

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('companies', 'user_id', existing_type=sa.dialects.postgresql.UUID(), nullable=True)


def downgrade():
    op.alter_column('companies', 'user_id', existing_type=sa.dialects.postgresql.UUID(), nullable=False)
