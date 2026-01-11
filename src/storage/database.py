"""
AquaWatch Database - PostgreSQL/TimescaleDB Integration
=======================================================
Database models and connection management for time-series data.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager
import json

# Database imports
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor, execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.dialects.postgresql import JSONB
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "aquawatch"
    user: str = "aquawatch"
    password: str = "aquawatch_secure_password"
    min_connections: int = 2
    max_connections: int = 10
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'aquawatch'),
            user=os.getenv('DB_USER', 'aquawatch'),
            password=os.getenv('DB_PASSWORD', 'aquawatch_secure_password'),
        )
    
    @property
    def connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


# =============================================================================
# CONNECTION POOL
# =============================================================================

class DatabasePool:
    """Manages PostgreSQL connection pool."""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig.from_env()
        self._pool = None
        self._engine = None
        self._Session = None
    
    def initialize(self):
        """Initialize the connection pool."""
        if not PSYCOPG2_AVAILABLE:
            print("⚠️ psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
        
        try:
            self._pool = pool.ThreadedConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            
            # Also initialize SQLAlchemy if available
            if SQLALCHEMY_AVAILABLE:
                self._engine = create_engine(self.config.connection_string)
                self._Session = sessionmaker(bind=self._engine)
            
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a cursor from a pooled connection."""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    @contextmanager
    def get_session(self):
        """Get SQLAlchemy session."""
        if not self._Session:
            raise RuntimeError("SQLAlchemy not initialized")
        
        session = self._Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close all connections."""
        if self._pool:
            self._pool.closeall()
        if self._engine:
            self._engine.dispose()


# =============================================================================
# SQLAlchemy MODELS
# =============================================================================

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class Device(Base):
        """ESP sensor device."""
        __tablename__ = 'devices'
        
        id = Column(Integer, primary_key=True)
        device_id = Column(String(50), unique=True, nullable=False, index=True)
        pipe_id = Column(String(50), nullable=False, index=True)
        location = Column(String(200))
        latitude = Column(Float)
        longitude = Column(Float)
        status = Column(String(20), default='offline')
        firmware_version = Column(String(20))
        last_seen = Column(DateTime)
        created_at = Column(DateTime, default=datetime.utcnow)
        config = Column(JSONB)
        
        readings = relationship("SensorReading", back_populates="device")
    
    class SensorReading(Base):
        """Time-series sensor reading (TimescaleDB hypertable)."""
        __tablename__ = 'sensor_readings'
        
        time = Column(DateTime, primary_key=True, index=True)
        device_id = Column(String(50), ForeignKey('devices.device_id'), primary_key=True)
        pipe_id = Column(String(50), nullable=False, index=True)
        pressure = Column(Float, nullable=False)
        flow = Column(Float, nullable=False)
        temperature = Column(Float)
        battery = Column(Float)
        rssi = Column(Integer)
        
        device = relationship("Device", back_populates="readings")
    
    class Alert(Base):
        """Anomaly alerts."""
        __tablename__ = 'alerts'
        
        id = Column(Integer, primary_key=True)
        alert_id = Column(String(50), unique=True, nullable=False)
        pipe_id = Column(String(50), nullable=False, index=True)
        device_id = Column(String(50))
        alert_type = Column(String(50), nullable=False)
        severity = Column(String(20), nullable=False)
        confidence = Column(Float)
        pressure = Column(Float)
        flow = Column(Float)
        expected_pressure = Column(Float)
        deviation = Column(Float)
        status = Column(String(20), default='active')
        acknowledged_by = Column(String(100))
        acknowledged_at = Column(DateTime)
        resolved_at = Column(DateTime)
        notes = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)
        details = Column(JSONB)
    
    class MaintenanceOrder(Base):
        """Work orders for field technicians."""
        __tablename__ = 'maintenance_orders'
        
        id = Column(Integer, primary_key=True)
        order_id = Column(String(50), unique=True, nullable=False)
        alert_id = Column(String(50), ForeignKey('alerts.alert_id'))
        pipe_id = Column(String(50), nullable=False)
        priority = Column(String(20), nullable=False)
        title = Column(String(200), nullable=False)
        description = Column(Text)
        assigned_to = Column(String(100))
        status = Column(String(20), default='pending')
        estimated_location = Column(String(200))
        latitude = Column(Float)
        longitude = Column(Float)
        created_at = Column(DateTime, default=datetime.utcnow)
        started_at = Column(DateTime)
        completed_at = Column(DateTime)
        findings = Column(Text)
        images = Column(JSONB)  # Array of image URLs


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

class SensorDataStore:
    """Operations for sensor data storage and retrieval."""
    
    def __init__(self, db_pool: DatabasePool):
        self.pool = db_pool
    
    def insert_reading(self, device_id: str, pipe_id: str, pressure: float, 
                      flow: float, temperature: float = None, battery: float = None,
                      rssi: int = None, timestamp: datetime = None):
        """Insert a sensor reading."""
        timestamp = timestamp or datetime.utcnow()
        
        with self.pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO sensor_readings 
                (time, device_id, pipe_id, pressure, flow, temperature, battery, rssi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (time, device_id) DO UPDATE SET
                    pressure = EXCLUDED.pressure,
                    flow = EXCLUDED.flow,
                    temperature = EXCLUDED.temperature,
                    battery = EXCLUDED.battery,
                    rssi = EXCLUDED.rssi
            """, (timestamp, device_id, pipe_id, pressure, flow, temperature, battery, rssi))
    
    def insert_readings_batch(self, readings: List[Dict]):
        """Insert multiple readings efficiently."""
        if not readings:
            return
        
        with self.pool.get_cursor() as cursor:
            values = [
                (
                    r.get('timestamp', datetime.utcnow()),
                    r['device_id'],
                    r['pipe_id'],
                    r['pressure'],
                    r['flow'],
                    r.get('temperature'),
                    r.get('battery'),
                    r.get('rssi')
                )
                for r in readings
            ]
            
            execute_values(cursor, """
                INSERT INTO sensor_readings 
                (time, device_id, pipe_id, pressure, flow, temperature, battery, rssi)
                VALUES %s
                ON CONFLICT (time, device_id) DO NOTHING
            """, values)
    
    def get_latest_readings(self, pipe_id: str = None, limit: int = 100) -> List[Dict]:
        """Get latest readings, optionally filtered by pipe."""
        with self.pool.get_cursor() as cursor:
            if pipe_id:
                cursor.execute("""
                    SELECT * FROM sensor_readings 
                    WHERE pipe_id = %s 
                    ORDER BY time DESC 
                    LIMIT %s
                """, (pipe_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM sensor_readings 
                    ORDER BY time DESC 
                    LIMIT %s
                """, (limit,))
            
            return cursor.fetchall()
    
    def get_readings_range(self, pipe_id: str, start_time: datetime, 
                          end_time: datetime) -> List[Dict]:
        """Get readings for a time range."""
        with self.pool.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sensor_readings 
                WHERE pipe_id = %s AND time >= %s AND time <= %s
                ORDER BY time ASC
            """, (pipe_id, start_time, end_time))
            
            return cursor.fetchall()
    
    def get_aggregated_readings(self, pipe_id: str, interval: str = '1 hour',
                               start_time: datetime = None) -> List[Dict]:
        """Get aggregated readings using TimescaleDB time_bucket."""
        start_time = start_time or (datetime.utcnow() - timedelta(days=7))
        
        with self.pool.get_cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    time_bucket(%s, time) AS bucket,
                    pipe_id,
                    AVG(pressure) as avg_pressure,
                    MIN(pressure) as min_pressure,
                    MAX(pressure) as max_pressure,
                    AVG(flow) as avg_flow,
                    COUNT(*) as reading_count
                FROM sensor_readings 
                WHERE pipe_id = %s AND time >= %s
                GROUP BY bucket, pipe_id
                ORDER BY bucket ASC
            """, (interval, pipe_id, start_time))
            
            return cursor.fetchall()


class AlertStore:
    """Operations for alert storage and management."""
    
    def __init__(self, db_pool: DatabasePool):
        self.pool = db_pool
    
    def create_alert(self, alert_data: Dict) -> str:
        """Create a new alert."""
        import uuid
        alert_id = alert_data.get('alert_id', f"ALT-{uuid.uuid4().hex[:8].upper()}")
        
        with self.pool.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO alerts 
                (alert_id, pipe_id, device_id, alert_type, severity, confidence,
                 pressure, flow, expected_pressure, deviation, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING alert_id
            """, (
                alert_id,
                alert_data['pipe_id'],
                alert_data.get('device_id'),
                alert_data['alert_type'],
                alert_data['severity'],
                alert_data.get('confidence'),
                alert_data.get('pressure'),
                alert_data.get('flow'),
                alert_data.get('expected_pressure'),
                alert_data.get('deviation'),
                json.dumps(alert_data.get('details', {}))
            ))
            
            return cursor.fetchone()['alert_id']
    
    def get_active_alerts(self, pipe_id: str = None) -> List[Dict]:
        """Get active alerts."""
        with self.pool.get_cursor() as cursor:
            if pipe_id:
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE status = 'active' AND pipe_id = %s
                    ORDER BY created_at DESC
                """, (pipe_id,))
            else:
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE status = 'active'
                    ORDER BY created_at DESC
                """)
            
            return cursor.fetchall()
    
    def acknowledge_alert(self, alert_id: str, user: str):
        """Acknowledge an alert."""
        with self.pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE alerts 
                SET status = 'acknowledged', 
                    acknowledged_by = %s, 
                    acknowledged_at = %s
                WHERE alert_id = %s
            """, (user, datetime.utcnow(), alert_id))
    
    def resolve_alert(self, alert_id: str, notes: str = None):
        """Resolve an alert."""
        with self.pool.get_cursor() as cursor:
            cursor.execute("""
                UPDATE alerts 
                SET status = 'resolved', 
                    resolved_at = %s,
                    notes = COALESCE(notes || E'\\n' || %s, %s)
                WHERE alert_id = %s
            """, (datetime.utcnow(), notes, notes, alert_id))


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

INIT_SQL = """
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    pipe_id VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    latitude FLOAT,
    longitude FLOAT,
    status VARCHAR(20) DEFAULT 'offline',
    firmware_version VARCHAR(20),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    config JSONB
);

CREATE INDEX IF NOT EXISTS idx_devices_pipe_id ON devices(pipe_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);

-- Sensor readings table (will be converted to hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMP NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    pipe_id VARCHAR(50) NOT NULL,
    pressure FLOAT NOT NULL,
    flow FLOAT NOT NULL,
    temperature FLOAT,
    battery FLOAT,
    rssi INTEGER,
    PRIMARY KEY (time, device_id)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_readings_pipe_id ON sensor_readings(pipe_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_readings_device_id ON sensor_readings(device_id, time DESC);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    pipe_id VARCHAR(50) NOT NULL,
    device_id VARCHAR(50),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence FLOAT,
    pressure FLOAT,
    flow FLOAT,
    expected_pressure FLOAT,
    deviation FLOAT,
    status VARCHAR(20) DEFAULT 'active',
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_pipe_id ON alerts(pipe_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Maintenance orders table
CREATE TABLE IF NOT EXISTS maintenance_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    alert_id VARCHAR(50) REFERENCES alerts(alert_id),
    pipe_id VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    estimated_location VARCHAR(200),
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    findings TEXT,
    images JSONB
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON maintenance_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_assigned ON maintenance_orders(assigned_to, status);

-- Enable compression for old data (TimescaleDB)
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days', if_not_exists => TRUE);

-- Create continuous aggregate for hourly stats
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    pipe_id,
    AVG(pressure) as avg_pressure,
    MIN(pressure) as min_pressure,
    MAX(pressure) as max_pressure,
    AVG(flow) as avg_flow,
    COUNT(*) as reading_count
FROM sensor_readings
GROUP BY hour, pipe_id;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('hourly_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);
"""


def initialize_database(config: DatabaseConfig = None):
    """Initialize the database schema."""
    config = config or DatabaseConfig.from_env()
    
    if not PSYCOPG2_AVAILABLE:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    try:
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Split and execute statements
        statements = [s.strip() for s in INIT_SQL.split(';') if s.strip()]
        
        for stmt in statements:
            try:
                cursor.execute(stmt)
                print(f"✅ Executed: {stmt[:50]}...")
            except Exception as e:
                print(f"⚠️ {stmt[:50]}... - {e}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("\n🗄️ AquaWatch Database Module")
    print("=" * 50)
    
    # Check dependencies
    print(f"\n📦 Dependencies:")
    print(f"   psycopg2: {'✅ Available' if PSYCOPG2_AVAILABLE else '❌ Not installed'}")
    print(f"   SQLAlchemy: {'✅ Available' if SQLALCHEMY_AVAILABLE else '❌ Not installed'}")
    
    if not PSYCOPG2_AVAILABLE:
        print("\n💡 Install with: pip install psycopg2-binary sqlalchemy")
    else:
        # Try to connect
        config = DatabaseConfig.from_env()
        print(f"\n🔌 Connecting to {config.host}:{config.port}/{config.database}...")
        
        pool = DatabasePool(config)
        if pool.initialize():
            print("✅ Connection successful!")
            
            # Initialize schema
            print("\n📋 Initializing schema...")
            initialize_database(config)
        else:
            print("❌ Connection failed. Check your PostgreSQL settings.")
    
    print("\n✅ Database module ready!")
