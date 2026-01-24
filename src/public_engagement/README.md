# AquaWatch NRW v3.0 - Public Engagement Module

## Overview

The Public Engagement Module enables water utilities to crowdsource leak detection and water issue reports from the public. It provides multiple reporting channels (web, WhatsApp, USSD), intelligent duplicate detection, spam prevention, and seamless integration with the AI-powered NRW detection system.

## Key Features

### A) Multi-Channel Reporting
- **Web Portal** (`/report`): Mobile-first multi-step form with GPS geolocation
- **WhatsApp Bot**: Conversational 5-step workflow via WhatsApp Business API
- **USSD**: Menu-driven reporting for feature phones (`*123#`)
- **Mobile App**: API-ready for native app integration
- **Call Center**: Manual entry support

### B) Public Ticket Tracking
- **Track Page** (`/track/{ticket}`): Public-facing status tracking
- **SMS/WhatsApp Notifications**: Automatic status updates to reporters
- **Visual Timeline**: Clear progress indicators

### C) Admin Triage Dashboard
- **Filter & Search**: By category, status, area, source, date range
- **Map View**: Cluster visualization of report locations
- **Bulk Actions**: Multi-select for batch operations
- **Quick Actions**: One-click verify, assign, create work order

### D) Intelligent Processing
- **Duplicate Detection**: Haversine-based proximity matching (100m/30min)
- **Spam Prevention**: IP rate limiting, text pattern detection
- **AI Integration**: Link reports to detected leaks
- **Work Order Creation**: Convert confirmed reports to maintenance tasks

### E) Analytics & KPIs
- **Monthly Trends**: Report volume over time
- **Confirmation Rate**: Verified vs false report ratio
- **Response Times**: First response and resolution SLA tracking
- **Channel Performance**: Breakdown by source channel
- **Hotspot Analysis**: Top reporting areas

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PUBLIC CHANNELS                              │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│   Web Form   │  WhatsApp    │    USSD      │   Mobile App      │
│   /report    │   Webhook    │   Gateway    │      API          │
└──────┬───────┴──────┬───────┴──────┬───────┴─────────┬─────────┘
       │              │              │                 │
       ▼              ▼              ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐ │
│  │ Rate Limiter  │ │ Spam Detector │ │ Duplicate Detector    │ │
│  └───────┬───────┘ └───────┬───────┘ └───────────┬───────────┘ │
│          │                 │                     │              │
│          ▼                 ▼                     ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               PublicReportService                        │   │
│  │  - create_report()    - link_to_ai_leak()               │   │
│  │  - get_tracking_info() - create_work_order()            │   │
│  │  - update_status()    - merge_duplicates()              │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │ public_reports  │ │ report_media    │ │ report_links    │   │
│  │ (tenant_id FK)  │ │ (photos/audio)  │ │ (AI/WO links)   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│  ┌─────────────────┐ ┌─────────────────┐                        │
│  │ audit_logs      │ │ report_timeline │                        │
│  └─────────────────┘ └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### public_reports
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| ticket | VARCHAR(20) | Public ticket number (TKT-XXXXXX) |
| tenant_id | UUID | Foreign key to tenants table |
| category | ENUM | leak, burst, no_water, low_pressure, etc. |
| description | TEXT | User-provided description |
| latitude | FLOAT | GPS latitude |
| longitude | FLOAT | GPS longitude |
| area_text | VARCHAR(255) | Human-readable location |
| source | ENUM | web, whatsapp, ussd, mobile_app, call_center |
| reporter_name | VARCHAR(100) | Optional reporter name |
| reporter_phone | VARCHAR(20) | For follow-up (encrypted) |
| reporter_email | VARCHAR(255) | Optional email |
| reporter_consent | BOOLEAN | Marketing consent |
| status | ENUM | received, under_review, assigned, in_progress, resolved, closed |
| verification | ENUM | pending, confirmed, duplicate, false_report, needs_review, spam |
| spam_flag | BOOLEAN | Flagged by spam detection |
| quarantine | BOOLEAN | Held for manual review |
| master_report_id | UUID | If merged, points to master |
| is_master | BOOLEAN | Is this a master report |
| duplicate_count | INT | Number of merged duplicates |
| linked_leak_id | UUID | FK to ai_detected_leaks |
| linked_work_order_id | UUID | FK to work_orders |
| admin_notes | TEXT | Internal notes |
| assigned_to_user_id | UUID | FK to users |
| assigned_team | VARCHAR(100) | Team assignment |
| created_at | TIMESTAMP | Report submission time |
| updated_at | TIMESTAMP | Last modification |

---

## API Reference

### Public Endpoints (No Auth Required)

#### Create Report
```http
POST /api/v1/public/{tenant_id}/report
Content-Type: application/json

{
  "category": "leak",
  "description": "Water leaking from pipe near junction",
  "latitude": -15.4167,
  "longitude": 28.2833,
  "area_text": "Cairo Road, near Levy Junction",
  "reporter_name": "John Mwansa",
  "reporter_phone": "+260971234567",
  "reporter_consent": true
}

Response: 201 Created
{
  "ticket": "TKT-ABC123",
  "status": "received",
  "message": "Thank you! Your report has been submitted.",
  "tracking_url": "/track/TKT-ABC123"
}
```

#### Track Report
```http
GET /api/v1/public/{tenant_id}/track/{ticket}

Response: 200 OK
{
  "ticket": "TKT-ABC123",
  "category": "leak",
  "status": "under_review",
  "status_label": "Under Review",
  "submitted_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T14:22:00Z",
  "timeline": [
    {"status": "received", "timestamp": "2024-01-15T10:30:00Z"},
    {"status": "under_review", "timestamp": "2024-01-15T14:22:00Z"}
  ]
}
```

### Admin Endpoints (Auth Required)

#### List Reports
```http
GET /api/v1/admin/{tenant_id}/public-reports?status=received&category=leak&page=1&per_page=25
Authorization: Bearer {token}
```

#### Update Status
```http
PATCH /api/v1/admin/{tenant_id}/public-reports/{report_id}
{
  "status": "technician_assigned",
  "assigned_to_user_id": "user-uuid",
  "admin_notes": "Dispatched Team Alpha"
}
```

#### Create Work Order
```http
POST /api/v1/admin/{tenant_id}/public-reports/{report_id}/work-order
{
  "task_type": "repair",
  "priority": 2,
  "notes": "From public report TKT-ABC123"
}
```

#### Merge Duplicates
```http
POST /api/v1/admin/{tenant_id}/public-reports/merge
{
  "master_id": "report-uuid-1",
  "duplicate_ids": ["report-uuid-2", "report-uuid-3"]
}
```

---

## WhatsApp Bot Flow

```
User: Hi
Bot: 🌊 Welcome to AquaWatch!
     Report water issues in your area.
     
     What type of issue?
     1️⃣ Leak
     2️⃣ Burst Pipe
     3️⃣ No Water
     4️⃣ Low Pressure
     5️⃣ Other

User: 1

Bot: 📍 Please share your location.
     Tap the 📎 button > Location > Send Current Location

User: [Shares Location]

Bot: 📷 Can you share a photo of the issue?
     Send a photo or type "skip" to continue.

User: [Sends Photo]

Bot: 📝 Please describe the issue briefly.

User: Water leaking from underground pipe near school

Bot: ✅ Report Summary:
     - Type: Leak
     - Location: Cairo Rd (15.4°S, 28.3°E)
     - Description: Water leaking from...
     
     Is this correct?
     1️⃣ Yes, Submit
     2️⃣ No, Start Over

User: 1

Bot: 🎉 Thank you! Your report has been submitted.
     Ticket: TKT-XYZ789
     Track status: aquawatch.io/track/TKT-XYZ789
```

---

## USSD Flow

```
*123#

1. Report Water Issue
2. Track My Report
3. Emergency Contact

> 1

Select Issue Type:
1. Leak
2. Burst Pipe
3. No Water
4. Low Pressure

> 1

Enter Area/Landmark:
> Cairo Road near Shoprite

Describe the issue:
> Water flowing on road

Report submitted!
Ticket: TKT-ABC123
SMS sent to your phone.
```

---

## Running Locally

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis (optional, for distributed rate limiting)
- Node.js 18+ (for dashboard)

### Backend Setup

```bash
# Clone and navigate
cd nrw-detection-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp src/public_engagement/.env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start API server
uvicorn src.api.integrated_nrw_api:app --reload --host 0.0.0.0 --port 8000
```

### Dashboard Setup

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access Points
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **Public Report Form**: http://localhost:3000/report
- **Admin Reports**: http://localhost:3000/lwsc-zambia/public-reports
- **Analytics**: http://localhost:3000/lwsc-zambia/public-analytics

---

## Running Tests

```bash
# Run all public engagement tests
pytest tests/test_public_engagement.py -v

# Run with coverage
pytest tests/test_public_engagement.py --cov=src/public_engagement

# Run integration tests (requires DB)
pytest tests/test_public_engagement.py -m integration -v
```

---

## Seed Data

```bash
# Generate sample reports for testing
python -c "
from src.public_engagement.services import PublicReportService
from src.database import SessionLocal

db = SessionLocal()
service = PublicReportService()

# Create 50 sample reports
service.seed_demo_data(db, tenant_id='lwsc-zambia', count=50)
print('Seeded 50 demo reports')
"
```

---

## Configuration

### Rate Limiting

| Setting | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_REPORTS_PER_IP` | 5 | Max reports per IP per hour |
| `RATE_LIMIT_REPORTS_PER_PHONE` | 3 | Max reports per phone per day |
| `SPAM_QUARANTINE_MODE` | true | Quarantine instead of reject |

### Duplicate Detection

| Setting | Default | Description |
|---------|---------|-------------|
| `DUPLICATE_RADIUS_METERS` | 100 | Proximity threshold |
| `DUPLICATE_TIME_WINDOW_MINUTES` | 30 | Time window for matching |

---

## Security Considerations

1. **Data Privacy**: Reporter phone/email never exposed via public API
2. **Tenant Isolation**: All queries filtered by tenant_id
3. **Rate Limiting**: Prevents abuse from single source
4. **Spam Detection**: Text patterns and behavioral analysis
5. **Audit Logging**: All status changes logged with user/timestamp
6. **Input Validation**: Pydantic schemas validate all inputs
7. **CORS**: Restricted to allowed origins

---

## Future Enhancements

- [ ] SMS-based reporting channel
- [ ] Voice bot (IVR) integration
- [ ] Machine learning spam detection
- [ ] Reporter reputation scoring
- [ ] Gamification (points, leaderboards)
- [ ] Community notification radius
- [ ] Integration with GIS systems

---

## Support

For issues or questions:
- **Technical**: tech-support@aquawatch.io
- **Documentation**: docs.aquawatch.io/public-engagement
- **API Status**: status.aquawatch.io
