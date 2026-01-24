"""Add notification system tables

Revision ID: 002
Revises: 001_add_multi_tenancy
Create Date: 2026-01-22

This migration adds:
1. notification_rules - Configurable notification rules per tenant
2. notifications - Individual notifications sent to users
3. escalation_trackers - Tracks escalation state for alerts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '002_add_notification_system'
down_revision: Union[str, None] = '001_add_multi_tenancy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add notification system tables.
    
    Tables:
    - notification_rules: Defines when and how to notify
    - notifications: Individual notifications to users
    - escalation_trackers: Tracks alert escalation state
    """
    
    # =========================================================================
    # STEP 1: Create ENUM types
    # =========================================================================
    
    notification_channel_enum = postgresql.ENUM(
        'in_app', 'email', 'sms', 'whatsapp', 'push', 'webhook',
        name='notificationchannel',
        create_type=True
    )
    notification_channel_enum.create(op.get_bind(), checkfirst=True)
    
    notification_severity_enum = postgresql.ENUM(
        'info', 'warning', 'critical',
        name='notificationseverity',
        create_type=True
    )
    notification_severity_enum.create(op.get_bind(), checkfirst=True)
    
    notification_status_enum = postgresql.ENUM(
        'pending', 'sent', 'delivered', 'read', 'failed',
        name='notificationstatus',
        create_type=True
    )
    notification_status_enum.create(op.get_bind(), checkfirst=True)
    
    # =========================================================================
    # STEP 2: Create notification_rules table
    # =========================================================================
    
    op.create_table(
        'notification_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), 
                  nullable=False),
        
        # Rule identification
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        
        # Trigger conditions
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'critical', 
                                       name='notificationseverity'), nullable=False),
        
        # Target roles
        sa.Column('target_roles', postgresql.JSONB, server_default='["operator"]'),
        
        # Channels configuration
        sa.Column('channels', postgresql.JSONB, nullable=False, 
                  server_default='{"in_app": {"enabled": true}}'),
        
        # Escalation configuration
        sa.Column('escalation', postgresql.JSONB, server_default='[]'),
        
        # Conditions filter
        sa.Column('conditions', postgresql.JSONB, server_default='{}'),
        
        # Throttling
        sa.Column('cooldown_minutes', sa.Integer, server_default='15'),
        
        # Status
        sa.Column('is_active', sa.Boolean, server_default='true'),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )
    
    # Indexes for notification_rules
    op.create_index('ix_notification_rules_tenant', 'notification_rules', ['tenant_id'])
    op.create_index('ix_notification_rules_event', 'notification_rules', ['event_type'])
    op.create_index('ix_notification_rules_severity', 'notification_rules', ['severity'])
    op.create_unique_constraint('uq_notification_rule_name', 'notification_rules', 
                                ['tenant_id', 'name'])
    
    # =========================================================================
    # STEP 3: Create notifications table
    # =========================================================================
    
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        
        # Content
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        
        # Classification
        sa.Column('severity', sa.Enum('info', 'warning', 'critical',
                                       name='notificationseverity'), 
                  nullable=False, server_default='info'),
        sa.Column('category', sa.String(50), nullable=True),
        
        # Source reference
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', sa.String(100), nullable=True),
        
        # Delivery
        sa.Column('channel', sa.Enum('in_app', 'email', 'sms', 'whatsapp', 'push', 'webhook',
                                      name='notificationchannel'),
                  server_default='in_app'),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'read', 'failed',
                                     name='notificationstatus'),
                  server_default='pending'),
        
        # For in-app notifications
        sa.Column('read', sa.Boolean, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        
        # Action URL
        sa.Column('action_url', sa.String(500), nullable=True),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        
        # Timing
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        
        # Delivery tracking
        sa.Column('delivery_attempts', sa.Integer, server_default='0'),
        sa.Column('last_error', sa.Text, nullable=True),
        
        # Link to rule
        sa.Column('rule_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('notification_rules.id', ondelete='SET NULL'), nullable=True),
    )
    
    # Indexes for notifications
    op.create_index('ix_notifications_tenant_user', 'notifications', ['tenant_id', 'user_id'])
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'read'])
    op.create_index('ix_notifications_created', 'notifications', ['created_at'])
    op.create_index('ix_notifications_status', 'notifications', ['status'])
    
    # =========================================================================
    # STEP 4: Create escalation_trackers table
    # =========================================================================
    
    op.create_table(
        'escalation_trackers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                  nullable=False),
        
        # Source reference
        sa.Column('alert_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('alerts.id', ondelete='CASCADE'), nullable=False),
        
        # Escalation state
        sa.Column('current_level', sa.Integer, server_default='0'),
        sa.Column('max_level', sa.Integer, server_default='2'),
        
        # Timing
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_escalation_at', sa.DateTime(timezone=True), nullable=True),
        
        # Status
        sa.Column('is_resolved', sa.Boolean, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_type', sa.String(50), nullable=True),
        
        # Notification history
        sa.Column('notifications_sent', postgresql.JSONB, server_default='[]'),
    )
    
    # Indexes for escalation_trackers
    op.create_index('ix_escalation_tenant', 'escalation_trackers', ['tenant_id'])
    op.create_index('ix_escalation_alert', 'escalation_trackers', ['alert_id'])
    op.create_index('ix_escalation_next', 'escalation_trackers', ['next_escalation_at'])
    op.create_unique_constraint('uq_escalation_alert', 'escalation_trackers', ['alert_id'])
    
    # =========================================================================
    # STEP 5: Insert default notification rules for default tenant
    # =========================================================================
    
    op.execute("""
        INSERT INTO notification_rules (tenant_id, name, event_type, severity, target_roles, channels, escalation, is_active)
        VALUES 
        -- Critical leak detection - notify operators immediately, escalate to engineer in 5min
        ('default-tenant', 'Critical Leak Alert', 'leak.detected', 'critical', 
         '["operator"]', 
         '{"in_app": {"enabled": true}, "email": {"enabled": true}, "sms": {"enabled": true}}',
         '[{"delay_minutes": 5, "roles": ["engineer"], "channels": ["in_app", "sms"]}, 
           {"delay_minutes": 120, "roles": ["executive"], "channels": ["in_app", "email"]}]',
         true),
        
        -- High priority leak
        ('default-tenant', 'High Priority Leak Alert', 'leak.detected', 'warning',
         '["operator"]',
         '{"in_app": {"enabled": true}, "email": {"enabled": true}}',
         '[{"delay_minutes": 30, "roles": ["engineer"], "channels": ["in_app"]}]',
         true),
        
        -- Sensor offline
        ('default-tenant', 'Sensor Offline Alert', 'sensor.offline', 'warning',
         '["operator", "engineer"]',
         '{"in_app": {"enabled": true}}',
         '[]',
         true),
        
        -- Work order created
        ('default-tenant', 'Work Order Notification', 'work_order.created', 'info',
         '["technician"]',
         '{"in_app": {"enabled": true}}',
         '[]',
         true)
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    """Remove notification system tables."""
    
    # Drop tables
    op.drop_table('escalation_trackers')
    op.drop_table('notifications')
    op.drop_table('notification_rules')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS notificationstatus')
    op.execute('DROP TYPE IF EXISTS notificationseverity')
    op.execute('DROP TYPE IF EXISTS notificationchannel')
