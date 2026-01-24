# Step 8: Explainable AI Insights - Implementation Summary

## Overview

Step 8 adds Explainable AI (XAI) capabilities to the AquaWatch NRW system, allowing operators to understand **why** the AI detected each leak with confidence breakdowns, evidence timelines, and actionable recommendations.

---

## Files Created/Modified

### Backend (Python)

#### 1. **NEW: `src/ai/explainable_ai.py`**
   - Core XAI module with data classes:
     - `SignalEvidence` - Evidence for each detection signal
     - `ConfidenceBreakdown` - Breakdown by detection method
     - `EvidenceTimelinePoint` - Time-series of detection events
     - `AIReason` - Main structure stored in `ai_reason` JSONB
   - `ExplainableLeakDetector` class with analysis methods:
     - `_analyze_pressure_drop()`
     - `_analyze_flow_rise()`
     - `_analyze_multi_sensor()`
     - `_analyze_night_flow()`
     - `_analyze_acoustic()`
     - `_calculate_confidence()`
     - `_generate_explanation()`
     - `_generate_recommendations()`

#### 2. **MODIFIED: `src/ai/anomaly_detector.py`**
   - Updated `AnomalyResult` dataclass with `ai_reason: Optional[Dict]` field
   - Added `_generate_ai_reason()` method to `AnomalyDetectionEngine`
   - `process_reading()` now returns `ai_reason` with every detection

#### 3. **MODIFIED: `src/storage/models.py`**
   - Added `ai_reason = Column(JSONB)` to `LeakEvent` model
   - Added documentation comments explaining JSONB structure

#### 4. **NEW: `migrations/versions/003_add_explainable_ai.py`**
   - Alembic migration to add `ai_reason` JSONB column
   - GIN indexes for efficient JSONB queries
   - Index on `confidence->>'overall_confidence'` for filtering

---

### Frontend (Next.js/TypeScript)

#### 5. **MODIFIED: `dashboard/src/app/api/leaks/route.ts`**
   - Added `AIReason` and supporting TypeScript interfaces
   - Updated `Leak` interface with `ai_reason` field
   - POST handler now accepts and stores `ai_reason`

#### 6. **NEW: `dashboard/src/components/ai/LeakXAIPanel.tsx`**
   - Main XAI visualization component with:
     - **Explanation Card** - Human-readable summary
     - **Top Contributing Signals** - Ranked with contribution percentages
     - **Confidence Breakdown** - Visual bars for each method
     - **Evidence Timeline** - Chronological anomaly events
     - **Recommendations** - Actionable next steps
     - **Feature Importance** - Badge cloud of signal weights

#### 7. **NEW: `dashboard/src/app/leaks/[id]/page.tsx`**
   - Full leak detail page with tabs:
     - **Overview** - Key metrics, details, actions
     - **AI Analysis** - Full XAI panel
     - **Timeline** - Event history

#### 8. **NEW: `dashboard/src/app/leaks/page.tsx`**
   - Leaks list page with filtering, sorting, and AI confidence indicators

#### 9. **NEW UI Components:**
   - `dashboard/src/components/ui/card.tsx`
   - `dashboard/src/components/ui/badge.tsx`
   - `dashboard/src/components/ui/button.tsx`
   - `dashboard/src/components/ui/progress.tsx`
   - `dashboard/src/components/ui/tabs.tsx`
   - `dashboard/src/components/ui/select.tsx`
   - `dashboard/src/components/ui/input.tsx`
   - `dashboard/src/components/ui/tooltip.tsx`
   - `dashboard/src/components/ai/index.ts` (exports)

---

## AI Reason JSONB Structure

```json
{
  "pressure_drop": {
    "signal_type": "pressure_drop",
    "contribution": 0.85,
    "value": 2.3,
    "threshold": 2.7,
    "deviation": -0.4,
    "description": "Sustained pressure drop of 0.4 bar detected...",
    "timestamp": "2026-01-23T10:30:00Z",
    "sensor_id": "PS-001",
    "raw_data": { "baseline_mean": 2.7, "baseline_std": 0.1 }
  },
  "flow_rise": { ... },
  "multi_sensor_agreement": { ... },
  "night_flow_deviation": { ... },
  "acoustic_anomaly": { ... },
  "confidence": {
    "statistical_confidence": 0.82,
    "ml_confidence": 0.78,
    "temporal_confidence": 0.65,
    "spatial_confidence": 0.90,
    "acoustic_confidence": 0.68,
    "overall_confidence": 0.87,
    "weights": { "statistical": 0.20, "ml": 0.25, ... }
  },
  "top_signals": ["multi_sensor_agreement", "pressure_drop", "flow_rise"],
  "evidence_timeline": [
    {
      "timestamp": "2026-01-23T10:25:00Z",
      "signal_type": "pressure_drop",
      "value": 2.3,
      "anomaly_score": 0.85,
      "description": "Sustained pressure drop confirmed",
      "is_key_event": true
    }
  ],
  "detection_method": "multi_signal",
  "detection_timestamp": "2026-01-23T10:30:00Z",
  "analysis_duration_seconds": 0.35,
  "explanation": "High confidence leak detection (87%)...",
  "recommendations": ["URGENT: Dispatch field team...", ...],
  "model_version": "3.0.0",
  "feature_importance": { "multi_sensor_agreement": 0.90, ... }
}
```

---

## Dashboard Routes

| Route | Description |
|-------|-------------|
| `/leaks` | Leaks list with filtering, sorting, AI indicators |
| `/leaks/[id]` | Leak detail page with XAI panel |
| `/leaks/[id]?tab=ai-analysis` | Direct to AI Analysis tab |

---

## Usage

### Python - Creating a Leak with AI Reason

```python
from src.ai.anomaly_detector import AnomalyDetectionEngine

engine = AnomalyDetectionEngine()
result = engine.process_reading("PIPE-001", pressure=2.3, flow=125.5)

if result.anomaly_type != AnomalyType.NORMAL:
    # result.ai_reason contains the full XAI data
    leak_event = LeakEvent(
        pipe_id=result.pipe_id,
        confidence=result.confidence,
        ai_reason=result.ai_reason,  # Store in JSONB column
        ...
    )
```

### React - Displaying XAI Panel

```tsx
import { LeakXAIPanel } from '@/components/ai/LeakXAIPanel'

<LeakXAIPanel aiReason={leak.ai_reason} leakId={leak.id} />
```

---

## Configuration

Tailwind CSS updated with shadcn/ui theme variables in:
- `globals.css` - CSS custom properties
- `tailwind.config.ts` - Color mappings

---

## Locked Decision Formula

```
Priority Score = (leak_probability × estimated_loss_m3_day) × criticality_factor × confidence_factor
```

This formula remains unchanged. The XAI system **explains** how confidence was calculated, not how priority is determined.

---

## Testing

```bash
# Run the explainable AI module directly
cd nrw-detection-system
python -m src.ai.explainable_ai

# Output shows sample detection with:
# - Overall Confidence
# - Top Signals
# - Confidence Breakdown
# - JSON ai_reason structure
```

---

## Next Steps

- [ ] Add acoustic sensor integration when hardware available
- [ ] Implement multi-sensor triangulation for precise localization
- [ ] Add model retraining feedback loop from confirmed/false-positive leaks
- [ ] Export XAI reports to PDF for regulatory compliance
