# AquaWatch NRW - AI-Powered Non-Revenue Water Detection System

## National Water Intelligence Platform for Zambia & South Africa

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Status: Production-Ready](https://img.shields.io/badge/status-production--ready-green.svg)]()

---

## Executive Summary

AquaWatch NRW is a **decision-support system** for reducing Non-Revenue Water (NRW) losses through AI-powered pressure anomaly detection. The system detects abnormal pressure behavior caused by water leakage, localizes issues to pipe segments or District Metered Areas (DMAs), and prioritizes maintenance actions.

### What This System Does
- ✅ Detects pressure anomalies indicating potential leaks
- ✅ Localizes leakage to pipe segments or zones
- ✅ Prioritizes maintenance actions by severity and impact
- ✅ Provides decision support for utility operators
- ✅ Scales from lab prototype to national deployment

### What This System Does NOT Do
- ❌ Claim exact leak distance detection (physically impossible with pressure-only data)
- ❌ Replace human judgment in maintenance decisions
- ❌ Guarantee leak detection (it's probabilistic)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AQUAWATCH NRW ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   FIELD     │    │    EDGE     │    │   COMMS     │    │  INGESTION  │  │
│  │   LAYER     │───▶│   LAYER     │───▶│   LAYER     │───▶│   LAYER     │  │
│  │             │    │             │    │             │    │             │  │
│  │ • Pressure  │    │ • ESP32     │    │ • LoRaWAN   │    │ • MQTT      │  │
│  │ • Flow      │    │ • RTU       │    │ • Cellular  │    │ • Kafka     │  │
│  │ • Solar     │    │ • Local AI  │    │ • Satellite │    │ • Validation│  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                                                        │          │
│         ▼                                                        ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  DASHBOARD  │◀───│  DECISION   │◀───│     AI      │◀───│ TIME-SERIES │  │
│  │   LAYER     │    │  SUPPORT    │    │   LAYER     │    │  STORAGE    │  │
│  │             │    │             │    │             │    │             │  │
│  │ • National  │    │ • Alerts    │    │ • Anomaly   │    │ • TimescaleDB│ │
│  │ • Utility   │    │ • Priority  │    │ • Probabily │    │ • InfluxDB  │  │
│  │ • Field     │    │ • Workflow  │    │ • Localize  │    │ • QuestDB   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+ with TimescaleDB extension
- Docker (for containerized deployment)
- MQTT Broker (Mosquitto recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/aquawatch/nrw-detection.git
cd nrw-detection

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and MQTT credentials

# Initialize database
python scripts/init_database.py

# Run prototype simulation
python prototype/run_simulation.py
```

### Run the Dashboard
```bash
cd src/dashboard
python app.py
# Open http://localhost:8050 in your browser
```

---

## Project Structure

```
nrw-detection-system/
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── docker-compose.yml
│
├── docs/                           # Documentation
│   ├── 01_system_architecture.md
│   ├── 02_ai_methodology.md
│   ├── 03_deployment_guide.md
│   ├── 04_operator_manual.md
│   ├── 05_academic_paper.md
│   ├── 06_business_model.md
│   └── diagrams/
│
├── src/                            # Source code
│   ├── ingestion/                  # Data ingestion layer
│   ├── storage/                    # Database models & queries
│   ├── features/                   # Feature engineering
│   ├── ai/                         # AI models
│   │   ├── anomaly/               # Layer 1: Anomaly detection
│   │   ├── probability/           # Layer 2: Leak probability
│   │   └── localization/          # Layer 3: Localization
│   ├── baseline/                   # Physics-based baseline
│   ├── decision/                   # Decision support engine
│   ├── dashboard/                  # Web dashboards
│   └── workflow/                   # Operations workflow
│
├── config/                         # Configuration files
│   ├── settings.yaml
│   ├── sensors.yaml
│   └── thresholds.yaml
│
├── prototype/                      # Lab prototype
│   ├── simulator/
│   ├── hardware/
│   └── demo/
│
├── tests/                          # Test suite
│   ├── unit/
│   ├── integration/
│   └── simulation/
│
└── scripts/                        # Utility scripts
    ├── init_database.py
    ├── generate_sample_data.py
    └── deploy.py
```

---

## Key Design Principles

1. **Start Small, Scale Clean**: Works on 3 sensors, scales to 100,000+
2. **Physics First**: AI is validated against physics-based rules
3. **Human-in-the-Loop**: All decisions require human confirmation
4. **African Infrastructure Reality**: Low bandwidth, unreliable power, remote areas
5. **Explainable AI**: Every alert has a clear explanation
6. **Cost Efficiency**: Minimize sensor density while maximizing detection

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contact

For deployment inquiries, partnerships, or technical support:
- Technical: engineering@aquawatch.io
- Business: partnerships@aquawatch.io
#   A I - W A T E R  
 