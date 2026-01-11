# AquaWatch NRW - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Database Installation](#database-installation)
4. [Application Deployment](#application-deployment)
5. [Edge Device Setup](#edge-device-setup)
6. [Scaling Strategy](#scaling-strategy)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

#### Central Server (Minimum)
| Component | Specification |
|-----------|--------------|
| CPU | 8 cores |
| RAM | 32 GB |
| Storage | 500 GB SSD |
| Network | 1 Gbps |

#### Production Deployment
| Component | Specification |
|-----------|--------------|
| CPU | 16+ cores |
| RAM | 64+ GB |
| Storage | 2 TB NVMe SSD |
| Network | 10 Gbps |

### Software Requirements
- Python 3.9+
- PostgreSQL 14+ with TimescaleDB 2.x
- Redis 6+
- Docker & Docker Compose
- Nginx (reverse proxy)

### Cloud Provider Options
- **AWS**: EC2 + RDS + ElastiCache
- **Azure**: VM + Azure Database + Redis Cache
- **On-Premise**: Recommended for data sovereignty

---

## Infrastructure Setup

### 1. Docker Compose (Development/Small Deployment)

```yaml
# docker-compose.yml
version: '3.8'

services:
  timescaledb:
    image: timescale/timescaledb:latest-pg14
    container_name: aquawatch-db
    environment:
      POSTGRES_USER: aquawatch
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: aquawatch
    volumes:
      - timescale_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aquawatch-redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  mqtt:
    image: eclipse-mosquitto:2
    container_name: aquawatch-mqtt
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
    ports:
      - "1883:1883"
      - "8883:8883"
    restart: unless-stopped

  app:
    build: .
    container_name: aquawatch-app
    environment:
      - AQUAWATCH_ENV=production
      - DB_HOST=timescaledb
      - DB_PASSWORD=${DB_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_HOST=redis
    depends_on:
      - timescaledb
      - redis
      - mqtt
    ports:
      - "8050:8050"
    restart: unless-stopped

volumes:
  timescale_data:
  redis_data:
```

### 2. Start Services

```bash
# Create environment file
cat > .env << EOF
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
EOF

# Start all services
docker-compose up -d

# Verify services
docker-compose ps
```

---

## Database Installation

### 1. TimescaleDB Setup

```sql
-- Connect to PostgreSQL
psql -U aquawatch -d aquawatch

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertable for sensor readings
CREATE TABLE sensor_readings (
    reading_id BIGSERIAL,
    sensor_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    pressure_bar FLOAT NOT NULL,
    flow_rate_m3h FLOAT,
    temperature_c FLOAT,
    battery_percent FLOAT,
    signal_strength INT,
    PRIMARY KEY (sensor_id, timestamp)
);

SELECT create_hypertable(
    'sensor_readings',
    'timestamp',
    chunk_time_interval => INTERVAL '1 day'
);

-- Enable compression
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_id'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

-- Create retention policy (1 year)
SELECT add_retention_policy('sensor_readings', INTERVAL '365 days');

-- Create continuous aggregate for hourly summaries
CREATE MATERIALIZED VIEW sensor_hourly
WITH (timescaledb.continuous) AS
SELECT
    sensor_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(pressure_bar) AS avg_pressure,
    MIN(pressure_bar) AS min_pressure,
    MAX(pressure_bar) AS max_pressure,
    STDDEV(pressure_bar) AS std_pressure,
    COUNT(*) AS reading_count
FROM sensor_readings
GROUP BY sensor_id, time_bucket('1 hour', timestamp);

-- Add refresh policy
SELECT add_continuous_aggregate_policy('sensor_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

### 2. Create Indexes

```sql
-- Index for time-range queries
CREATE INDEX idx_readings_sensor_time 
ON sensor_readings (sensor_id, timestamp DESC);

-- Index for anomaly queries
CREATE INDEX idx_readings_pressure 
ON sensor_readings (pressure_bar)
WHERE pressure_bar < 2.0 OR pressure_bar > 8.0;

-- Index for alerts
CREATE INDEX idx_alerts_status 
ON alerts (status, severity, timestamp DESC)
WHERE status IN ('new', 'acknowledged');
```

---

## Application Deployment

### 1. Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m appuser
USER appuser

# Expose port
EXPOSE 8050

# Run application
CMD ["python", "-m", "src.dashboard.app"]
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/aquawatch
upstream aquawatch {
    server 127.0.0.1:8050;
}

server {
    listen 80;
    server_name aquawatch.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aquawatch.example.com;

    ssl_certificate /etc/letsencrypt/live/aquawatch.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aquawatch.example.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://aquawatch;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Systemd Service

```ini
# /etc/systemd/system/aquawatch.service
[Unit]
Description=AquaWatch NRW Detection Service
After=network.target postgresql.service

[Service]
Type=simple
User=aquawatch
Group=aquawatch
WorkingDirectory=/opt/aquawatch
Environment="AQUAWATCH_ENV=production"
EnvironmentFile=/etc/aquawatch/env
ExecStart=/opt/aquawatch/venv/bin/python -m src.dashboard.app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Edge Device Setup

### 1. Raspberry Pi Edge Controller

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip libpq-dev mosquitto-clients

# Install Python packages
pip3 install paho-mqtt psutil schedule

# Create edge service
sudo cat > /etc/systemd/system/aquawatch-edge.service << EOF
[Unit]
Description=AquaWatch Edge Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/aquawatch-edge
ExecStart=/usr/bin/python3 edge_controller.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable aquawatch-edge
sudo systemctl start aquawatch-edge
```

### 2. Edge Controller Script

```python
#!/usr/bin/env python3
"""
Edge controller for offline buffering and data upload.
"""

import paho.mqtt.client as mqtt
import json
import sqlite3
import time
import schedule
from datetime import datetime

# Configuration
MQTT_BROKER = "central-server.example.com"
MQTT_PORT = 8883
DEVICE_ID = "EDGE-001"

# Local buffer database
def init_buffer():
    conn = sqlite3.connect('/var/lib/aquawatch/buffer.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS readings
                    (id INTEGER PRIMARY KEY, 
                     sensor_id TEXT,
                     timestamp TEXT,
                     data TEXT,
                     uploaded INTEGER DEFAULT 0)''')
    return conn

def store_reading(conn, sensor_id, data):
    """Store reading in local buffer."""
    conn.execute(
        "INSERT INTO readings (sensor_id, timestamp, data) VALUES (?, ?, ?)",
        (sensor_id, datetime.now().isoformat(), json.dumps(data))
    )
    conn.commit()

def upload_buffered(conn, client):
    """Upload buffered readings when connected."""
    cursor = conn.execute(
        "SELECT id, sensor_id, timestamp, data FROM readings WHERE uploaded = 0 LIMIT 100"
    )
    
    for row in cursor:
        try:
            payload = {
                "sensor_id": row[1],
                "timestamp": row[2],
                "data": json.loads(row[3])
            }
            client.publish(f"sensors/{row[1]}/readings", json.dumps(payload))
            conn.execute("UPDATE readings SET uploaded = 1 WHERE id = ?", (row[0],))
        except Exception as e:
            print(f"Upload error: {e}")
    
    conn.commit()

def main():
    conn = init_buffer()
    client = mqtt.Client()
    
    # TLS configuration
    client.tls_set()
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        
        # Schedule buffer upload
        schedule.every(5).minutes.do(upload_buffered, conn, client)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except Exception as e:
        print(f"Connection error: {e}")
        # Continue in offline mode

if __name__ == "__main__":
    main()
```

---

## Scaling Strategy

### Phase 1: Pilot (1-5 DMAs, ~50 sensors)
- Single server deployment
- Local database
- Manual model training

### Phase 2: Utility-Wide (20+ DMAs, ~200 sensors)
- Database replication
- Redis cluster for caching
- Automated model retraining

### Phase 3: National (100+ DMAs, 1000+ sensors)
- Kubernetes deployment
- Distributed processing (Apache Spark)
- Multi-region failover

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aquawatch-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aquawatch
  template:
    metadata:
      labels:
        app: aquawatch
    spec:
      containers:
      - name: app
        image: aquawatch:latest
        ports:
        - containerPort: 8050
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: aquawatch-secrets
              key: db-password
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aquawatch-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aquawatch-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring

### 1. Prometheus Metrics

```python
# Add to application
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
READINGS_PROCESSED = Counter('readings_processed_total', 'Total sensor readings processed')
ANOMALIES_DETECTED = Counter('anomalies_detected_total', 'Total anomalies detected')
PROCESSING_TIME = Histogram('processing_seconds', 'Time spent processing readings')
ACTIVE_ALERTS = Gauge('active_alerts', 'Number of active alerts', ['severity'])

# Start metrics server
start_http_server(9090)
```

### 2. Grafana Dashboard

Import dashboard for:
- Sensor reading rates
- Anomaly detection performance
- Alert response times
- System resource usage

### 3. Log Aggregation

```yaml
# Filebeat configuration
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

---

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check Python memory
ps aux --sort=-%mem | head
# Clear Redis cache
redis-cli FLUSHDB
```

#### 2. Database Connection Issues
```bash
# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='aquawatch';"
# Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname='aquawatch' AND state='idle' AND query_start < now() - interval '1 hour';
```

#### 3. MQTT Connection Drops
```bash
# Check mosquitto logs
journalctl -u mosquitto -f
# Test connection
mosquitto_sub -h localhost -t "sensors/#" -v
```

#### 4. Model Performance Degradation
```bash
# Trigger model retraining
python -m src.ai.anomaly.detector --retrain
# Check model metrics
python -m src.ai.evaluator --report
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable TLS for all connections
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up backup schedule
- [ ] Configure rate limiting
- [ ] Enable MFA for admin accounts
- [ ] Review RBAC permissions
- [ ] Test disaster recovery
- [ ] Schedule security audits

---

## Support

For deployment assistance:
- Email: support@aquawatch.africa
- Documentation: https://docs.aquawatch.africa
- GitHub Issues: https://github.com/aquawatch/nrw-detection
