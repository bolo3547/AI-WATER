# System Architecture Document
# AquaWatch NRW - Non-Revenue Water Detection System

## IWA Water Balance Aligned Architecture

> **"Most AI systems detect anomalies; ours understands water networks, NRW categories, and utility operations."**

---

## 1. Introduction

### 1.1 Purpose
This document defines the complete system architecture for the AquaWatch NRW platform—an AI-powered decision-support system for detecting and localizing water leakage through pressure anomaly analysis, **aligned with the IWA (International Water Association) Water Balance framework**.

### 1.2 IWA Water Balance Framework
The system is designed around the IWA Water Balance methodology:

```
System Input Volume
├── Authorized Consumption
│   ├── Billed Metered Consumption
│   ├── Billed Unmetered Consumption
│   ├── Unbilled Metered Consumption
│   └── Unbilled Unmetered Consumption
└── Water Losses (NRW) ← PRIMARY DETECTION TARGET
    ├── Real Losses (Physical)
    │   ├── Leakage from transmission/distribution mains
    │   ├── Leakage from service connections
    │   └── Overflow at storage facilities
    └── Apparent Losses (Commercial)
        ├── Unauthorized consumption (theft)
        └── Customer meter inaccuracies
```

### 1.3 Scope
The system is designed for deployment in Zambia and South Africa, scaling from lab prototype to national infrastructure. It addresses the specific challenges of African utility environments: unreliable power, limited connectivity, resource constraints, and the need for cost-effective solutions.

### 1.4 Design Philosophy
- **IWA Alignment**: All outputs use water utility language (not generic anomaly detection)
- **First Principles Thinking**: Every component must justify its existence
- **Graceful Degradation**: System must function when components fail
- **Cost Efficiency**: Optimize sensor density and infrastructure costs
- **Human-in-the-Loop**: AI assists humans; it doesn't replace judgment

### 1.5 Key Differentiators
| Generic Anomaly Detection | AquaWatch NRW (IWA-Aligned) |
|---------------------------|----------------------------|
| "Anomaly detected" | "Real Loss - Distribution Main Leakage detected" |
| "Probability: 78%" | "Probability: 78%, Confidence: HIGH (MNF window)" |
| "Action: Investigate" | "Action: Acoustic survey in affected zone" |
| Time-agnostic | Night analysis (00:00-04:00) emphasized |
| Pressure-blind | Pressure-leakage relationship (N1 factor) |

---

## 2. System Layers

### 2.1 Layer 1: Field Layer

**Role**: Physical measurement of water network parameters

**Components**:
| Component | Specification | African Optimization |
|-----------|--------------|---------------------|
| Pressure Sensors | 0-16 bar, 0.1% accuracy, 4-20mA output | IP68 rated, corrosion-resistant |
| Flow Meters | Electromagnetic, ±0.5% accuracy | Battery backup, low-power mode |
| Power Supply | Solar panel + battery | 3-day autonomy without sun |
| Enclosure | IP66 rated cabinet | Vandal-resistant, lockable |

**Inputs**:
- Physical pressure from water pipes (via pressure taps)
- Flow rate from bulk meters

**Outputs**:
- Analog signal (4-20mA) or digital (RS485/Modbus)
- Typical range: 0.5 - 10 bar for distribution networks

**Sensor Selection Criteria**:
```
Minimum Requirements:
- Operating temperature: 0°C to 60°C
- Overpressure tolerance: 2x rated pressure
- Response time: <100ms
- Long-term stability: <0.1% drift/year
- MTBF: >100,000 hours
```

**Power Budget**:
```
Pressure sensor: 20mA @ 24V = 0.48W
Edge device: 1W average, 3W peak
Communication: 0.5W average (cellular)
Total: ~2W continuous
Solar sizing: 20W panel, 20Ah battery (3-day autonomy)
```

---

### 2.2 Layer 2: Edge Layer

**Role**: Local data processing, buffering, and preliminary analysis

**Technology Options**:

| Option | Use Case | Cost | Power |
|--------|----------|------|-------|
| ESP32 | Low-cost, simple deployments | $5-15 | 0.5W |
| Industrial RTU | Critical infrastructure | $200-500 | 2-5W |
| Raspberry Pi CM4 | Edge AI processing | $50-100 | 3-5W |

**Primary Choice: ESP32-S3 for scale deployments**

**Inputs**:
- Analog sensor signals (via ADC)
- Digital sensor data (via Modbus RTU)
- Local time (GPS or NTP synchronized)

**Outputs**:
- Timestamped sensor readings
- Local anomaly flags
- Device health metrics

**Edge Processing Functions**:
```python
# Implemented on edge device
1. Signal conditioning (filtering, calibration)
2. Data buffering (72 hours minimum)
3. Simple threshold checks
4. Data compression
5. Secure packaging for transmission
```

**Firmware Requirements**:
- Over-the-air (OTA) updates
- Watchdog timer for reliability
- Encrypted storage for credentials
- Local logging for debugging

---

### 2.3 Layer 3: Communication Layer

**Role**: Reliable data transmission from field to cloud

**Technology Matrix**:

| Technology | Range | Power | Cost/Month | Best For |
|------------|-------|-------|------------|----------|
| LoRaWAN | 15km rural, 3km urban | Very Low | $0-2 | Dense urban deployments |
| 2G/GPRS | Network coverage | Medium | $2-5 | Legacy compatibility |
| 4G LTE | Network coverage | High | $5-15 | High data rates |
| NB-IoT | Network coverage | Low | $1-3 | Low power, wide area |
| Satellite | Global | High | $20-50 | Remote areas |

**Primary Strategy for Zambia/South Africa**:
1. **Urban areas**: LoRaWAN with 4G backhaul
2. **Peri-urban**: NB-IoT where available, else 2G
3. **Rural**: Satellite for critical points only

**Protocol Stack**:
```
Application:  MQTT (QoS 1 for reliability)
Security:     TLS 1.3
Transport:    TCP (cellular) / UDP (LoRaWAN)
Network:      IP (cellular) / LoRaWAN
```

**Data Transmission Schedule**:
```yaml
Normal operation:
  interval: 15 minutes
  payload: ~100 bytes compressed
  daily_data: ~10 KB per sensor

Alert mode:
  interval: 1 minute
  trigger: threshold breach or anomaly
  
Offline resilience:
  buffer: 72 hours
  sync: automatic on reconnection
```

---

### 2.4 Layer 4: Data Ingestion Layer

**Role**: Receive, validate, and route incoming sensor data

**Technology**: Apache Kafka + Custom MQTT Bridge

**Architecture**:
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  MQTT Broker │────▶│  Ingestion   │────▶│    Kafka     │
│  (Mosquitto) │     │   Service    │     │   Cluster    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │  Validation │
                     │  • Schema   │
                     │  • Range    │
                     │  • Timestamp│
                     └─────────────┘
```

**Inputs**:
- Raw MQTT messages from edge devices
- HTTP POST from legacy systems (REST API)

**Outputs**:
- Validated records to Kafka topics
- Invalid records to dead-letter queue
- Metrics to monitoring system

**Validation Rules**:
```python
validation_rules = {
    'pressure': {
        'min': 0.0,      # bar
        'max': 20.0,     # bar
        'max_change_rate': 2.0,  # bar/minute
    },
    'timestamp': {
        'max_age': 3600,      # seconds
        'max_future': 60,      # seconds
    },
    'sensor_id': {
        'format': r'^[A-Z]{2}-\d{6}$',
        'must_exist': True,
    }
}
```

**Throughput Design**:
```
Target: 100,000 sensors @ 15-minute intervals
Peak load: ~7,000 messages/minute
Design capacity: 20,000 messages/minute (3x headroom)
```

---

### 2.5 Layer 5: Time-Series Storage Layer

**Role**: Efficient storage and retrieval of sensor time-series data

**Primary Technology**: TimescaleDB (PostgreSQL extension)

**Why TimescaleDB**:
- Familiar PostgreSQL interface
- Automatic partitioning (hypertables)
- Compression (10-20x)
- Continuous aggregates
- Strong African PostgreSQL expertise availability

**Alternative for Scale**: QuestDB (higher write throughput)

**Schema Design**:
```sql
-- Hypertable for raw sensor data
CREATE TABLE sensor_readings (
    time        TIMESTAMPTZ NOT NULL,
    sensor_id   TEXT NOT NULL,
    pressure    DOUBLE PRECISION,
    flow        DOUBLE PRECISION,
    quality     SMALLINT DEFAULT 100,  -- 0-100 quality score
    PRIMARY KEY (time, sensor_id)
);

SELECT create_hypertable('sensor_readings', 'time');

-- Continuous aggregate for hourly summaries
CREATE MATERIALIZED VIEW sensor_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS hour,
    sensor_id,
    AVG(pressure) as avg_pressure,
    MIN(pressure) as min_pressure,
    MAX(pressure) as max_pressure,
    STDDEV(pressure) as stddev_pressure,
    COUNT(*) as sample_count
FROM sensor_readings
GROUP BY hour, sensor_id;
```

**Retention Policy**:
```yaml
raw_data: 90 days
hourly_aggregates: 2 years
daily_aggregates: 10 years
anomaly_events: forever
```

**Storage Estimates**:
```
Per sensor per day (raw): ~1 KB
Per sensor per day (compressed): ~100 bytes
100,000 sensors × 365 days × 100 bytes = 3.65 GB/year (compressed raw)
```

---

### 2.6 Layer 6: AI and Analytics Layer

**Role**: Detect anomalies, estimate leak probability, and localize issues

**Three-Layer AI Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI PROCESSING PIPELINE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────┐ │
│  │    LAYER 1      │    │    LAYER 2      │    │ LAYER 3 │ │
│  │    ANOMALY      │───▶│   PROBABILITY   │───▶│ LOCALIZE│ │
│  │   DETECTION     │    │   ESTIMATION    │    │         │ │
│  │                 │    │                 │    │         │ │
│  │ • Z-Score       │    │ • Random Forest │    │ • Graph │ │
│  │ • IQR           │    │ • XGBoost       │    │ • Bayes │ │
│  │ • Isolation     │    │ • Calibrated    │    │ • Rules │ │
│  │   Forest        │    │   Probability   │    │         │ │
│  │                 │    │                 │    │         │ │
│  │ Latency: <1s    │    │ Latency: <5s    │    │ <10s    │ │
│  │ Runs: Real-time │    │ Runs: 5-min     │    │ On-alert│ │
│  └─────────────────┘    └─────────────────┘    └─────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Layer 1: Real-Time Anomaly Detection**
- Input: Latest sensor reading + recent history
- Output: Anomaly score (0-1)
- Model: Isolation Forest (trained per DMA)
- Latency requirement: <1 second

**Layer 2: Leak Probability Estimation**
- Input: Anomaly scores + engineered features
- Output: Leak probability (0-1) with confidence interval
- Model: Calibrated XGBoost classifier
- Latency requirement: <5 seconds

**Layer 3: Localization and Prioritization**
- Input: Leak probabilities across network
- Output: Ranked list of segments/zones
- Method: Bayesian inference on network graph
- Latency requirement: <10 seconds

**Model Training Infrastructure**:
```yaml
training_schedule:
  anomaly_models: weekly (per DMA)
  probability_models: monthly (global)
  localization_models: quarterly

training_data:
  minimum_history: 30 days
  minimum_confirmed_leaks: 10 per DMA

model_storage:
  location: S3-compatible object storage
  versioning: enabled
  rollback: last 5 versions
```

---

### 2.7 Layer 7: Decision Support Layer

**Role**: Translate AI outputs into actionable recommendations

**Functions**:
1. Alert generation and routing
2. Severity classification
3. Work order creation
4. Priority queue management
5. Human feedback integration

**Alert Classification**:
```yaml
critical:
  threshold: probability > 0.9 AND estimated_loss > 100 m³/day
  response_time: 2 hours
  notification: SMS + Email + Dashboard

high:
  threshold: probability > 0.7 AND estimated_loss > 50 m³/day
  response_time: 24 hours
  notification: Email + Dashboard

medium:
  threshold: probability > 0.5
  response_time: 72 hours
  notification: Dashboard

low:
  threshold: probability > 0.3
  response_time: scheduled_maintenance
  notification: Weekly report
```

**Work Order Integration**:
```json
{
  "work_order_id": "WO-2026-00123",
  "created_at": "2026-01-05T10:30:00Z",
  "priority": "high",
  "type": "leak_investigation",
  "location": {
    "dma": "DMA-KIT-015",
    "segment": "SEG-4521",
    "description": "Main Road, between pump station and school"
  },
  "ai_summary": {
    "probability": 0.78,
    "confidence": 0.85,
    "estimated_loss": "75 m³/day",
    "key_evidence": [
      "Night pressure 15% below normal",
      "Pressure gradient increased 0.3 bar/km",
      "Similar pattern preceded confirmed leak in DMA-KIT-012"
    ]
  },
  "recommended_actions": [
    "Deploy acoustic logger at valve V-1234",
    "Check pressure at hydrant H-567",
    "Inspect visible pipe section near GPS: -15.4123, 28.2876"
  ]
}
```

---

### 2.8 Layer 8: Dashboard and Reporting Layer

**Role**: Visualize data and support human decision-making

**Technology**: Plotly Dash (Python-based, interactive)

**Three Dashboard Levels**:

**National/Ministry Dashboard**:
- NRW percentage by region (map view)
- Trend analysis (monthly, quarterly)
- Utility performance comparison
- Budget allocation recommendations

**Utility Operations Dashboard**:
- Real-time DMA status overview
- Active alerts and work orders
- Pressure/flow trends
- AI confidence indicators
- Performance metrics (detection rate, response time)

**Field Technician Dashboard** (Mobile-optimized):
- Active work orders
- Navigation to inspection points
- Data entry for field observations
- Photo upload for documentation
- Confirmation of repairs

**Design Principles**:
- Mobile-first for field use
- Offline capability for areas with poor connectivity
- Clear traffic-light indicators (red/yellow/green)
- Minimal cognitive load

---

## 3. Infrastructure Deployment

### 3.1 Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD INFRASTRUCTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   REGION    │  │   REGION    │  │   REGION    │         │
│  │   PRIMARY   │  │   BACKUP    │  │    EDGE     │         │
│  │  (Jo'burg)  │  │  (Cape Town)│  │   (Lusaka)  │         │
│  │             │  │             │  │             │         │
│  │ • Database  │  │ • Read      │  │ • Cache     │         │
│  │ • API       │  │   Replica   │  │ • Local API │         │
│  │ • AI        │  │ • Backup    │  │             │         │
│  │ • Dashboard │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  Cloud Provider: AWS Africa (Cape Town) or Azure South Afr │
│  Backup: Local data center for data sovereignty            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Containerization

All services deployed as Docker containers orchestrated by Kubernetes:

```yaml
services:
  - name: mqtt-broker
    replicas: 3
    resources:
      cpu: 2
      memory: 4Gi
    
  - name: ingestion-service
    replicas: 5
    autoscale: true
    
  - name: ai-service
    replicas: 3
    gpu: optional
    
  - name: dashboard
    replicas: 3
    
  - name: timescaledb
    replicas: 2  # Primary + standby
    storage: 1Ti
```

---

## 4. Reliability & Fault Tolerance

### 4.1 Failure Modes and Mitigations

| Failure | Impact | Mitigation |
|---------|--------|------------|
| Sensor failure | Data gap | Redundant sensors in critical locations |
| Edge device failure | No data from location | Local buffering, automatic restart |
| Network outage | Delayed data | 72-hour edge buffer, store-and-forward |
| Cloud service failure | No real-time alerts | Edge-based threshold alerts |
| Database failure | Data loss | Replication, hourly backups |
| AI model failure | No probability scores | Fall back to baseline rules |

### 4.2 Recovery Time Objectives

| Component | RTO | RPO |
|-----------|-----|-----|
| Dashboard | 5 minutes | 0 |
| API | 5 minutes | 0 |
| Database | 30 minutes | 1 hour |
| AI Service | 15 minutes | N/A |
| Edge Devices | Self-healing | 72 hours buffer |

---

## 5. Security Architecture

### 5.1 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                    SECURITY STACK                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Device Layer:                                          │
│  • Unique device certificates                           │
│  • Secure boot (where supported)                        │
│  • Encrypted credential storage                         │
│                                                         │
│  Communication Layer:                                   │
│  • TLS 1.3 for all connections                          │
│  • MQTT with client certificates                        │
│  • VPN for administrative access                        │
│                                                         │
│  Application Layer:                                     │
│  • Role-based access control (RBAC)                     │
│  • API key + JWT authentication                         │
│  • Audit logging                                        │
│                                                         │
│  Data Layer:                                            │
│  • Encryption at rest (AES-256)                         │
│  • Column-level encryption for PII                      │
│  • Automated backup encryption                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Access Control Matrix

| Role | Dashboard | API | Admin | Database |
|------|-----------|-----|-------|----------|
| Field Tech | View (limited) | None | None | None |
| Operator | View + Act | Read | None | None |
| Manager | Full | Read/Write | Limited | None |
| Admin | Full | Full | Full | Read |
| System | N/A | Full | Full | Full |

---

## 6. Cost Estimates

### 6.1 Per-Sensor Cost (Field Deployment)

| Item | Cost (USD) |
|------|------------|
| Pressure sensor | $100-200 |
| Edge device (ESP32) | $20 |
| Enclosure + mounting | $50 |
| Solar panel + battery | $80 |
| Installation labor | $100 |
| **Total per point** | **$350-450** |

### 6.2 Annual Operating Cost (per 1,000 sensors)

| Item | Annual Cost (USD) |
|------|-------------------|
| Connectivity (average) | $36,000 |
| Cloud infrastructure | $24,000 |
| Maintenance (10%) | $40,000 |
| Software licenses | $0 (open source) |
| **Total annual** | **$100,000** |
| **Per sensor/month** | **$8.33** |

---

## 7. Appendices

### Appendix A: Glossary

- **DMA**: District Metered Area - a discrete section of the water network
- **NRW**: Non-Revenue Water - water produced but not billed
- **RTU**: Remote Terminal Unit - industrial-grade edge device
- **Hypertable**: TimescaleDB's partitioned time-series table

### Appendix B: Reference Documents

1. IWA Water Loss Guidelines
2. AWWA M36 Water Audits and Loss Control Programs
3. TimescaleDB Best Practices
4. MQTT v5.0 Specification

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Classification: Internal Use*
