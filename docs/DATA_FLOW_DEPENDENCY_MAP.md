# AquaWatch NRW Detection System - Complete Data Flow & Dependency Map

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AQUAWATCH NRW DATA FLOW ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  ESP32/IoT   │───▶│  Ingestion   │───▶│   Storage    │───▶│  AI Models   │      │
│  │   Sensors    │    │   Layer      │    │   Layer      │    │   Layer      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │                   │              │
│         │                   │                   │                   ▼              │
│         │                   │                   │            ┌──────────────┐      │
│         │                   │                   │            │   Decision   │      │
│         │                   │                   │            │   Engine     │      │
│         │                   │                   │            └──────────────┘      │
│         │                   │                   │                   │              │
│         │                   │                   │                   ▼              │
│         │                   │                   │            ┌──────────────┐      │
│         │                   │                   └───────────▶│  Dashboard   │      │
│         │                   │                                │    Layer     │      │
│         │                   │                                └──────────────┘      │
│         │                   │                                       │              │
│         │                   │                                       ▼              │
│         │                   │                   ┌──────────────┐    │              │
│         │                   │                   │ Notifications│◀───┘              │
│         │                   │                   │  & Workflow  │                   │
│         │                   │                   └──────────────┘                   │
│         │                   │                          │                           │
│         │                   │                          ▼                           │
│         │                   │                   ┌──────────────┐                   │
│         │                   │                   │   Feedback   │                   │
│         └───────────────────┴───────────────────│     Loop     │──────────────────▶│
│                                                 └──────────────┘   (to AI Models)  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. DATA INGESTION LAYER

### Entry Points Identified:

#### 1.1 ESP32 MQTT Connector
**File:** [src/iot/esp32_connector.py](../src/iot/esp32_connector.py)
**Status:** ✅ ACTIVELY INTEGRATED

| Component | Description |
|-----------|-------------|
| `MQTTIngestionService` | Subscribes to MQTT topics for real-time sensor data |
| `ESP32DataIngestionService` | Combined MQTT + REST API ingestion |
| `SensorReading` | Data class for sensor readings |

**Input Sources:**
- MQTT Topics: `aquawatch/{utility_id}/{dma_id}/sensors/{sensor_id}/{type}`
- Types: `pressure`, `flow`, `level`, `status`
- Format: JSON or Binary (24 bytes with CRC)

**Output Destinations:**
- → `TimescaleDBHandler` for storage
- → Callbacks: `on_reading_received`, `on_device_status`, `on_alert`
- → `integrated_api.py` for processing

**Data Format:**
```python
SensorReading:
  - device_id: str
  - sensor_type: SensorType (pressure/flow/level/quality)
  - timestamp: datetime
  - value: float
  - unit: str
  - quality: DataQuality (good/suspect/bad/stale)
  - battery_pct: Optional[float]
  - signal_strength: Optional[int]
  - dma_id: str
  - utility_id: str
```

---

#### 1.2 REST API (HTTP) Entry Points
**File:** [src/api/sensor_api.py](../src/api/sensor_api.py)
**Status:** ✅ ACTIVELY USED

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sensor` | POST | ESP32 sends pressure/flow readings |
| `/api/sensor` | GET | Dashboard fetches latest readings |
| `/api/pipes` | GET | Get all pipe statuses by location |
| `/api/history` | GET | Get sensor reading history |

**Input Format:**
```json
{
  "pipe_id": "Pipe_A1",
  "pressure": 45.2,
  "flow": 12.5,
  "device_id": "ESP32_001"
}
```

**Output:** JSON stored to `sensor_data.json`

---

#### 1.3 Integrated API (Main Entry)
**File:** [src/api/integrated_api.py](../src/api/integrated_api.py)
**Status:** ✅ PRIMARY INTEGRATION POINT

**Imports & Dependencies:**
- `src.ai.anomaly_detector` → AnomalyDetectionEngine
- `src.security.auth` → TokenManager, PasswordManager
- `src.workflow.engine` → WorkflowEngine
- `src.notifications.alerting` → NotificationService, EscalationManager
- `src.storage.database` → DatabasePool, SensorDataStore, AlertStore

**Processing Pipeline:**
```
POST /api/sensor → process_sensor_reading()
  1. Store reading (JSON/DB)
  2. Update PressureBaseline
  3. Run AnomalyDetectionEngine.process_reading()
  4. Create Alert if anomaly detected
  5. Send notifications for critical alerts
```

---

#### 1.4 SIV Manager (System Input Volume)
**File:** [src/siv/siv_manager.py](../src/siv/siv_manager.py)
**Status:** ✅ ACTIVELY INTEGRATED

| Entry Method | Purpose |
|--------------|---------|
| `ingest_siv()` | API ingestion of SIV data |
| `ingest_siv_csv()` | CSV batch import |
| `ingest_siv_scada()` | SCADA system integration |

**Data Class:**
```python
SIVRecord:
  - record_id: str
  - source_id: str
  - timestamp: datetime
  - volume_m3: float
  - flow_rate_m3_hour: float
  - quality: DataQuality
  - ingestion_method: str (api/csv/scada/manual)
```

**Output Destinations:**
- → `NRWCalculator` for water balance
- → `IntegratedNRWService` for unified processing

---

#### 1.5 ESP32 Firmware (Edge Device)
**File:** [firmware/aquawatch_sensor/aquawatch_sensor.ino](../firmware/aquawatch_sensor/aquawatch_sensor.ino)
**Status:** ✅ REFERENCE IMPLEMENTATION

**Sensors Supported:**
- Flow meter (pulse-based, 450 pulses/liter)
- Pressure sensor (4-20mA analog)
- Ultrasonic level sensor
- Water quality (pH, turbidity, chlorine)
- Temperature
- Battery/solar monitoring

**Data Output:**
```cpp
MQTT Topic: aquawatch/{utility}/{dma}/sensors/{device}/pressure
JSON Format: {
  "device_id": "SENSOR_NODE_001",
  "dma_id": "DMA_NORTH_01",
  "pressure_bar": 4.5,
  "flow_lpm": 12.3,
  "timestamp": "2026-01-16T10:30:00Z",
  "battery_pct": 85,
  "signal_strength": -65
}
```

---

## 2. DATABASE/STORAGE LAYER

### 2.1 TimescaleDB Handler
**File:** [src/iot/database_handler.py](../src/iot/database_handler.py)
**Status:** ✅ IMPLEMENTED

**Tables (Hypertables):**
- `nrw.sensor_readings` - Time-series sensor data
- `nrw.device_status` - Device health metrics
- `nrw.edge_alerts` - Edge-detected alerts

**Schema:**
```sql
sensor_readings:
  - time: TIMESTAMPTZ (partition key)
  - device_id: TEXT
  - dma_id: TEXT
  - sensor_type: TEXT
  - value: DOUBLE PRECISION
  - quality: TEXT
  - battery_pct: REAL
```

---

### 2.2 Main Database Module
**File:** [src/storage/database.py](../src/storage/database.py)
**Status:** ✅ IMPLEMENTED (Optional - falls back to JSON)

**Components:**
- `DatabasePool` - PostgreSQL connection pool
- `SensorDataStore` - CRUD for sensor readings
- `AlertStore` - CRUD for alerts

---

### 2.3 SQLAlchemy Models
**File:** [src/storage/models.py](../src/storage/models.py)
**Status:** ⚠️ DEFINED BUT NOT FULLY CONNECTED

**Entities:**
- `Country`, `Utility`, `DMA` - Organization hierarchy
- `Pipe`, `Sensor`, `MeterReading` - Infrastructure
- `Alert`, `WorkOrder`, `FieldFeedback` - Operations
- `User`, `Role`, `AuditLog` - Security

---

### 2.4 JSON File Storage (Fallback)
**Files:**
- `src/api/sensor_data.json` - Current sensor readings
- `src/api/devices.json` - Device registry
- `src/api/alerts_store.json` - Alerts

**Status:** ✅ ACTIVELY USED as fallback when DB unavailable

---

## 3. FEATURE ENGINEERING LAYER

### 3.1 Feature Engineering Pipeline
**File:** [src/features/feature_engineering.py](../src/features/feature_engineering.py)
**Status:** ✅ IMPLEMENTED

**Main Class:** `FeatureEngineer`

**Input:** Raw pressure/flow DataFrames
**Output:** `SensorFeatures` object with computed features

**Feature Categories:**

| Category | Features | Physical Meaning |
|----------|----------|------------------|
| Absolute | mean, std, min, max, range | Operating point characteristics |
| Temporal | rate_of_change, acceleration | Sudden vs gradual changes |
| Contextual | hour, is_weekend, is_night | Time-of-day patterns |
| Statistical | zscore, percentile, kurtosis | Anomaly indicators |
| Night (MNF) | mnf_mean, mnf_deviation | IWA Minimum Night Flow analysis |
| Relative | neighbor_delta, gradient | Spatial patterns |
| Derived | leak_score_composite | Combined leak probability |

**IWA Alignment:**
- Night window: 00:00-04:00 (HIGH CONFIDENCE)
- MNF legitimate flow: 1.7 L/property/night
- Background leakage allowance: 5% of average day flow

---

## 4. AI MODELS LAYER

### 4.1 Anomaly Detection Engine
**File:** [src/ai/anomaly_detector.py](../src/ai/anomaly_detector.py)
**Status:** ✅ ACTIVELY INTEGRATED

**Classes:**
| Class | Purpose | ML Method |
|-------|---------|-----------|
| `PressureBaseline` | Learn hourly pressure patterns | Statistical (rolling window) |
| `StatisticalDetector` | Z-score and IQR detection | Statistical |
| `IsolationForestDetector` | Multivariate anomalies | Isolation Forest (sklearn) |
| `AnomalyDetectionEngine` | Main orchestrator | Ensemble |

**Input:**
```python
process_reading(pipe_id, pressure, flow, timestamp)
```

**Output:**
```python
AnomalyResult:
  - pipe_id: str
  - timestamp: datetime
  - anomaly_type: AnomalyType (NORMAL/PRESSURE_DROP/LEAK_SUSPECTED/etc)
  - confidence: float (0-1)
  - severity: str (low/medium/high/critical)
  - expected_pressure: float
  - deviation: float
```

---

### 4.2 Time Series Forecasting
**File:** [src/ai/time_series_forecasting.py](../src/ai/time_series_forecasting.py)
**Status:** ✅ IMPLEMENTED

**Components:**
| Forecaster | Library | Purpose |
|------------|---------|---------|
| `STLAnomalyDetector` | statsmodels | Seasonal-Trend decomposition |
| `ProphetForecaster` | prophet | Interpretable forecasting |
| `LSTMForecaster` | tensorflow | Deep learning sequences |
| `EnsembleForecaster` | Combined | Weighted ensemble |

**Output:** `ForecastResult` with predicted values, confidence intervals, anomaly flags

---

### 4.3 Baseline Comparison Service
**File:** [src/ai/baseline_comparison.py](../src/ai/baseline_comparison.py)
**Status:** ✅ ACTIVELY INTEGRATED

**Purpose:** Compare STL statistical baseline vs AI predictions

**Output:**
```python
ComparisonResult:
  - verdict: ComparisonVerdict (BOTH_AGREE_NORMAL/BOTH_AGREE_ANOMALY/AI_ONLY/etc)
  - prediction_delta_percent: float
  - agreement_score: float (0-1)
  - explanation: str
```

**Drift Detection:**
```python
DriftMetrics:
  - mean_prediction_delta: float
  - agreement_rate: float
  - drift_severity: DriftSeverity
```

---

### 4.4 Leak Localizer
**File:** [src/ai/leak_localizer.py](../src/ai/leak_localizer.py)
**Status:** ✅ IMPLEMENTED

**Techniques:**
- Pressure wave analysis
- Network topology constraints
- Multi-sensor correlation

**Input:** `NetworkTopology` + pressure readings from multiple sensors
**Output:** `LeakLocation` with segment_id, confidence, probability_map

---

### 4.5 Continuous Learning Pipeline
**File:** [src/ai/continuous_learning.py](../src/ai/continuous_learning.py)
**Status:** ✅ IMPLEMENTED

**Purpose:** Feedback loop for model improvement

**Components:**
- `FieldFeedback` - Store field confirmation labels
- `ModelPerformanceSnapshot` - Track metrics over time
- `ContinuousLearningController` - Orchestrate retraining

**Model Lifecycle:**
```
INITIAL → LEARNING → READY_TO_TRAIN → SUPERVISED → RETRAINING
                                          ↓
                                   DRIFT_DETECTED
```

**Triggers:**
- Minimum labels threshold (100 labels, 30 positive)
- Baseline drift detection
- Performance degradation

---

## 5. DECISION ENGINE

### 5.1 Central Decision Engine
**File:** [src/ai/decision_engine.py](../src/ai/decision_engine.py)
**Status:** ✅ ACTIVELY INTEGRATED (LOCKED FORMULA)

**LOCKED DECISION FORMULA:**
```
Priority Score = (leak_probability × estimated_loss_m3_day)
                × criticality_factor
                × confidence_factor
```

**Input:**
```python
score_dma(
  leak_probability: float,      # 0-1 from AI
  estimated_loss_m3_day: float, # m³/day
  criticality_factor: float,    # 0-2 (pipe age, material, population)
  confidence_factor: float,     # 0-1 AI confidence
)
```

**Output:**
```python
DMAPriorityScore:
  - priority_score: float (0-100)
  - rank: int
  - recommended_intervention: InterventionType
  - urgency: UrgencyLevel (IMMEDIATE/SAME_DAY/NEXT_48H/etc)
  - explanation: str
  - contributing_factors: List[str]
```

---

### 5.2 NRW Calculator
**File:** [src/nrw/nrw_calculator.py](../src/nrw/nrw_calculator.py)
**Status:** ✅ ACTIVELY INTEGRATED

**IWA Water Balance Formula:**
```
NRW = System Input Volume - Billed Authorized - Unbilled Authorized
NRW = Real Losses + Apparent Losses
```

**Input:** SIV data + billing data
**Output:**
```python
NRWResult:
  - nrw_m3: float
  - nrw_percent: float
  - real_losses_m3: float
  - apparent_losses_m3: float
  - ili: float (Infrastructure Leakage Index)
```

---

### 5.3 Integrated NRW Service
**File:** [src/api/integrated_nrw_api.py](../src/api/integrated_nrw_api.py)
**Status:** ✅ MAIN INTEGRATION POINT

**Integrates 5 Components:**
1. `SIVManager` - System Input Volume
2. `NRWCalculator` - Water balance
3. `DecisionEngine` - Priority scoring (LOCKED)
4. `BaselineComparisonService` - STL vs AI
5. `ContinuousLearningController` - Feedback loop

**Main Method:**
```python
process_dma_data(dma_id, timestamp, siv_m3, billed_m3, pressure_data, 
                 flow_data, leak_probability, ai_confidence)
  → Returns comprehensive result dict with all component outputs
```

---

## 6. ALERTS & NOTIFICATIONS

### 6.1 Alert Generator
**File:** [src/workflow/engine.py](../src/workflow/engine.py) (AlertGenerator class)
**Status:** ✅ IMPLEMENTED

**IWA Classification:**
- Night window: 00:00-04:00 (HIGH CONFIDENCE)
- Pressure risk zones: low (<2.5 bar), optimal (2.5-4), elevated (4-5), high (5-6), critical (>6)

**Alert Severity Mapping:**
| Probability | Time | Severity |
|-------------|------|----------|
| >0.9 | Any | CRITICAL |
| >0.75 | Night | HIGH |
| >0.75 | Day | MEDIUM |
| >0.5 | Any | LOW |

**Output:**
```python
Alert:
  - alert_id: str
  - dma_id: str
  - severity: AlertSeverity
  - nrw_category: NRWCategory (REAL_LOSS_LEAKAGE/APPARENT_LOSS_METER/etc)
  - estimated_loss_m3_day: float
  - key_evidence: List[str]
  - utility_summary: str
```

---

### 6.2 Notification Service
**File:** [src/notifications/alerting.py](../src/notifications/alerting.py)
**Status:** ✅ IMPLEMENTED

**Channels:**
| Channel | Provider | Region |
|---------|----------|--------|
| SMS | Africa's Talking | Kenya, Uganda, Tanzania |
| SMS | Twilio | Global |
| SMS | BulkSMS | South Africa |
| Email | SMTP/SendGrid | Global |
| Push | Firebase | Mobile apps |
| Webhook | HTTP | External systems |

**Message Templates:**
- Multi-language: English, Swahili, Zulu
- Alert types: leak_alert, work_order, escalation

---

### 6.3 Escalation Manager
**File:** [src/notifications/alerting.py](../src/notifications/alerting.py) (EscalationManager class)
**Status:** ✅ IMPLEMENTED

**Escalation Rules:**
- Time-based escalation
- Role hierarchy
- Multi-channel notifications

---

## 7. WORKFLOW ENGINE

### 7.1 Workflow Engine
**File:** [src/workflow/engine.py](../src/workflow/engine.py)
**Status:** ✅ IMPLEMENTED

**Components:**
- `AlertGenerator` - Create IWA-classified alerts
- `WorkOrderManager` - CRUD for work orders
- `EscalationEngine` - Time-based escalation
- `WorkflowEngine` - Main orchestrator

**Work Order Lifecycle:**
```
NEW → ACKNOWLEDGED → ASSIGNED → IN_PROGRESS → RESOLVED/FALSE_POSITIVE
```

---

### 7.2 Work Order Service
**File:** [src/workflow/work_orders.py](../src/workflow/work_orders.py)
**Status:** ✅ IMPLEMENTED

**Work Order Types:**
- LEAK_REPAIR, BURST_REPAIR
- METER_INSTALLATION/REPAIR/REPLACEMENT
- PRESSURE_CHECK, WATER_QUALITY_TEST
- PREVENTIVE_MAINTENANCE, INSPECTION

**Priority SLA:**
| Priority | Response Time | Completion Time |
|----------|---------------|-----------------|
| EMERGENCY | 1 hour | 4 hours |
| URGENT | 4 hours | 24 hours |
| HIGH | 24 hours | 48 hours |
| NORMAL | 48 hours | 1 week |

---

## 8. DASHBOARD LAYER

### 8.1 Main Dashboard
**File:** [src/dashboard/app.py](../src/dashboard/app.py)
**Status:** ✅ ACTIVELY USED

**Framework:** Dash + Plotly + Bootstrap

**API Connections:**
```python
API_BASE_URL = "http://127.0.0.1:5000"

fetch_sensor_data() → GET /api/sensor
fetch_alerts() → GET /api/alerts
fetch_history() → GET /api/history
fetch_system_status() → GET /api/status
```

**Three-tier Design:**
1. **National/Ministry** - Strategic overview
2. **Utility Operations** - Operational management
3. **Field Technician** - Mobile work orders

---

### 8.2 Additional Dashboards
| File | Purpose | Status |
|------|---------|--------|
| `monday_style_app.py` | Monday.com style UI | ✅ Available |
| `command_center.py` | Operations center | ✅ Available |
| `aquawatch_pro.py` | Premium features | ✅ Available |
| `world_class_dashboard.py` | Enterprise version | ✅ Available |

---

## 9. FEEDBACK LOOP

### 9.1 Field Feedback Integration
**File:** [src/ai/continuous_learning.py](../src/ai/continuous_learning.py)

**Feedback Types:**
```python
FeedbackType:
  - LEAK_CONFIRMED      # AI was right
  - LEAK_NEARBY         # Leak within 100m
  - NO_LEAK_FOUND       # False positive
  - OPERATIONAL_EVENT   # Valve operation
  - SENSOR_FAULT        # Sensor error
  - INCONCLUSIVE        # Needs more investigation
  - APPARENT_LOSS       # Commercial loss
  - BASELINE_DRIFT      # Triggered by drift
```

**Data Flow:**
```
Field Investigation → FieldFeedback → ContinuousLearningController
                                              ↓
                                      Store labels + features
                                              ↓
                                      Check retraining triggers
                                              ↓
                                      Retrain if needed
```

---

## 10. MODULE STATUS SUMMARY

### Actively Integrated (✅)
| Module | File | Called By |
|--------|------|-----------|
| ESP32 Connector | `src/iot/esp32_connector.py` | `run_system.py` |
| Integrated API | `src/api/integrated_api.py` | Flask server |
| Anomaly Detector | `src/ai/anomaly_detector.py` | `integrated_api.py` |
| Decision Engine | `src/ai/decision_engine.py` | `integrated_nrw_api.py` |
| NRW Calculator | `src/nrw/nrw_calculator.py` | `integrated_nrw_api.py` |
| SIV Manager | `src/siv/siv_manager.py` | `integrated_nrw_api.py` |
| Baseline Comparison | `src/ai/baseline_comparison.py` | `integrated_nrw_api.py` |
| Continuous Learning | `src/ai/continuous_learning.py` | `integrated_nrw_api.py` |
| Workflow Engine | `src/workflow/engine.py` | `integrated_api.py` |
| Notification Service | `src/notifications/alerting.py` | `integrated_api.py` |
| Dashboard | `src/dashboard/app.py` | Standalone / `run_system.py` |

### Implemented but Standalone (⚠️)
| Module | File | Notes |
|--------|------|-------|
| Feature Engineering | `src/features/feature_engineering.py` | Ready but needs explicit call |
| Leak Localizer | `src/ai/leak_localizer.py` | Needs network topology data |
| Time Series Forecasting | `src/ai/time_series_forecasting.py` | Used by BaselineComparison |
| Work Orders | `src/workflow/work_orders.py` | Separate from engine.py |
| SQLAlchemy Models | `src/storage/models.py` | Full ORM defined |
| Database Handler | `src/iot/database_handler.py` | TimescaleDB specific |

---

## 11. DATA FORMAT SUMMARY

### Sensor Reading Flow
```
ESP32 (JSON/Binary)
     ↓
MQTTIngestionService → SensorReading dataclass
     ↓
integrated_api.py → JSON storage + DB
     ↓
PressureBaseline → Updates hourly patterns
     ↓
AnomalyDetectionEngine → AnomalyResult
     ↓
AlertGenerator → Alert (IWA-classified)
     ↓
NotificationService → SMS/Email/Push
     ↓
WorkOrderManager → WorkOrder
     ↓
Field App → FieldFeedback
     ↓
ContinuousLearningController → Model improvement
```

### API Response Formats

**Sensor Data:**
```json
{
  "Pipe_A1": {
    "pressure": 45.2,
    "flow": 12.5,
    "status": "normal|warning|leak",
    "last_update": "2026-01-16T10:30:00",
    "location": "Lusaka Central"
  }
}
```

**Alert:**
```json
{
  "alert_id": "NRW-2026-000001",
  "dma_id": "DMA-KIT-001",
  "severity": "critical",
  "nrw_category": "real_loss_leakage",
  "probability": 0.92,
  "estimated_loss_m3_day": 85.5,
  "key_evidence": ["Night MNF +45%", "Pressure drop 0.8 bar"]
}
```

**Decision Engine Output:**
```json
{
  "priority_score": 78.5,
  "rank": 1,
  "locked_formula": {
    "leak_probability": 0.92,
    "estimated_loss_m3_day": 85.5,
    "criticality_factor": 1.2,
    "confidence_factor": 0.88
  },
  "urgency": "SAME_DAY",
  "recommendation": "Dispatch acoustic survey team"
}
```

---

## 12. ENTRY POINTS FOR RUNNING

### Main System Runner
```bash
python run_system.py
# Starts: MQTT Ingestion (1883), Dashboard (8050), REST API (8000)
```

### Individual Components
```bash
# Dashboard only
python -m src.dashboard.app

# API only
python -m src.api.integrated_api

# Sensor API only
python -m src.api.sensor_api
```

### Docker
```bash
docker-compose up -d
# Starts: API, Dashboard, MQTT Broker, TimescaleDB
```

---

## 13. DEPENDENCY GRAPH (Text)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEPENDENCY FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ESP32 Firmware ──MQTT──▶ esp32_connector.py ──▶ database_handler.py       │
│        │                        │                      │                    │
│        │                        ▼                      ▼                    │
│        └──HTTP──▶ sensor_api.py ───▶ sensor_data.json + database.py        │
│                        │                      │                             │
│                        ▼                      │                             │
│              integrated_api.py ◀──────────────┘                             │
│                        │                                                    │
│          ┌─────────────┼─────────────┐                                      │
│          ▼             ▼             ▼                                      │
│  anomaly_detector.py  workflow/   notifications/                            │
│          │           engine.py    alerting.py                               │
│          │              │              │                                    │
│          ▼              ▼              ▼                                    │
│  ┌───────────────────────────────────────────────┐                          │
│  │          integrated_nrw_api.py                │                          │
│  │  (Integrates 5 core components)               │                          │
│  └───────────────────────────────────────────────┘                          │
│          │                                                                  │
│          ├──▶ siv_manager.py (SIV data)                                     │
│          ├──▶ nrw_calculator.py (Water balance)                             │
│          ├──▶ decision_engine.py (Priority - LOCKED)                        │
│          ├──▶ baseline_comparison.py (STL vs AI)                            │
│          └──▶ continuous_learning.py (Feedback)                             │
│                        │                                                    │
│                        ▼                                                    │
│                 dashboard/app.py ◀──── Fetches from API                     │
│                        │                                                    │
│                        ▼                                                    │
│                 Field Feedback ──▶ continuous_learning.py ──▶ AI Models     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Document generated: 2026-01-16*
*AquaWatch NRW Detection System v3.0*
