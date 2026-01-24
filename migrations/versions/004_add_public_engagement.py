"""
Add Public Engagement Tables

Revision ID: 004_add_public_engagement
Revises: 003_add_explainable_ai
Create Date: 2026-01-22

Tables:
- public_reports: Main reports from public
- public_report_media: Media attachments
- public_report_links: Duplicate report links
- public_engagement_audit_logs: Audit trail
- public_report_timeline: Public-safe timeline entries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_add_public_engagement'
down_revision = '003_add_explainable_ai'
branch_labels = None
depends_on = None


def upgrade():
    """Create public engagement tables."""
    
    # Create enum types
    op.execute("""
        CREATE TYPE report_category AS ENUM (
            'leak', 'burst', 'no_water', 'low_pressure',
            'illegal_connection', 'overflow', 'contamination', 'other'
        );
    """)
    
    op.execute("""
        CREATE TYPE report_status AS ENUM (
            'received', 'under_review', 'technician_assigned',
            'in_progress', 'resolved', 'closed'
        );
    """)
    
    op.execute("""
        CREATE TYPE report_source AS ENUM (
            'web', 'whatsapp', 'ussd', 'mobile_app', 'call_center'
        );
    """)
    
    op.execute("""
        CREATE TYPE report_verification AS ENUM (
            'pending', 'confirmed', 'duplicate', 'false_report',
            'needs_review', 'spam'
        );
    """)
    
    op.execute("""
        CREATE TYPE media_type AS ENUM (
            'image', 'video', 'audio'
        );
    """)
    
    # ==========================================================================
    # PUBLIC_REPORTS TABLE
    # ==========================================================================
    op.create_table(
        'public_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket', sa.String(20), unique=True, nullable=False),
        
        # Classification
        sa.Column('category', sa.Enum('leak', 'burst', 'no_water', 'low_pressure', 'illegal_connection', 'overflow', 'contamination', 'other', name='report_category'), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        
        # Location
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('area_text', sa.String(500), nullable=True),
        sa.Column('dma_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dmas.id'), nullable=True),
        
        # Source
        sa.Column('source', sa.Enum('web', 'whatsapp', 'ussd', 'mobile_app', 'call_center', name='report_source'), nullable=False, server_default='web'),
        
        # Reporter (PRIVATE)
        sa.Column('reporter_name', sa.String(200), nullable=True),
        sa.Column('reporter_phone', sa.String(50), nullable=True),
        sa.Column('reporter_email', sa.String(200), nullable=True),
        sa.Column('reporter_consent', sa.Boolean, server_default='false'),
        sa.Column('whatsapp_phone_hash', sa.String(64), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        
        # Status
        sa.Column('status', sa.Enum('received', 'under_review', 'technician_assigned', 'in_progress', 'resolved', 'closed', name='report_status'), nullable=False, server_default='received'),
        sa.Column('verification', sa.Enum('pending', 'confirmed', 'duplicate', 'false_report', 'needs_review', 'spam', name='report_verification'), server_default='pending'),
        
        # Trust/Spam
        sa.Column('trust_score_delta', sa.Integer, server_default='0'),
        sa.Column('spam_flag', sa.Boolean, server_default='false'),
        sa.Column('spam_reason', sa.String(200), nullable=True),
        sa.Column('quarantine', sa.Boolean, server_default='false'),
        
        # Duplicates
        sa.Column('master_report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public_reports.id'), nullable=True),
        sa.Column('is_master', sa.Boolean, server_default='true'),
        sa.Column('duplicate_count', sa.Integer, server_default='0'),
        
        # Linking
        sa.Column('linked_leak_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leak_events.id'), nullable=True),
        sa.Column('linked_alert_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('alerts.id'), nullable=True),
        sa.Column('linked_work_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('work_orders.id'), nullable=True),
        
        # Admin (PRIVATE)
        sa.Column('admin_notes', sa.Text, nullable=True),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_team', sa.String(100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        
        # Resolution
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        
        # Rate limiting
        sa.Column('reporter_ip', sa.String(50), nullable=True),
        sa.Column('device_fingerprint', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Indexes for public_reports
    op.create_index('ix_public_reports_tenant_id', 'public_reports', ['tenant_id'])
    op.create_index('ix_public_reports_ticket', 'public_reports', ['ticket'])
    op.create_index('ix_public_reports_status', 'public_reports', ['status'])
    op.create_index('ix_public_reports_category', 'public_reports', ['category'])
    op.create_index('ix_public_reports_location', 'public_reports', ['latitude', 'longitude'])
    op.create_index('ix_public_reports_created', 'public_reports', ['created_at'])
    op.create_index('ix_public_reports_spam', 'public_reports', ['spam_flag', 'quarantine'])
    op.create_index('ix_public_reports_master', 'public_reports', ['master_report_id'])
    op.create_index('ix_public_reports_dma', 'public_reports', ['dma_id'])
    op.create_index('ix_public_reports_verification', 'public_reports', ['verification'])
    
    # Composite index for admin filtering
    op.create_index(
        'ix_public_reports_admin_filter',
        'public_reports',
        ['tenant_id', 'status', 'category', 'created_at']
    )
    
    # ==========================================================================
    # PUBLIC_REPORT_MEDIA TABLE
    # ==========================================================================
    op.create_table(
        'public_report_media',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public_reports.id', ondelete='CASCADE'), nullable=False),
        
        # File info
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('media_type', sa.Enum('image', 'video', 'audio', name='media_type'), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        
        # Storage
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('url', sa.String(500), nullable=True),
        
        # Dimensions
        sa.Column('width', sa.Integer, nullable=True),
        sa.Column('height', sa.Integer, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        
        # EXIF GPS
        sa.Column('exif_latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('exif_longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('exif_timestamp', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('ix_public_report_media_tenant', 'public_report_media', ['tenant_id'])
    op.create_index('ix_public_report_media_report', 'public_report_media', ['report_id'])
    
    # ==========================================================================
    # PUBLIC_REPORT_LINKS TABLE
    # ==========================================================================
    op.create_table(
        'public_report_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('master_report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('duplicate_report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public_reports.id', ondelete='CASCADE'), nullable=False),
        
        # Metadata
        sa.Column('reason', sa.String(200), nullable=True),
        sa.Column('distance_meters', sa.Numeric(10, 2), nullable=True),
        sa.Column('time_diff_minutes', sa.Integer, nullable=True),
        sa.Column('similarity_score', sa.Numeric(5, 4), nullable=True),
        
        # Linking info
        sa.Column('auto_detected', sa.Boolean, server_default='true'),
        sa.Column('linked_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('master_report_id', 'duplicate_report_id', name='uq_report_link'),
    )
    
    op.create_index('ix_public_report_links_tenant', 'public_report_links', ['tenant_id'])
    op.create_index('ix_public_report_links_master', 'public_report_links', ['master_report_id'])
    op.create_index('ix_public_report_links_duplicate', 'public_report_links', ['duplicate_report_id'])
    
    # ==========================================================================
    # PUBLIC_ENGAGEMENT_AUDIT_LOGS TABLE
    # ==========================================================================
    op.create_table(
        'public_engagement_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        
        # Actor
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('actor_type', sa.String(50), server_default='system'),
        
        # Action
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Details
        sa.Column('meta_json', postgresql.JSONB, nullable=True),
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('new_values', postgresql.JSONB, nullable=True),
        
        # Context
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('ix_pe_audit_tenant', 'public_engagement_audit_logs', ['tenant_id'])
    op.create_index('ix_pe_audit_entity', 'public_engagement_audit_logs', ['entity_type', 'entity_id'])
    op.create_index('ix_pe_audit_action', 'public_engagement_audit_logs', ['action'])
    op.create_index('ix_pe_audit_created', 'public_engagement_audit_logs', ['created_at'])
    
    # ==========================================================================
    # PUBLIC_REPORT_TIMELINE TABLE
    # ==========================================================================
    op.create_table(
        'public_report_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('received', 'under_review', 'technician_assigned', 'in_progress', 'resolved', 'closed', name='report_status', create_type=False), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('ix_pe_timeline_tenant', 'public_report_timeline', ['tenant_id'])
    op.create_index('ix_pe_timeline_report', 'public_report_timeline', ['report_id'])
    op.create_index('ix_pe_timeline_created', 'public_report_timeline', ['created_at'])


def downgrade():
    """Remove public engagement tables."""
    
    # Drop tables
    op.drop_table('public_report_timeline')
    op.drop_table('public_engagement_audit_logs')
    op.drop_table('public_report_links')
    op.drop_table('public_report_media')
    op.drop_table('public_reports')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS media_type;')
    op.execute('DROP TYPE IF EXISTS report_verification;')
    op.execute('DROP TYPE IF EXISTS report_source;')
    op.execute('DROP TYPE IF EXISTS report_status;')
    op.execute('DROP TYPE IF EXISTS report_category;')
