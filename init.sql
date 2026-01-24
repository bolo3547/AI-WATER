-- AquaWatch NRW - TimescaleDB initialization
-- Generated from src/storage/database.py (INIT_SQL)

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
