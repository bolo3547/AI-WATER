"""Add multi-tenancy support

Revision ID: 001
Revises: 
Create Date: 2026-01-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '001_add_multi_tenancy'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default tenant for backfilling existing data
DEFAULT_TENANT_ID = 'default-tenant'


def upgrade() -> None:
    """
    Add multi-tenancy support to the database.
    
    This migration:
    1. Creates tenants table
    2. Creates tenant_users table
    3. Adds tenant_id to existing tables (dmas, sensors, alerts, work_orders, audit_logs)
    4. Creates default tenant and backfills existing data
    5. Creates indexes for tenant_id columns
    
    NOTE: sensor_readings is a TimescaleDB hypertable - we handle it specially
    """
    
    # =========================================================================
    # STEP 1: Create ENUM types for new tables
    # =========================================================================
    
    tenant_plan_enum = postgresql.ENUM(
        'free', 'starter', 'professional', 'enterprise',
        name='tenantplan',
        create_type=True
    )
    tenant_plan_enum.create(op.get_bind(), checkfirst=True)
    
    tenant_role_enum = postgresql.ENUM(
        'owner', 'admin', 'operator', 'technician', 'viewer',
        name='tenantrole',
        create_type=True
    )
    tenant_role_enum.create(op.get_bind(), checkfirst=True)
    
    tenant_user_status_enum = postgresql.ENUM(
        'active', 'invited', 'suspended', 'removed',
        name='tenantuserstatus',
        create_type=True
    )
    tenant_user_status_enum.create(op.get_bind(), checkfirst=True)
    
    # =========================================================================
    # STEP 2: Create tenants table
    # =========================================================================
    
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('country', sa.String(3), nullable=True),  # ISO 3166-1 alpha-3
        sa.Column('timezone', sa.String(50), server_default='UTC'),
        sa.Column('plan', sa.Enum('free', 'starter', 'professional', 'enterprise', 
                                   name='tenantplan'), server_default='free'),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )
    
    op.create_index('ix_tenants_country', 'tenants', ['country'])
    op.create_index('ix_tenants_plan', 'tenants', ['plan'])
    
    # =========================================================================
    # STEP 3: Create tenant_users table
    # =========================================================================
    
    op.create_table(
        'tenant_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), 
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'operator', 'technician', 'viewer',
                                   name='tenantrole'), server_default='viewer'),
        sa.Column('status', sa.Enum('active', 'invited', 'suspended', 'removed',
                                     name='tenantuserstatus'), server_default='active'),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_access_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),
    )
    
    op.create_index('ix_tenant_users_tenant', 'tenant_users', ['tenant_id'])
    op.create_index('ix_tenant_users_user', 'tenant_users', ['user_id'])
    
    # =========================================================================
    # STEP 4: Insert default tenant BEFORE adding foreign keys
    # =========================================================================
    
    op.execute(f"""
        INSERT INTO tenants (id, name, country, timezone, plan, contact_email, is_active)
        VALUES (
            '{DEFAULT_TENANT_ID}',
            'LWSC Zambia (Default)',
            'ZMB',
            'Africa/Lusaka',
            'professional',
            'admin@lwsc.co.zm',
            true
        )
        ON CONFLICT (id) DO NOTHING;
    """)
    
    # =========================================================================
    # STEP 5: Add tenant_id to existing tables (nullable first)
    # =========================================================================
    
    # DMAs table
    op.add_column('dmas', sa.Column('tenant_id', sa.String(50), nullable=True))
    op.create_foreign_key('fk_dmas_tenant', 'dmas', 'tenants', ['tenant_id'], ['id'])
    op.create_index('ix_dmas_tenant_id', 'dmas', ['tenant_id'])
    
    # Sensors table
    op.add_column('sensors', sa.Column('tenant_id', sa.String(50), nullable=True))
    op.create_foreign_key('fk_sensors_tenant', 'sensors', 'tenants', ['tenant_id'], ['id'])
    op.create_index('ix_sensors_tenant_id', 'sensors', ['tenant_id'])
    
    # Alerts table
    op.add_column('alerts', sa.Column('tenant_id', sa.String(50), nullable=True))
    op.create_foreign_key('fk_alerts_tenant', 'alerts', 'tenants', ['tenant_id'], ['id'])
    op.create_index('ix_alerts_tenant_id', 'alerts', ['tenant_id'])
    
    # Work orders table
    op.add_column('work_orders', sa.Column('tenant_id', sa.String(50), nullable=True))
    op.create_foreign_key('fk_work_orders_tenant', 'work_orders', 'tenants', ['tenant_id'], ['id'])
    op.create_index('ix_work_orders_tenant_id', 'work_orders', ['tenant_id'])
    
    # Audit logs table
    op.add_column('audit_logs', sa.Column('tenant_id', sa.String(50), nullable=True))
    op.create_foreign_key('fk_audit_logs_tenant', 'audit_logs', 'tenants', ['tenant_id'], ['id'])
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    
    # =========================================================================
    # STEP 6: Backfill existing data with default tenant
    # =========================================================================
    
    op.execute(f"UPDATE dmas SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;")
    op.execute(f"UPDATE sensors SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;")
    op.execute(f"UPDATE alerts SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;")
    op.execute(f"UPDATE work_orders SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;")
    op.execute(f"UPDATE audit_logs SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;")
    
    # =========================================================================
    # STEP 7: Link existing users to default tenant
    # =========================================================================
    
    op.execute(f"""
        INSERT INTO tenant_users (tenant_id, user_id, role, status)
        SELECT 
            '{DEFAULT_TENANT_ID}',
            id,
            CASE 
                WHEN role = 'admin' THEN 'admin'::tenantrole
                WHEN role = 'operator' THEN 'operator'::tenantrole
                WHEN role = 'technician' THEN 'technician'::tenantrole
                ELSE 'viewer'::tenantrole
            END,
            'active'::tenantuserstatus
        FROM users
        WHERE NOT EXISTS (
            SELECT 1 FROM tenant_users 
            WHERE tenant_users.user_id = users.id 
            AND tenant_users.tenant_id = '{DEFAULT_TENANT_ID}'
        );
    """)
    
    # =========================================================================
    # STEP 8: Handle TimescaleDB sensor_readings hypertable
    # =========================================================================
    # 
    # TimescaleDB hypertables have restrictions on ALTER TABLE.
    # We add tenant_id but keep it nullable since changing to NOT NULL
    # on a hypertable requires special handling.
    #
    # Option 1 (simple): Add nullable column - chosen for safety
    # Option 2 (complex): Create new hypertable, migrate data, drop old
    #
    # For production, consider adding tenant_id to new readings only
    # and filtering by sensor -> dma -> tenant relationship for older data.
    # =========================================================================
    
    # Check if sensor_readings table exists before modifying
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sensor_readings') THEN
                -- Add tenant_id column if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'sensor_readings' AND column_name = 'tenant_id'
                ) THEN
                    ALTER TABLE sensor_readings ADD COLUMN tenant_id VARCHAR(50);
                END IF;
            END IF;
        END $$;
    """)
    
    print("✅ Multi-tenancy migration completed successfully!")
    print(f"   - Created tenants table with default tenant: {DEFAULT_TENANT_ID}")
    print("   - Created tenant_users table")
    print("   - Added tenant_id to: dmas, sensors, alerts, work_orders, audit_logs")
    print("   - Backfilled all existing data with default tenant")
    print("   - Linked existing users to default tenant")


def downgrade() -> None:
    """
    Remove multi-tenancy support.
    
    WARNING: This will DELETE all tenant data and relationships!
    """
    
    # =========================================================================
    # STEP 1: Remove tenant_id from sensor_readings (if exists)
    # =========================================================================
    
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'sensor_readings' AND column_name = 'tenant_id'
            ) THEN
                ALTER TABLE sensor_readings DROP COLUMN tenant_id;
            END IF;
        END $$;
    """)
    
    # =========================================================================
    # STEP 2: Remove tenant_id from existing tables
    # =========================================================================
    
    # Audit logs
    op.drop_index('ix_audit_logs_tenant_id', table_name='audit_logs')
    op.drop_constraint('fk_audit_logs_tenant', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'tenant_id')
    
    # Work orders
    op.drop_index('ix_work_orders_tenant_id', table_name='work_orders')
    op.drop_constraint('fk_work_orders_tenant', 'work_orders', type_='foreignkey')
    op.drop_column('work_orders', 'tenant_id')
    
    # Alerts
    op.drop_index('ix_alerts_tenant_id', table_name='alerts')
    op.drop_constraint('fk_alerts_tenant', 'alerts', type_='foreignkey')
    op.drop_column('alerts', 'tenant_id')
    
    # Sensors
    op.drop_index('ix_sensors_tenant_id', table_name='sensors')
    op.drop_constraint('fk_sensors_tenant', 'sensors', type_='foreignkey')
    op.drop_column('sensors', 'tenant_id')
    
    # DMAs
    op.drop_index('ix_dmas_tenant_id', table_name='dmas')
    op.drop_constraint('fk_dmas_tenant', 'dmas', type_='foreignkey')
    op.drop_column('dmas', 'tenant_id')
    
    # =========================================================================
    # STEP 3: Drop tenant_users table
    # =========================================================================
    
    op.drop_index('ix_tenant_users_user', table_name='tenant_users')
    op.drop_index('ix_tenant_users_tenant', table_name='tenant_users')
    op.drop_table('tenant_users')
    
    # =========================================================================
    # STEP 4: Drop tenants table
    # =========================================================================
    
    op.drop_index('ix_tenants_plan', table_name='tenants')
    op.drop_index('ix_tenants_country', table_name='tenants')
    op.drop_table('tenants')
    
    # =========================================================================
    # STEP 5: Drop ENUM types
    # =========================================================================
    
    op.execute("DROP TYPE IF EXISTS tenantuserstatus;")
    op.execute("DROP TYPE IF EXISTS tenantrole;")
    op.execute("DROP TYPE IF EXISTS tenantplan;")
    
    print("⚠️ Multi-tenancy support removed. All tenant data has been deleted.")
