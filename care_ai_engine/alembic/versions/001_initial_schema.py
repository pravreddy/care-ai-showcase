"""Initial schema with all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('organisation', sa.String(255), nullable=True),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('totp_secret', sa.String(64), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), default=False),
        sa.Column('totp_verified', sa.Boolean(), default=False),
        sa.Column('recovery_codes_hash', postgresql.JSON(), nullable=True),
        sa.Column('coupon_code', sa.String(50), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tier', sa.Enum('free', 'pro', 'agency', 'enterprise', name='subscriptiontier'), nullable=False),
        sa.Column('status', sa.Enum('active', 'trialing', 'cancelled', 'past_due', 'expired', name='subscriptionstatus'), nullable=False),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'], unique=True)

    # Create usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ai_queries', sa.Integer(), default=0),
        sa.Column('voice_notes_count', sa.Integer(), default=0),
        sa.Column('storage_used_mb', sa.Float(), default=0.0),
        sa.Column('processing_seconds', sa.Float(), default=0.0),
        sa.Column('tokens_used', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_usage_user_date', 'usage_records', ['user_id', 'date'], unique=True)

    # Create voice_notes table
    op.create_table(
        'voice_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('input_type', sa.String(20), default='audio'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('clinical_note_data', postgresql.JSON(), nullable=True),
        sa.Column('client_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_voice_notes_user_created', 'voice_notes', ['user_id', 'created_at'])

    # Create partner_accounts table
    op.create_table(
        'partner_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('tier', sa.String(50), default='starter'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('monthly_quota', sa.Integer(), default=10000),
        sa.Column('requests_this_month', sa.Integer(), default=0),
        sa.Column('quota_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_test', sa.Boolean(), default=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_requests', sa.BigInteger(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['partner_id'], ['partner_accounts.id'], ),
    )
    op.create_index('ix_api_keys_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_partner_created', 'api_keys', ['partner_id', 'created_at'])

    # Create coupons table
    op.create_table(
        'coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('tier_granted', sa.Enum('free', 'pro', 'agency', 'enterprise', name='subscriptiontier'), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    op.create_index('ix_coupons_code', 'coupons', ['code'], unique=True)

    # Create coupon_redemptions table
    op.create_table(
        'coupon_redemptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('granted_tier', sa.String(50), nullable=False),
        sa.Column('granted_until', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('ix_redemption_user_coupon', 'coupon_redemptions', ['user_id', 'coupon_id'], unique=True)

    # Create medical_knowledge_log table
    op.create_table(
        'medical_knowledge_log',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('item_name', sa.String(500), nullable=False),
        sa.Column('item_url', sa.String(1000), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('character_count', sa.Integer(), default=0),
    )
    op.create_index('ix_knowledge_source_name', 'medical_knowledge_log', ['source', 'item_name'], unique=True)


def downgrade() -> None:
    op.drop_table('medical_knowledge_log')
    op.drop_table('coupon_redemptions')
    op.drop_table('coupons')
    op.drop_table('api_keys')
    op.drop_table('partner_accounts')
    op.drop_table('voice_notes')
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
