"""Initial schema - all BBB tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('subscription_tier', sa.String(50), server_default='free'),
        sa.Column('stripe_customer_id', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('license_status', sa.String(50), server_default='trial'),
        sa.Column('license_terms_version', sa.String(20), server_default='v1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Businesses table
    op.create_table(
        'businesses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('business_type', sa.String(100)),
        sa.Column('industry', sa.String(100)),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('settings', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Business Plans table
    op.create_table(
        'business_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plan_data', JSONB(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Marketing Campaigns table
    op.create_table(
        'marketing_campaigns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('platform', sa.String(100), nullable=True),
        sa.Column('campaign_type', sa.String(100), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='draft'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('performance_metrics', JSONB(), nullable=True),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True, nullable=True),
        sa.Column('plan_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('key_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('marketing_campaigns')
    op.drop_table('business_plans')
    op.drop_table('businesses')
    op.drop_table('users')
