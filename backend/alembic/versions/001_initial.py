"""Create initial tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-04-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('industry_tags', postgresql.JSONB(), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('platform_confidence', sa.Float(), nullable=True),
        sa.Column('base44_connected', sa.Boolean(), nullable=False),
        sa.Column('gsc_connected', sa.Boolean(), nullable=False),
        sa.Column('sitemaps_found', sa.Boolean(), nullable=False),
        sa.Column('gsc_verified', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_companies_user_id'), 'companies', ['user_id'])
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'])

    # Create seo_scans table
    op.create_table(
        'seo_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('meta_score', sa.Integer(), nullable=True),
        sa.Column('content_score', sa.Integer(), nullable=True),
        sa.Column('technical_score', sa.Integer(), nullable=True),
        sa.Column('legal_score', sa.Integer(), nullable=True),
        sa.Column('pages_crawled', sa.Integer(), nullable=False),
        sa.Column('urls_discovered', sa.Integer(), nullable=False),
        sa.Column('healthy_pages', sa.Integer(), nullable=False),
        sa.Column('page_types', sa.Integer(), nullable=False),
        sa.Column('impressum_found', sa.Boolean(), nullable=False),
        sa.Column('privacy_found', sa.Boolean(), nullable=False),
        sa.Column('terms_found', sa.Boolean(), nullable=False),
        sa.Column('impressum_completeness', sa.Float(), nullable=True),
        sa.Column('privacy_completeness', sa.Float(), nullable=True),
        sa.Column('terms_completeness', sa.Float(), nullable=True),
        sa.Column('raw_results', postgresql.JSONB(), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_seo_scans_company_id'), 'seo_scans', ['company_id'])

    # Create additional tables as needed...


def downgrade():
    op.drop_table('seo_scans')
    op.drop_table('companies')
    op.drop_table('users')
