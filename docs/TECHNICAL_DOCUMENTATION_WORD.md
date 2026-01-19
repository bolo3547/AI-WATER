AQUAWATCH NRW DETECTION SYSTEM
COMPREHENSIVE TECHNICAL DOCUMENTATION

Version: 2.0
Date: January 2026
Authors: AquaWatch Development Team

════════════════════════════════════════════════════════════════════════════════

TABLE OF CONTENTS

1. Executive Summary
2. System Overview
3. Technology Stack
4. System Architecture
5. AI/ML Engine
6. Frontend Dashboard
7. Backend API
8. IoT & Sensor Integration
9. Data Models
10. Deployment
11. API Reference
12. Appendices

════════════════════════════════════════════════════════════════════════════════

1. EXECUTIVE SUMMARY

1.1 Purpose

The AquaWatch NRW Detection System is an enterprise-grade water utility management platform designed to:

    • Detect water leaks in real-time using AI-powered anomaly detection
    • Localize leak positions using gradient-based pressure analysis
    • Predict potential failures before they occur
    • Reduce Non-Revenue Water (NRW) losses by up to 40%
    • Optimize maintenance resource allocation through priority scoring


1.2 Key Benefits

    Benefit                     Impact
    ─────────────────────────────────────────────────────────────
    Water Loss Reduction        30-40% reduction in NRW
    Cost Savings                $500K+ annual savings for mid-size utilities
    Response Time               80% faster leak detection
    Operational Efficiency      60% reduction in manual monitoring
    Compliance                  IWA (International Water Association) aligned metrics


1.3 Target Users

    • Water Utility Operators - Daily monitoring and incident response
    • Network Engineers - DMA analysis and infrastructure planning
    • Executive Management - KPI dashboards and ROI tracking
    • Field Technicians - Work order management and leak repairs

════════════════════════════════════════════════════════════════════════════════

2. SYSTEM OVERVIEW

2.1 What is Non-Revenue Water (NRW)?

Non-Revenue Water represents water that is produced and lost before reaching the customer. It is calculated as:

    NRW = System Input Volume - Billed Authorized Consumption

NRW is categorized into:

    Category                Description                         Examples
    ─────────────────────────────────────────────────────────────────────────────
    Real Losses             Physical water losses               Pipe leaks, burst mains, tank overflows
    Apparent Losses         Commercial losses                   Meter errors, unauthorized consumption
    Unbilled Authorized     Legitimate unbilled use             Fire fighting, flushing, public fountains


2.2 IWA Water Balance

The system follows the International Water Association's standard water balance methodology:

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        SYSTEM INPUT VOLUME (SIV)                        │
    ├─────────────────────────────────┬───────────────────────────────────────┤
    │      AUTHORIZED CONSUMPTION     │         NON-REVENUE WATER (NRW)       │
    ├─────────────────┬───────────────┼─────────────────┬─────────────────────┤
    │  Billed         │ Unbilled      │ Apparent Losses │    Real Losses      │
    │  Metered        │ Authorized    │                 │                     │
    │  Consumption    │ Consumption   │ • Unauthorized  │ • Leakage on mains  │
    │                 │               │ • Meter errors  │ • Service pipe leaks│
    │                 │ • Firefighting│ • Data handling │ • Tank overflows    │
    │                 │ • Flushing    │   errors        │                     │
    └─────────────────┴───────────────┴─────────────────┴─────────────────────┘


2.3 Performance Indicators

    Indicator       Formula                             Target
    ─────────────────────────────────────────────────────────────────────────────
    NRW %           (SIV - Billed) / SIV × 100         < 25%
    ILI             CARL / UARL                         < 2.0
    CARL            Current Annual Real Losses          Minimize
    UARL            Unavoidable Annual Real Losses      Baseline

Where:
    • ILI = Infrastructure Leakage Index
    • CARL = Current Annual Real Losses (actual)
    • UARL = Unavoidable Annual Real Losses (theoretical minimum)

════════════════════════════════════════════════════════════════════════════════

3. TECHNOLOGY STACK

3.1 Complete Technology Matrix

FRONTEND LAYER:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    Next.js             14.0.4          React framework with App Router
    React               18.2.0          UI component library
    TypeScript          5.x             Type-safe JavaScript
    Tailwind CSS        3.4.0           Utility-first styling
    Recharts            2.10.3          Data visualization
    SWR                 2.2.4           Data fetching & caching
    Lucide React        0.303.0         Icon library
    clsx                2.1.0           Conditional classnames
    date-fns            3.2.0           Date manipulation

BACKEND LAYER:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    Python              3.10+           Core programming language
    FastAPI             0.104+          High-performance REST API
    Uvicorn             0.24+           ASGI server
    Pydantic            2.x             Data validation

AI/ML LAYER:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    scikit-learn        1.3+            Machine learning algorithms
    NumPy               1.24+           Numerical computing
    Pandas              2.0+            Data manipulation
    SciPy               1.11+           Scientific computing

DATABASE LAYER:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    SQLite              3.x             Development database
    PostgreSQL          15+             Production database
    TimescaleDB         2.x             Time-series extension

IOT LAYER:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    MQTT                5.0             IoT messaging protocol
    Mosquitto           2.x             MQTT broker
    ESP32               -               Microcontroller

INFRASTRUCTURE:
    Technology          Version         Purpose
    ─────────────────────────────────────────────────────────────────────────────
    Docker              24+             Containerization
    Docker Compose      2.x             Multi-container orchestration
    Nginx               1.25+           Reverse proxy & load balancer


3.2 Language Distribution

    Language                Percentage
    ─────────────────────────────────────────────────────────────────────────────
    Python                  45%         (Backend API, AI/ML engine, data processing)
    TypeScript/JavaScript   40%         (Frontend dashboard, React components)
    CSS (Tailwind)          10%         (Styling and theming)
    C++ (Arduino)           3%          (ESP32 sensor firmware)
    SQL                     2%          (Database queries)

════════════════════════════════════════════════════════════════════════════════

4. SYSTEM ARCHITECTURE

4.1 High-Level Architecture

The system is organized into five main layers:

LAYER 1: PRESENTATION LAYER
    ┌────────────────────────────────────────────────────────────────────────┐
    │                      Next.js 14 Dashboard                              │
    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐   │
    │  │  Executive   │ │     DMA      │ │    Work      │ │   System   │   │
    │  │  Overview    │ │ Intelligence │ │   Orders     │ │   Health   │   │
    │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘   │
    └────────────────────────────────────────────────────────────────────────┘

LAYER 2: API GATEWAY
    ┌────────────────────────────────────────────────────────────────────────┐
    │                         Nginx Reverse Proxy                            │
    │            Load Balancing • SSL Termination • Rate Limiting            │
    └────────────────────────────────────────────────────────────────────────┘

LAYER 3: SERVICE LAYER
    ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
    │    FastAPI Server   │  │   AI/ML Engine      │  │  Data Ingestion │
    │  • REST Endpoints   │  │  • Anomaly Detector │  │  • MQTT Client  │
    │  • Authentication   │  │  • Leak Localizer   │  │  • Validation   │
    │  • Rate Limiting    │  │  • Acoustic Analyzer│  │  • Normalization│
    └─────────────────────┘  └─────────────────────┘  └─────────────────┘

LAYER 4: DATA LAYER
    ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
    │   PostgreSQL +      │  │     MQTT Broker     │  │   Redis Cache   │
    │   TimescaleDB       │  │    (Mosquitto)      │  │  • Session store│
    │  • Sensor readings  │  │  • Pub/Sub topics   │  │  • Query cache  │
    │  • DMA configs      │  │  • QoS levels       │  │  • Rate limiting│
    └─────────────────────┘  └─────────────────────┘  └─────────────────┘

LAYER 5: SENSOR NETWORK
    ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
    │  ESP32    │  │  ESP32    │  │  ESP32    │  │  ESP32    │
    │ Flow Meter│  │ Pressure  │  │ Acoustic  │  │ Combined  │
    └───────────┘  └───────────┘  └───────────┘  └───────────┘


4.2 Data Flow Sequence

    STEP 1: SENSOR READING
        ESP32 captures:
        • Flow rate (pulses → m³/hour)
        • Pressure (analog → bar)
        • Acoustic signature (microphone → FFT)
                    ↓
    STEP 2: MQTT PUBLISH
        Topic: aquawatch/sensors/{sensor_id}/data
        Payload: JSON with sensor_id, timestamp, flow_rate, pressure, battery
                    ↓
    STEP 3: DATA INGESTION
        • Validate schema
        • Check sensor status
        • Normalize units
        • Store to TimescaleDB
                    ↓
    STEP 4: REAL-TIME ANALYSIS
        AI Engine processes:
        • Isolation Forest anomaly score
        • Z-score deviation
        • Pattern matching
                    ↓
    STEP 5: ANOMALY DETECTED?
        NO  → Continue monitoring
        YES → Trigger alert pipeline
                    ↓
    STEP 6: LEAK LOCALIZATION
        • Pressure gradient analysis
        • Multi-sensor triangulation
        • GPS coordinate estimation
        • Confidence scoring
                    ↓
    STEP 7: ALERT GENERATION
        • Create work order
        • Notify operators (WebSocket)
        • Log to database
        • Update dashboard KPIs
                    ↓
    STEP 8: DASHBOARD UPDATE
        SWR fetches new data → Components re-render → Real-time visualization

════════════════════════════════════════════════════════════════════════════════

5. AI/ML ENGINE

5.1 Overview

The AI/ML Engine is the core intelligence of the system, responsible for:

    • Anomaly Detection - Identifying unusual patterns in sensor data
    • Leak Localization - Pinpointing the physical location of leaks
    • Acoustic Analysis - Detecting leak signatures from sound patterns
    • Priority Scoring - Ranking interventions by urgency and impact
    • Predictive Maintenance - Forecasting potential failures


5.2 Anomaly Detection Module

File Location: src/ai/anomaly_detector.py

5.2.1 Algorithm: Isolation Forest

Isolation Forest is an unsupervised machine learning algorithm that identifies anomalies by isolating observations in the feature space.

How it works:
    1. Randomly select a feature
    2. Randomly select a split value between min and max
    3. Recursively partition data until each point is isolated
    4. Anomalies require fewer splits to isolate (shorter path length)

Mathematical Basis:

    Anomaly Score: s(x, n) = 2^(-E(h(x))/c(n))

    Where:
    • h(x) = path length of observation x
    • E(h(x)) = average path length over all trees
    • c(n) = average path length in unsuccessful search in BST
    • n = number of samples

Model Parameters:

    Parameter           Value           Description
    ─────────────────────────────────────────────────────────────────────────────
    contamination       0.1             Expected 10% anomaly rate
    n_estimators        100             100 trees for robust detection
    max_samples         auto            Samples per tree
    random_state        42              Reproducibility
    n_jobs              -1              Parallel processing


5.2.2 Algorithm: Z-Score Analysis

Z-Score measures how many standard deviations a value is from the mean.

Formula:
    Z = (X - μ) / σ

Where:
    • X = observed value
    • μ = mean of the dataset
    • σ = standard deviation

Detection Rule:
    Values with |Z| > 3.0 are considered anomalies.
    Default threshold of 3.0 catches ~0.3% of normal distribution.


5.2.3 Feature Engineering

The AI engine uses these features for detection:

    Feature             Description                     Unit            Weight
    ─────────────────────────────────────────────────────────────────────────────
    flow_rate           Water flow measurement          m³/hour         0.35
    pressure            Line pressure                   bar             0.25
    flow_variance       Flow rate variability           m³/hour²        0.15
    pressure_variance   Pressure variability            bar²            0.10
    hour_of_day         Time-based patterns             0-23            0.05
    day_of_week         Weekly patterns                 0-6             0.05
    temperature         Ambient temperature             °C              0.05


5.3 Leak Localization Module

File Location: src/ai/leak_localizer.py

5.3.1 Gradient-Based Localization

Leaks create pressure drops that propagate through the pipe network. By analyzing pressure gradients between multiple sensors, we can triangulate the leak location.

Example:
    Sensor A (3.5 bar)    Sensor B (3.2 bar)    Sensor C (3.4 bar)
         |                      |                      |
         ↓                      ↓                      ↓
    ═════╪══════════════════════╪══════════════════════╪═════
                                |
                             LEAK 💧
    
    Pressure gradient: ΔP_AB = 0.3 bar, ΔP_BC = 0.2 bar
    Result: Leak closer to B (highest pressure drop)

Algorithm Steps:
    1. Calculate pressure deviations from baseline for each sensor
    2. Assign weights based on deviation magnitude
    3. Calculate weighted centroid (latitude/longitude)
    4. Compute confidence score based on sensor agreement
    5. Estimate water loss from flow imbalance


5.4 Acoustic Detection Module

File Location: src/ai/acoustic_detection.py

5.4.1 FFT-Based Leak Signature Detection

Leaks produce characteristic acoustic signatures that can be detected using Fast Fourier Transform analysis.

Leak Frequency Ranges:

    Leak Type                   Frequency Range     Amplitude Pattern
    ─────────────────────────────────────────────────────────────────────────────
    Small leak (< 1 L/min)      500-1500 Hz         Low, consistent
    Medium leak (1-10 L/min)    200-800 Hz          Medium, pulsating
    Large leak (> 10 L/min)     50-300 Hz           High, irregular
    Burst pipe                  20-100 Hz           Very high, decaying

Analysis Process:
    1. Apply bandpass filter (20-2000 Hz for pipe acoustics)
    2. Compute FFT
    3. Analyze energy in each leak frequency range
    4. Determine leak type and confidence
    5. Find dominant frequency


5.5 Priority Scoring Algorithm

The system calculates a priority score (0-100) for each detected anomaly to help operators focus on the most critical issues.

Scoring Formula:

    Priority Score = (W₁ × NRW_Impact) + (W₂ × Confidence) + (W₃ × Duration) + (W₄ × Location_Risk)

    Where:
    • W₁ = 0.40 (NRW impact weight)
    • W₂ = 0.25 (Detection confidence weight)
    • W₃ = 0.20 (Duration/persistence weight)
    • W₄ = 0.15 (Location risk weight)

Score Interpretation:

    Score Range     Priority        Action Required
    ─────────────────────────────────────────────────────────────────────────────
    80-100          Critical        Immediate dispatch
    60-79           High            Within 24 hours
    40-59           Medium          Within 1 week
    0-39            Low             Scheduled maintenance


5.6 Detection Thresholds

    Threshold               Value           Description
    ─────────────────────────────────────────────────────────────────────────────
    NRW_CRITICAL            35%             Red alert threshold
    NRW_WARNING             25%             Yellow alert threshold
    NRW_HEALTHY             15%             Green (IWA target)
    CONFIDENCE_MIN          70%             Minimum confidence for alerts

════════════════════════════════════════════════════════════════════════════════

6. FRONTEND DASHBOARD

6.1 Technology Overview

The dashboard is built with Next.js 14 using the App Router paradigm, providing:

    • Server Components - Default rendering on server for performance
    • Client Components - Interactive elements with 'use client' directive
    • File-based Routing - Pages defined by folder structure
    • API Routes - Backend API proxied through Next.js


6.2 Project Structure

    dashboard/
    ├── src/
    │   ├── app/                          # App Router pages
    │   │   ├── layout.tsx                # Root layout with sidebar/topbar
    │   │   ├── page.tsx                  # Executive Overview (/)
    │   │   ├── globals.css               # Global styles & Tailwind
    │   │   ├── dma/
    │   │   │   ├── page.tsx              # DMA Intelligence (/dma)
    │   │   │   └── [id]/
    │   │   │       └── page.tsx          # DMA Deep Dive (/dma/[id])
    │   │   ├── actions/
    │   │   │   └── page.tsx              # Work Orders (/actions)
    │   │   └── health/
    │   │       └── page.tsx              # System Health (/health)
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── Sidebar.tsx           # Navigation sidebar
    │   │   │   └── TopBar.tsx            # Header with status
    │   │   ├── metrics/
    │   │   │   ├── KPICard.tsx           # Key metric cards
    │   │   │   └── StatusIndicators.tsx  # Status badges
    │   │   ├── charts/
    │   │   │   └── Charts.tsx            # Recharts wrappers
    │   │   ├── data/
    │   │   │   └── DataTable.tsx         # Data tables
    │   │   └── ui/
    │   │       └── Cards.tsx             # UI card components
    │   └── lib/
    │       └── api.ts                    # API client & hooks
    ├── package.json
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── next.config.js


6.3 Dashboard Pages

    Page                Route           Purpose
    ─────────────────────────────────────────────────────────────────────────────
    Executive Overview  /               Network-wide KPIs, NRW trend, AI insights
    DMA Intelligence    /dma            District Metered Area rankings & analysis
    DMA Deep Dive       /dma/[id]       Individual DMA detailed metrics
    Work Orders         /actions        Leak repairs & maintenance tasks
    System Health       /health         Sensor status, API health, AI engine status


6.4 Data Fetching Strategy

The dashboard uses SWR (stale-while-revalidate) for real-time data fetching:

    Hook                    Endpoint            Refresh Interval
    ─────────────────────────────────────────────────────────────────────────────
    useSystemMetrics()      /api/metrics        30 seconds
    useDMAList()            /api/dmas           60 seconds
    useDMA(id)              /api/dmas/{id}      On demand
    useLeaks()              /api/leaks          15 seconds (more frequent for alerts)


6.5 Visual Design System

Color Palette:

    Color               Hex Code        Usage
    ─────────────────────────────────────────────────────────────────────────────
    Slate 900           #0f172a         Dark backgrounds, text
    Slate 50            #f8fafc         Light backgrounds
    Blue 500            #3b82f6         Primary accent, links
    Emerald 500         #10b981         Success, healthy status
    Amber 500           #f59e0b         Warning status
    Red 500             #ef4444         Error, critical status

Typography:

    Element             Font            Size        Weight
    ─────────────────────────────────────────────────────────────────────────────
    Hero Metric         Inter           48px        800 (Extra Bold)
    Page Title          Inter           32px        700 (Bold)
    Section Title       Inter           18px        600 (Semi Bold)
    Body Text           Inter           14px        400 (Regular)
    Labels              Inter           12px        500 (Medium)
    Monospace           JetBrains Mono  14px        400 (Regular)

════════════════════════════════════════════════════════════════════════════════

7. BACKEND API

7.1 API Structure

File Location: src/api/integrated_api.py

Framework: FastAPI (Python)

The API provides RESTful endpoints for all dashboard data requirements.


7.2 API Endpoints Reference

    Method      Endpoint                        Description
    ─────────────────────────────────────────────────────────────────────────────
    GET         /api/metrics                    System-wide KPIs
    GET         /api/dmas                       List all DMAs
    GET         /api/dmas/{id}                  Single DMA details
    GET         /api/dmas/{id}/flow             DMA flow time-series
    GET         /api/leaks                      List leaks (filterable)
    POST        /api/leaks/{id}/acknowledge     Acknowledge leak
    POST        /api/leaks/{id}/resolve         Mark leak resolved
    GET         /api/sensors                    List all sensors
    GET         /api/sensors/{id}               Sensor details
    GET         /api/health                     System health check
    GET         /api/nrw/trend                  NRW trend data


7.3 Response Examples

GET /api/metrics Response:

    {
        "total_nrw_percent": 32.4,
        "total_nrw_trend": "down",
        "total_real_losses": 12450,
        "water_recovered_30d": 8230,
        "revenue_recovered_30d": 485000,
        "active_high_priority_leaks": 3,
        "ai_status": "operational",
        "ai_confidence": 94,
        "dma_count": 12,
        "sensor_count": 48,
        "last_data_received": "2026-01-17T10:30:00Z"
    }

GET /api/dmas Response:

    [
        {
            "dma_id": "dma-001",
            "name": "Kabulonga North",
            "nrw_percent": 45.2,
            "priority_score": 87,
            "status": "critical",
            "trend": "up",
            "sensor_count": 8,
            "area_km2": 4.5,
            "population": 25000
        }
    ]

GET /api/leaks Response:

    [
        {
            "id": "leak-001",
            "dma_id": "dma-001",
            "location": "Junction Rd & Main St",
            "latitude": -15.4167,
            "longitude": 28.2833,
            "estimated_loss": 450,
            "priority": "high",
            "confidence": 92,
            "status": "detected",
            "detected_at": "2026-01-17T09:15:00Z"
        }
    ]

════════════════════════════════════════════════════════════════════════════════

8. IOT & SENSOR INTEGRATION

8.1 ESP32 Sensor Firmware

File Location: firmware/aquawatch_sensor/aquawatch_sensor.ino

Language: C++ (Arduino framework)

The ESP32 microcontroller handles:
    • Flow measurement via pulse counting
    • Pressure measurement via analog input
    • WiFi connectivity
    • MQTT publishing


8.2 Sensor Specifications

    Parameter               Value               Description
    ─────────────────────────────────────────────────────────────────────────────
    Flow Calibration        7.5 pulses/liter    Conversion factor
    Pressure Offset         0.5V                Sensor zero offset
    Pressure Scale          1.2 bar/V           Voltage to pressure
    Publish Interval        60 seconds          Data transmission rate
    WiFi Reconnect          Auto                Automatic reconnection


8.3 MQTT Topic Structure

    aquawatch/
    ├── sensors/
    │   ├── {sensor_id}/
    │   │   ├── data          # Sensor readings (published by sensors)
    │   │   ├── status        # Online/offline status
    │   │   └── config        # Configuration updates
    ├── alerts/
    │   ├── leaks             # New leak detections
    │   └── anomalies         # Anomaly alerts
    └── system/
        ├── health            # System health updates
        └── commands          # System commands


8.4 Sensor Data Payload

    {
        "sensor_id": "S-001",
        "timestamp": "2026-01-17T10:30:00Z",
        "flow_rate": 125.4,
        "pressure": 3.2,
        "battery": 87,
        "rssi": -65
    }

    Field           Type        Unit        Description
    ─────────────────────────────────────────────────────────────────────────────
    sensor_id       string      -           Unique sensor identifier
    timestamp       ISO8601     -           Reading timestamp
    flow_rate       float       m³/hour     Water flow rate
    pressure        float       bar         Line pressure
    battery         integer     %           Battery level
    rssi            integer     dBm         WiFi signal strength

════════════════════════════════════════════════════════════════════════════════

9. DATA MODELS

9.1 Database Schema

TABLE: sensor_readings (Time-series data)

    Column              Type            Description
    ─────────────────────────────────────────────────────────────────────────────
    id                  SERIAL          Primary key
    sensor_id           VARCHAR(50)     Foreign key to sensors
    timestamp           TIMESTAMPTZ     Reading timestamp
    flow_rate           DECIMAL(10,4)   Flow measurement
    pressure            DECIMAL(10,4)   Pressure measurement
    temperature         DECIMAL(5,2)    Temperature (optional)
    battery_percent     INTEGER         Battery level
    rssi                INTEGER         Signal strength
    created_at          TIMESTAMPTZ     Record creation time


TABLE: dmas (District Metered Areas)

    Column              Type            Description
    ─────────────────────────────────────────────────────────────────────────────
    dma_id              VARCHAR(50)     Primary key
    name                VARCHAR(255)    DMA name
    description         TEXT            Description
    area_km2            DECIMAL(10,2)   Area in square kilometers
    population          INTEGER         Population served
    pipe_length_km      DECIMAL(10,2)   Total pipe length
    created_at          TIMESTAMPTZ     Record creation time
    updated_at          TIMESTAMPTZ     Last update time


TABLE: sensors

    Column              Type            Description
    ─────────────────────────────────────────────────────────────────────────────
    sensor_id           VARCHAR(50)     Primary key
    dma_id              VARCHAR(50)     Foreign key to dmas
    name                VARCHAR(255)    Sensor name
    type                VARCHAR(50)     flow, pressure, acoustic, combined
    latitude            DECIMAL(10,8)   GPS latitude
    longitude           DECIMAL(11,8)   GPS longitude
    installation_date   DATE            Installation date
    last_calibration    DATE            Last calibration date
    status              VARCHAR(20)     active, inactive, maintenance


TABLE: leaks

    Column                  Type            Description
    ─────────────────────────────────────────────────────────────────────────────
    id                      SERIAL          Primary key
    leak_id                 VARCHAR(50)     Unique identifier
    dma_id                  VARCHAR(50)     Foreign key to dmas
    latitude                DECIMAL(10,8)   GPS latitude
    longitude               DECIMAL(11,8)   GPS longitude
    location_description    TEXT            Human-readable location
    estimated_loss_m3_day   DECIMAL(10,2)   Estimated water loss
    priority                VARCHAR(20)     high, medium, low
    confidence              DECIMAL(5,2)    Detection confidence %
    status                  VARCHAR(20)     detected, confirmed, in_progress, resolved
    detected_at             TIMESTAMPTZ     Detection timestamp
    resolved_at             TIMESTAMPTZ     Resolution timestamp


TABLE: work_orders

    Column              Type            Description
    ─────────────────────────────────────────────────────────────────────────────
    id                  SERIAL          Primary key
    work_order_id       VARCHAR(50)     Unique identifier
    leak_id             VARCHAR(50)     Foreign key to leaks
    assigned_to         VARCHAR(255)    Assigned technician
    priority            VARCHAR(20)     high, medium, low
    status              VARCHAR(20)     pending, in_progress, completed, cancelled
    scheduled_date      DATE            Scheduled repair date
    completed_date      DATE            Actual completion date
    notes               TEXT            Work notes

════════════════════════════════════════════════════════════════════════════════

10. DEPLOYMENT

10.1 Docker Services

The system is deployed using Docker Compose with the following services:

    Service         Image/Build             Port        Purpose
    ─────────────────────────────────────────────────────────────────────────────
    api             Dockerfile.api          8000        FastAPI REST server
    dashboard       Dockerfile.dashboard    3001        Next.js frontend
    ingestion       Dockerfile.ingestion    -           Data ingestion service
    db              timescaledb:pg15        5432        PostgreSQL + TimescaleDB
    mqtt            eclipse-mosquitto:2     1883, 9001  MQTT broker
    nginx           nginx:alpine            80, 443     Reverse proxy


10.2 Production Deployment Steps

    Step 1: Clone repository
        git clone https://github.com/aquawatch/nrw-detection-system.git
        cd nrw-detection-system

    Step 2: Configure environment
        cp .env.example .env
        # Edit .env with production values

    Step 3: Build and start services
        docker-compose -f docker-compose.prod.yml up -d --build

    Step 4: Run database migrations
        docker-compose exec api python -m alembic upgrade head

    Step 5: Train initial AI model
        docker-compose exec api python scripts/train_model.py

    Step 6: Verify deployment
        curl http://localhost/api/health


10.3 Environment Variables

    Variable                Value (Example)                         Description
    ─────────────────────────────────────────────────────────────────────────────
    DATABASE_URL            postgresql://user:pass@db:5432/aquawatch Database connection
    MQTT_BROKER             mqtt                                    MQTT broker hostname
    AI_MODEL_PATH           /app/models                             AI model storage path
    SECRET_KEY              [secure-random-string]                  JWT secret key
    CORS_ORIGINS            http://localhost:3001                   Allowed CORS origins

════════════════════════════════════════════════════════════════════════════════

11. API REFERENCE

11.1 Authentication

All API endpoints require authentication via JWT token:

    Header: Authorization: Bearer <token>


11.2 Error Responses

    Status Code     Description             Response Body
    ─────────────────────────────────────────────────────────────────────────────
    400             Bad Request             {"detail": "Invalid parameters"}
    401             Unauthorized            {"detail": "Not authenticated"}
    403             Forbidden               {"detail": "Permission denied"}
    404             Not Found               {"detail": "Resource not found"}
    500             Server Error            {"detail": "Internal server error"}


11.3 Pagination

List endpoints support pagination:

    Parameter       Type        Default     Description
    ─────────────────────────────────────────────────────────────────────────────
    page            integer     1           Page number
    limit           integer     20          Items per page
    sort_by         string      varies      Sort field
    order           string      desc        Sort order (asc/desc)

════════════════════════════════════════════════════════════════════════════════

12. APPENDICES

12.1 Glossary

    Term            Definition
    ─────────────────────────────────────────────────────────────────────────────
    NRW             Non-Revenue Water - water produced but not billed
    DMA             District Metered Area - hydraulically isolated zone
    MNF             Minimum Night Flow - lowest flow (typically 2-4 AM)
    ILI             Infrastructure Leakage Index - IWA performance metric
    CARL            Current Annual Real Losses
    UARL            Unavoidable Annual Real Losses
    FFT             Fast Fourier Transform - signal analysis algorithm
    MQTT            Message Queuing Telemetry Transport - IoT protocol
    SWR             Stale-While-Revalidate - data fetching strategy


12.2 References

    1. IWA Water Loss Task Force. "Best Practice Performance Indicators"
    2. Lambert, A. "International Report on Water Losses Management"
    3. scikit-learn Documentation: Isolation Forest
    4. Next.js 14 Documentation
    5. TimescaleDB Best Practices Guide
    6. FastAPI Documentation
    7. Eclipse Mosquitto MQTT Broker


12.3 Version History

    Version     Date            Changes
    ─────────────────────────────────────────────────────────────────────────────
    2.0         January 2026    Next.js dashboard, enhanced AI, acoustic detection
    1.5         November 2025   Acoustic detection module
    1.0         September 2025  Initial release


12.4 Contact Information

    Role                    Contact
    ─────────────────────────────────────────────────────────────────────────────
    Technical Support       support@aquawatch.com
    Sales Inquiries         sales@aquawatch.com
    Documentation           docs@aquawatch.com

════════════════════════════════════════════════════════════════════════════════

© 2026 AquaWatch Technologies. All Rights Reserved.

Document Version: 2.0
Last Updated: January 17, 2026
