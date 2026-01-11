# IWA Water Balance Framework Alignment

## Overview

> **"Most AI systems detect anomalies; ours understands water networks, NRW categories, and utility operations."**

The AquaWatch NRW system is designed from the ground up to align with the **IWA (International Water Association) Water Balance** framework. This document describes how the system implements IWA best practices.

---

## 1. IWA Water Balance Structure

```
System Input Volume (SIV)
├── Authorized Consumption
│   ├── Billed Authorized Consumption
│   │   ├── Billed Metered Consumption
│   │   └── Billed Unmetered Consumption
│   └── Unbilled Authorized Consumption
│       ├── Unbilled Metered Consumption
│       └── Unbilled Unmetered Consumption
│
└── Water Losses (NRW) ← AquaWatch Detection Target
    │
    ├── Apparent Losses (Commercial)
    │   ├── Unauthorized Consumption
    │   │   └── Theft, illegal connections
    │   └── Customer Metering Inaccuracies
    │       └── Under-registration, stopped meters
    │
    └── Real Losses (Physical)
        ├── Leakage on Transmission/Distribution Mains
        ├── Leakage on Service Connections
        └── Leakage and Overflows at Storage
```

---

## 2. NRW Category Classification

The system classifies all detections into IWA-standard NRW categories:

### 2.1 Real Losses (Physical Water Loss)

| Category | Code | Description | Typical Evidence |
|----------|------|-------------|------------------|
| Distribution Leakage | `REAL_LOSS_LEAKAGE` | Transmission/distribution main leaks | Night pressure drop, gradient change |
| Tank Overflow | `REAL_LOSS_OVERFLOW` | Reservoir/tank overflow events | Level sensor max, inlet flow continues |
| Service Connection | `REAL_LOSS_SERVICE` | Service connection leaks (utility side) | Elevated MNF, localized to area |

### 2.2 Apparent Losses (Commercial Water Loss)

| Category | Code | Description | Typical Evidence |
|----------|------|-------------|------------------|
| Meter Error | `APPARENT_LOSS_METER` | Customer meter under-registration | Flow-consumption mismatch |
| Unauthorized | `APPARENT_LOSS_UNAUTHORIZED` | Theft/illegal connections | Consumption anomaly, unaccounted water |

### 2.3 Classification Logic

```python
# Simplified classification logic from feature_engineering.py

def classify_nrw_category(features, is_night, pressure):
    """
    Classify detection into IWA NRW category.
    """
    if night_features_dominant and is_night:
        if pressure_gradient_change:
            return NRWCategory.REAL_LOSS_LEAKAGE
        else:
            return NRWCategory.REAL_LOSS_SERVICE
    
    elif pressure_features_dominant:
        return NRWCategory.REAL_LOSS_LEAKAGE
    
    elif meter_features_present:
        if flow_mismatch:
            return NRWCategory.APPARENT_LOSS_METER
        else:
            return NRWCategory.APPARENT_LOSS_UNAUTHORIZED
    
    else:
        return NRWCategory.UNKNOWN
```

---

## 3. Night-Time Analysis (MNF Window)

### 3.1 IWA Minimum Night Flow (MNF) Concept

The MNF analysis is a cornerstone of IWA methodology for Real Loss estimation:

- **Window:** 00:00 - 04:00 (configurable)
- **Rationale:** Minimal legitimate consumption during this period
- **Implication:** Elevated night flow indicates Real Losses

### 3.2 Implementation

```python
# Constants from feature_engineering.py
IWA_NIGHT_START_HOUR = 0   # 00:00
IWA_NIGHT_END_HOUR = 4     # 04:00

def is_night_window(timestamp):
    """Check if within MNF analysis window."""
    return IWA_NIGHT_START_HOUR <= timestamp.hour < IWA_NIGHT_END_HOUR
```

### 3.3 Confidence Boost

Detections during the MNF window receive a confidence boost:

```python
# From workflow/engine.py
if is_night_detection:
    effective_confidence = confidence * 1.2  # 20% boost
    effective_confidence = min(effective_confidence, 1.0)
```

---

## 4. Pressure-Leakage Relationship

### 4.1 IWA N1 Factor

The IWA recognizes that pressure directly affects leakage rate:

$$L = C \times P^{N_1}$$

Where:
- $L$ = Leakage rate (m³/hr)
- $C$ = Coefficient (depends on leak characteristics)
- $P$ = Pressure (bar)
- $N_1$ = Leakage exponent (0.5 for fixed outlets, 1.0-1.5 for flexible pipes)

### 4.2 Pressure Risk Zones

```python
# From workflow/engine.py
PRESSURE_ZONES = {
    "low": (0, 2.5),        # Under-pressure risk
    "optimal": (2.5, 4.0),  # Target zone
    "elevated": (4.0, 5.0), # Increased leakage risk
    "high": (5.0, 6.0),     # High leakage risk
    "critical": (6.0, 15.0) # Very high leakage risk
}
```

### 4.3 Loss Estimation with Pressure

```python
def estimate_loss_iwa(probability, pipe_diameter_mm, nrw_category, pressure_bar):
    """
    IWA-aligned loss estimation including pressure factor.
    """
    base_loss = BASE_LOSS_BY_CATEGORY[nrw_category]
    diameter_factor = (pipe_diameter_mm / 150.0) ** 0.5
    
    # IWA N1 pressure adjustment
    pressure_factor = (pressure_bar / 4.0) ** 1.0  # N1 = 1.0
    
    daily_loss = base_loss * diameter_factor * pressure_factor * probability
    return daily_loss
```

---

## 5. Water Utility Language

### 5.1 Alert Output Format

Instead of generic anomaly detection output:
```
❌ GENERIC: "Anomaly detected, probability 78%"
```

The system produces water-utility-focused output:
```
✅ IWA-ALIGNED:
"Real Loss - Distribution Main Leakage detected
 DMA: DMA-KIT-015
 Probability: 78%
 Confidence: HIGH (Night Analysis)
 Est. Loss: 45.2 m³/day ($169.50/day)
 Recommended: Acoustic survey in affected zone"
```

### 5.2 Work Order Content

Work orders include:
- NRW category context
- IWA-recommended intervention type
- Category-specific investigation steps
- Category-specific equipment list

### 5.3 Example Utility Report

```
╔══════════════════════════════════════════════════════════════════╗
║                    NRW DETECTION ALERT                           ║
╠══════════════════════════════════════════════════════════════════╣
║ Alert ID: NRW-2024-000042                                        ║
║ DMA: DMA-KIT-015                                                 ║
║ Time: 2024-01-15 02:30                                           ║
╠══════════════════════════════════════════════════════════════════╣
║ IWA CLASSIFICATION                                               ║
╠──────────────────────────────────────────────────────────────────╣
║ Category: Real Loss - Distribution Main Leakage                  ║
║ Confidence: 87% (HIGH - Night Analysis)                          ║
║ Severity: HIGH                                                   ║
╠══════════════════════════════════════════════════════════════════╣
║ ESTIMATED NRW IMPACT                                             ║
╠──────────────────────────────────────────────────────────────────╣
║ Daily Loss: 45.2 m³/day ($169.50/day)                           ║
║ Annual Loss: 16,498 m³/year ($61,868/year)                       ║
╠══════════════════════════════════════════════════════════════════╣
║ ANALYSIS CONTEXT                                                 ║
╠──────────────────────────────────────────────────────────────────╣
║ ⏰ Night Analysis (00:00-04:00): MNF deviation +15.2%            ║
║ 📊 Pressure: 3.80 bar (optimal risk)                             ║
║ Key Evidence:                                                    ║
║   • Detected during MNF window (00:00-04:00) - HIGH CONFIDENCE   ║
║   • Night pressure lower than baseline (MNF period)              ║
║   • Pressure gradient to downstream sensor increased             ║
╠══════════════════════════════════════════════════════════════════╣
║ RECOMMENDED ACTION                                               ║
╠──────────────────────────────────────────────────────────────────╣
║ Suspected distribution main leakage. MNF anomaly with pressure   ║
║ drop pattern. Recommend acoustic survey in affected zone.        ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 6. IWA-Aligned Interventions

The system recommends IWA-standard interventions based on NRW category:

| NRW Category | Primary Intervention | Secondary Intervention |
|--------------|---------------------|----------------------|
| Real Loss - Leakage | Acoustic Survey | Pressure Management |
| Real Loss - Overflow | Tank Level Control | SCADA Review |
| Real Loss - Service | Step Testing | Active Leak Detection |
| Apparent Loss - Meter | Meter Testing | Meter Replacement |
| Apparent Loss - Unauthorized | Customer Audit | Enforcement |

---

## 7. IWA Performance Indicators

The system tracks IWA standard performance indicators:

### 7.1 Infrastructure Leakage Index (ILI)

$$ILI = \frac{CARL}{UARL}$$

Where:
- CARL = Current Annual Real Losses (m³/year)
- UARL = Unavoidable Annual Real Losses

### 7.2 ILI Target Bands

| ILI | Band | Interpretation |
|-----|------|----------------|
| 1-2 | A | Excellent (low leakage potential) |
| 2-4 | B | Good (some potential for improvement) |
| 4-8 | C | Fair (significant potential for improvement) |
| >8 | D | Poor (urgent improvement needed) |

### 7.3 NRW as Percentage

$$NRW\% = \frac{System Input Volume - Billed Authorized Consumption}{System Input Volume} \times 100$$

Typical targets:
- Well-managed utility: < 15%
- Acceptable: 15-25%
- Needs improvement: 25-40%
- Critical: > 40%

---

## 8. Files Modified for IWA Alignment

| File | Changes |
|------|---------|
| `src/features/feature_engineering.py` | Added NRWCategory, OperationalPriority, SuggestedAction enums; WaterUtilityDetection class; classify_for_water_utility() method |
| `src/workflow/engine.py` | Updated Alert class with IWA fields; AlertGenerator with IWA classification; WorkOrderManager with NRW-specific content |
| `prototype/demo.py` | Enhanced to demonstrate IWA alignment |
| `docs/01_system_architecture.md` | Added IWA context |
| `docs/04_operator_manual.md` | Added IWA Water Balance section, NRW categories, night analysis guidance |

---

## 9. References

- IWA Water Balance Methodology
- IWA Performance Indicators for Water Supply Services (PI)
- Managing Leakage by Managing Pressure (IWA)
- Best Practice Guide on Minimum Night Flow Analysis
