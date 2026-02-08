"""
AquaWatch NRW - Database Handler for ESP32 Data
================================================

Stores sensor readings from ESP32 devices into TimescaleDB.
Implements time-series optimizations for water network data.
"""

import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# PostgreSQL/TimescaleDB
try:
    import psycopg2
    from psycopg2.extras import execute_batch
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)


def _parse_port(default: str = "5432") -> int:
    """Parse DB_PORT from environment with validation."""
    raw = os.getenv("DB_PORT", default)
    try:
        return int(raw)
    except ValueError:
        logger.warning(f"Invalid DB_PORT '{raw}', using default {default}")
        return int(default)


@dataclass  
class DatabaseConfig:
    """Database configuration."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = _parse_port()
    database: str = os.getenv("DB_NAME", "aquawatch")
    user: str = os.getenv("DB_USER", "aquawatch")
    password: str = os.getenv("DB_PASSWORD", "")
    schema: str = "nrw"


class TimescaleDBHandler:
    """
    Handles storage of ESP32 sensor data in TimescaleDB.
    
    TimescaleDB is PostgreSQL optimized for time-series data,
    perfect for high-frequency sensor readings.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.conn = None
        self.cursor = None
        
    def connect(self) -> bool:
        """Connect to TimescaleDB."""
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
            return False
            
        try:
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to TimescaleDB at {self.config.host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from TimescaleDB")
    
    def setup_schema(self):
        """Create database schema for ESP32 data."""
        schema_sql = f"""
        -- Create schema
        CREATE SCHEMA IF NOT EXISTS {self.config.schema};
        
        -- Sensor readings table (hypertable)
        CREATE TABLE IF NOT EXISTS {self.config.schema}.sensor_readings (
            time            TIMESTAMPTZ NOT NULL,
            device_id       TEXT NOT NULL,
            dma_id          TEXT,
            utility_id      TEXT,
            sensor_type     TEXT NOT NULL,
            value           DOUBLE PRECISION NOT NULL,
            unit            TEXT,
            quality         TEXT DEFAULT 'good',
            battery_pct     REAL,
            signal_strength INTEGER,
            sequence_num    BIGINT
        );
        
        -- Convert to hypertable if not already
        SELECT create_hypertable(
            '{self.config.schema}.sensor_readings', 
            'time',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 day'
        );
        
        -- Device status table
        CREATE TABLE IF NOT EXISTS {self.config.schema}.device_status (
            time            TIMESTAMPTZ NOT NULL,
            device_id       TEXT NOT NULL,
            firmware        TEXT,
            uptime_sec      INTEGER,
            free_heap       INTEGER,
            wifi_rssi       INTEGER,
            battery_voltage REAL,
            battery_pct     REAL,
            readings_sent   BIGINT,
            errors_count    INTEGER
        );
        
        SELECT create_hypertable(
            '{self.config.schema}.device_status',
            'time',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 day'
        );
        
        -- Alerts table
        CREATE TABLE IF NOT EXISTS {self.config.schema}.edge_alerts (
            time        TIMESTAMPTZ NOT NULL,
            alert_type  TEXT NOT NULL,
            device_id   TEXT NOT NULL,
            dma_id      TEXT,
            value       DOUBLE PRECISION,
            severity    REAL,
            acknowledged BOOLEAN DEFAULT FALSE,
            notes       TEXT
        );
        
        SELECT create_hypertable(
            '{self.config.schema}.edge_alerts',
            'time',
            if_not_exists => TRUE
        );
        
        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_readings_device 
            ON {self.config.schema}.sensor_readings (device_id, time DESC);
        CREATE INDEX IF NOT EXISTS idx_readings_dma 
            ON {self.config.schema}.sensor_readings (dma_id, time DESC);
        CREATE INDEX IF NOT EXISTS idx_readings_type
            ON {self.config.schema}.sensor_readings (sensor_type, time DESC);
            
        -- Continuous aggregates for dashboards
        CREATE MATERIALIZED VIEW IF NOT EXISTS {self.config.schema}.hourly_readings
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 hour', time) AS bucket,
            device_id,
            dma_id,
            sensor_type,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            COUNT(*) as reading_count
        FROM {self.config.schema}.sensor_readings
        GROUP BY bucket, device_id, dma_id, sensor_type;
        
        -- Compression policy (compress data older than 7 days)
        SELECT add_compression_policy(
            '{self.config.schema}.sensor_readings',
            INTERVAL '7 days',
            if_not_exists => TRUE
        );
        
        -- Retention policy (keep 2 years of data)
        SELECT add_retention_policy(
            '{self.config.schema}.sensor_readings',
            INTERVAL '2 years',
            if_not_exists => TRUE
        );
        """
        
        try:
            # Execute each statement separately
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        self.cursor.execute(statement)
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            logger.warning(f"Schema statement warning: {e}")
            
            self.conn.commit()
            logger.info("Database schema created/updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            self.conn.rollback()
            return False
    
    def insert_reading(self, reading) -> bool:
        """Insert single sensor reading."""
        sql = f"""
        INSERT INTO {self.config.schema}.sensor_readings 
        (time, device_id, dma_id, utility_id, sensor_type, value, unit, 
         quality, battery_pct, signal_strength, sequence_num)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self.cursor.execute(sql, (
                reading.timestamp,
                reading.device_id,
                reading.dma_id,
                reading.utility_id,
                reading.sensor_type.value,
                reading.value,
                reading.unit,
                reading.quality.value,
                reading.battery_pct,
                reading.signal_strength,
                reading.sequence_num
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to insert reading: {e}")
            self.conn.rollback()
            return False
    
    def insert_readings_batch(self, readings: list) -> int:
        """Insert batch of sensor readings (more efficient)."""
        sql = f"""
        INSERT INTO {self.config.schema}.sensor_readings 
        (time, device_id, dma_id, utility_id, sensor_type, value, unit, 
         quality, battery_pct, signal_strength, sequence_num)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            data = [
                (
                    r.timestamp, r.device_id, r.dma_id, r.utility_id,
                    r.sensor_type.value, r.value, r.unit, r.quality.value,
                    r.battery_pct, r.signal_strength, r.sequence_num
                )
                for r in readings
            ]
            
            execute_batch(self.cursor, sql, data, page_size=100)
            self.conn.commit()
            return len(readings)
        except Exception as e:
            logger.error(f"Failed to insert batch: {e}")
            self.conn.rollback()
            return 0
    
    def insert_device_status(self, status) -> bool:
        """Insert device status report."""
        sql = f"""
        INSERT INTO {self.config.schema}.device_status
        (time, device_id, firmware, uptime_sec, free_heap, wifi_rssi,
         battery_voltage, battery_pct, readings_sent, errors_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self.cursor.execute(sql, (
                status.timestamp,
                status.device_id,
                status.firmware_version,
                status.uptime_seconds,
                status.free_heap_bytes,
                status.wifi_rssi,
                status.battery_voltage,
                status.battery_pct,
                status.readings_sent,
                status.errors_count
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to insert device status: {e}")
            self.conn.rollback()
            return False
    
    def get_latest_readings(self, dma_id: str = None, limit: int = 100) -> List[Dict]:
        """Get latest sensor readings."""
        sql = f"""
        SELECT time, device_id, dma_id, sensor_type, value, unit, quality
        FROM {self.config.schema}.sensor_readings
        {'WHERE dma_id = %s' if dma_id else ''}
        ORDER BY time DESC
        LIMIT %s
        """
        
        try:
            if dma_id:
                self.cursor.execute(sql, (dma_id, limit))
            else:
                self.cursor.execute(sql.replace('WHERE dma_id = %s', ''), (limit,))
            
            columns = ['time', 'device_id', 'dma_id', 'sensor_type', 'value', 'unit', 'quality']
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get readings: {e}")
            return []
    
    def get_hourly_stats(self, dma_id: str, hours: int = 24) -> List[Dict]:
        """Get hourly aggregated statistics."""
        sql = f"""
        SELECT bucket, device_id, sensor_type, avg_value, min_value, max_value, reading_count
        FROM {self.config.schema}.hourly_readings
        WHERE dma_id = %s AND bucket > NOW() - INTERVAL '%s hours'
        ORDER BY bucket DESC
        """
        
        try:
            self.cursor.execute(sql, (dma_id, hours))
            columns = ['bucket', 'device_id', 'sensor_type', 'avg_value', 'min_value', 'max_value', 'reading_count']
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get hourly stats: {e}")
            return []


# =============================================================================
# INTEGRATION: ESP32 → Database
# =============================================================================

class ESP32DatabaseIntegration:
    """
    Integrates ESP32 data ingestion with TimescaleDB storage.
    """
    
    def __init__(self, mqtt_service, db_handler: TimescaleDBHandler):
        self.mqtt = mqtt_service
        self.db = db_handler
        self.batch_buffer = []
        self.batch_size = 50  # Insert in batches of 50
        
    def setup(self):
        """Set up integration callbacks."""
        self.mqtt.on_reading_received = self.handle_reading
        self.mqtt.on_device_status = self.handle_status
        
    def handle_reading(self, reading):
        """Handle incoming sensor reading."""
        self.batch_buffer.append(reading)
        
        # Batch insert when buffer is full
        if len(self.batch_buffer) >= self.batch_size:
            count = self.db.insert_readings_batch(self.batch_buffer)
            logger.info(f"Inserted batch of {count} readings")
            self.batch_buffer = []
    
    def handle_status(self, status):
        """Handle device status report."""
        self.db.insert_device_status(status)
        
    def flush(self):
        """Flush remaining buffered readings."""
        if self.batch_buffer:
            self.db.insert_readings_batch(self.batch_buffer)
            self.batch_buffer = []


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create database handler
    config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "aquawatch"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    
    db = TimescaleDBHandler(config)
    
    if db.connect():
        print("Creating database schema...")
        db.setup_schema()
        
        print("Database ready for ESP32 data!")
        db.disconnect()
