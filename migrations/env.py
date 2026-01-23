"""
Alembic Environment Configuration - LWSC NRW Detection System
==============================================================
Handles database migrations with TimescaleDB hypertable support.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src directory to path for model imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Import models for autogenerate support
from src.storage.models import Base

# this is the Alembic Config object
config = context.config

# Get database URL from environment or use defaults
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'aquawatch')
DB_USER = os.environ.get('DB_USER', 'aquawatch')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'aquawatch_secure_password')

# Build connection URL
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

# Override the sqlalchemy.url from alembic.ini
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a 
    connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Compare types for better autogenerate
            compare_type=True,
            # Don't drop tables that TimescaleDB creates
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function to exclude TimescaleDB internal objects from autogenerate.
    """
    # Exclude TimescaleDB internal schemas and tables
    if type_ == "table":
        # Skip TimescaleDB internal tables
        if name.startswith('_timescaledb') or name.startswith('chunk_'):
            return False
        # Skip continuous aggregates (materialized views)
        if name.endswith('_hourly') or name.endswith('_daily'):
            return False
    
    return True


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
