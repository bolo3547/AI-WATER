# AquaWatch NRW - Operator Manual

## IWA Water Balance Aligned Operations

> **"Most AI systems detect anomalies; ours understands water networks, NRW categories, and utility operations."**

This system is built on the **IWA (International Water Association) Water Balance** framework, ensuring all detections, alerts, and recommendations align with global water utility best practices.

---

## Quick Reference Card

### IWA NRW Categories
| Category | Type | Description | Typical Intervention |
|----------|------|-------------|---------------------|
| Real Loss - Leakage | Physical | Distribution main leakage | Acoustic survey, repair |
| Real Loss - Overflow | Physical | Tank/reservoir overflow | Level control adjustment |
| Real Loss - Service | Physical | Service connection leaks | Step-testing, repair |
| Apparent Loss - Meter | Commercial | Meter under-registration | Meter testing/replacement |
| Apparent Loss - Unauthorized | Commercial | Theft/illegal connections | Customer audit, enforcement |

### Alert Severity Response Times
| Severity | Color | Response Time | Action |
|----------|-------|---------------|--------|
| CRITICAL | 🔴 Red | < 30 minutes | Immediate dispatch (Real Loss >100 m³/day) |
| HIGH | 🟠 Orange | < 4 hours | Same-day response (Real Loss confirmed) |
| MEDIUM | 🟡 Yellow | < 48 hours | Scheduled investigation |
| LOW | 🟢 Green | < 1 week | Routine maintenance/monitoring |

### Night Detection Confidence (IWA MNF Window)
| Detection Time | Confidence | Rationale |
|----------------|------------|-----------|
| 00:00 - 04:00 | HIGH | Minimum Night Flow window - minimal legitimate demand |
| 04:00 - 06:00 | MODERATE | Early morning - some legitimate use starting |
| 06:00 - 00:00 | STANDARD | Normal operation - legitimate demand present |

### AI Confidence Interpretation
| Confidence | Meaning | Recommended Action |
|------------|---------|-------------------|
| > 85% | High confidence | Trust AI recommendation |
| 70-85% | Moderate confidence | Verify with additional data |
| 50-70% | Low confidence | Manual review required |
| < 50% | Insufficient data | Increase sensor coverage |

---

## 1. Understanding IWA Water Balance

### 1.1 What is NRW?

**Non-Revenue Water (NRW)** = Water that is produced but does not generate revenue.

```
System Input Volume
├── Authorized Consumption (Billed + Unbilled)
└── Water Losses (NRW)
    ├── Real Losses (Physical)
    │   ├── Leakage from transmission/distribution mains
    │   ├── Leakage from service connections
    │   └── Overflow at storage facilities
    └── Apparent Losses (Commercial)
        ├── Meter under-registration
        └── Unauthorized consumption
```

### 1.2 Why IWA Classification Matters

**Real Losses** and **Apparent Losses** require different interventions:

| Real Losses | Apparent Losses |
|-------------|-----------------|
| Physical leak detection | Meter testing |
| Acoustic surveys | Customer audits |
| Pressure management | Revenue protection |
| Infrastructure repair | Data validation |

The AquaWatch system automatically classifies detections so you know **exactly what action to take**.

### 1.3 Night-Time Analysis (MNF)

The **Minimum Night Flow (MNF)** analysis is a cornerstone of IWA methodology:

- **Window:** 00:00 - 04:00 (configurable)
- **Why:** Minimal legitimate consumption during this period
- **Implication:** Elevated night flow = Real Loss (leakage)

When you see **"🌙 Night Detection"** in an alert, it means:
- Detection occurred during MNF window
- **HIGH CONFIDENCE** in the finding
- Likely **Real Loss** category

### 1.4 Pressure-Leakage Relationship

The IWA recognizes that **pressure directly affects leakage rate**:

$$L = C \times P^{N_1}$$

Where:
- $L$ = Leakage rate
- $P$ = Pressure
- $N_1$ = Exponent (0.5 for fixed outlets, 1.0-1.5 for flexible pipes)

**Pressure Risk Zones:**
| Zone | Pressure (bar) | Implication |
|------|---------------|-------------|
| Low | < 2.5 | Service quality risk |
| Optimal | 2.5 - 4.0 | Target operating range |
| Elevated | 4.0 - 5.0 | Increased leakage risk |
| High | 5.0 - 6.0 | High leakage risk |
| Critical | > 6.0 | Very high leakage risk |

---

## 2. Daily Operations

### 1.1 Start of Shift Checklist

1. **Login to Dashboard**
   - Navigate to https://aquawatch.yourutility.com
   - Enter credentials
   - Select your DMA assignment

2. **Review Overnight Alerts**
   - Check the Alert Panel for new items
   - Note any CRITICAL or HIGH severity alerts
   - Acknowledge alerts to claim ownership

3. **System Health Check**
   - Verify sensor connectivity (green indicators)
   - Check for any offline sensors (red indicators)
   - Review data quality metrics

### 1.2 Alert Acknowledgement Process

```
Step 1: Click on alert in dashboard
Step 2: Review AI evidence and probability
Step 3: Click "Acknowledge" button
Step 4: Alert moves to your work queue
Step 5: Create work order if investigation needed
```

### 1.3 Work Order Creation

From an acknowledged alert:

1. Click **"Create Work Order"** button
2. System auto-populates:
   - Location details
   - AI probability and evidence
   - Recommended investigation steps
   - Equipment list
3. Assign to available technician
4. Set priority based on severity
5. Click **"Submit"**

---

## 3. Understanding AI Detections (IWA-Aligned)

### 3.1 Detection Types by NRW Category

#### Real Loss - Distribution Leakage
**What it means:** Physical water loss from transmission/distribution mains

**IWA Classification:** Real Loss - Infrastructure Leakage

**Key Evidence:**
- Night pressure drop (MNF period)
- Pressure gradient changes toward leak location
- Sustained deviation from baseline

**Example Alert:**
```
╔══════════════════════════════════════════════════════════════════╗
║                    NRW DETECTION ALERT                           ║
╠══════════════════════════════════════════════════════════════════╣
║ Alert ID: NRW-2024-000042                                        ║
║ DMA: Kitwe Central (DMA-KIT-015)                                 ║
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
║ KEY EVIDENCE                                                     ║
╠──────────────────────────────────────────────────────────────────╣
║ • 🌙 Detected during MNF window (00:00-04:00) - HIGH CONFIDENCE  ║
║ • Night pressure 0.15 bar below baseline (MNF period)            ║
║ • Pressure gradient to downstream sensor increased 20%           ║
║ • Night/day pressure ratio indicates night leakage               ║
╠══════════════════════════════════════════════════════════════════╣
║ RECOMMENDED ACTION                                               ║
╠──────────────────────────────────────────────────────────────────╣
║ Suspected distribution main leakage. MNF anomaly with pressure   ║
║ drop pattern. Recommend acoustic survey in affected zone.        ║
╚══════════════════════════════════════════════════════════════════╝
```

#### Real Loss - Tank/Reservoir Overflow
**What it means:** Water loss from storage facility overflow

**IWA Classification:** Real Loss - Overflow from Utility Storage

**Key Evidence:**
- Inlet flow continues despite full tank
- Level sensor shows maximum
- Overflow pipe discharge detected

**Intervention:**
- Check level sensor calibration
- Verify inlet valve automatic shutoff
- Review SCADA setpoints

#### Real Loss - Service Connection
**What it means:** Leakage from service pipes (utility-side of meter)

**IWA Classification:** Real Loss - Service Connection Leakage

**Key Evidence:**
- MNF elevated in specific area
- No main pressure anomaly (suggests smaller distributed leaks)
- Step-test narrows down to service connections

**Intervention:**
- Perform step-testing
- Listen at stop taps and ferrules
- Check meter box areas for moisture

#### Apparent Loss - Meter Under-registration
**What it means:** Customer meters recording less than actual consumption

**IWA Classification:** Apparent Loss - Customer Meter Inaccuracies

**Key Evidence:**
- Flow-consumption mismatch
- Old meter age (degradation)
- Specific customer anomalies

**Intervention:**
- Meter accuracy testing
- Calibration check
- Replacement if accuracy < 98%

#### Apparent Loss - Unauthorized Consumption
**What it means:** Theft or illegal connections

**IWA Classification:** Apparent Loss - Unauthorized Consumption

**Key Evidence:**
- Consumption pattern anomalies
- Unaccounted-for water in specific areas
- Physical inspection triggers

**Intervention:**
- Customer audit
- Connection survey
- Revenue protection enforcement

### 3.2 Minimum Night Flow (MNF) Deviation
**What it means:** Higher-than-expected water flow during 00:00-04:00

**Why it matters (IWA Standard):**
- Minimum legitimate consumption period
- Elevated MNF = Real Loss indicator
- HIGH CONFIDENCE detection window

**Calculation:**
```
Expected MNF = Authorized night use + Legitimate leakage allowance
Deviation = Actual MNF - Expected MNF
If Deviation > 10%: Alert generated with HIGH confidence
```

---

## 3. Interpreting Dashboard Views

### 3.1 National Dashboard (Ministry Level)

**Purpose:** Strategic overview for policy makers

**Key Metrics:**
- **National NRW %**: Target < 25%
- **Active Alerts**: Should decrease over time
- **Critical DMAs**: Priority areas for investment
- **Trend Charts**: Month-over-month improvement

**Actions available:**
- Export reports for government briefings
- Compare utility performance
- Identify investment priorities

### 3.2 Operations Dashboard (Utility Level)

**Purpose:** Day-to-day operations management

**Panels:**

1. **Alert Panel** (Left)
   - Real-time alerts sorted by severity
   - Click to expand details
   - Acknowledge/assign from here

2. **Pressure Trend** (Center)
   - 7-day pressure history
   - Highlighted anomaly periods
   - Click to drill into specific time

3. **AI Analysis** (Bottom)
   - Current leak probability
   - Model confidence level
   - Key contributing factors
   - Recommended actions

### 3.3 Field Dashboard (Technician Level)

**Purpose:** Mobile-optimized for field work

**Features:**
- Active work order details
- GPS navigation to site
- Step-by-step investigation guide
- Photo capture for documentation
- Report submission form

---

## 4. Field Investigation Procedures

### 4.1 Standard Investigation Steps

#### Step 1: Navigation
1. Open work order on mobile app
2. Click "Navigate" for GPS directions
3. Park safely near suspected location

#### Step 2: Visual Inspection
- Look for:
  - Wet spots on road/pavement
  - Unusually green vegetation
  - Sinkholes or ground settlement
  - Water pooling in drains
  - Discoloration on walls/fences

#### Step 3: Acoustic Testing
1. Use listening stick at valve covers
2. Listen at hydrants
3. Note any hissing or rushing sounds
4. Louder sound = closer to leak

#### Step 4: Pressure Measurement
1. Connect gauge to nearest hydrant
2. Record static pressure
3. Compare to expected value (from work order)
4. Pressure lower than expected = upstream leak

#### Step 5: Documentation
1. Take photos of:
   - General location
   - Any visible evidence
   - Pressure gauge reading
   - Equipment used
2. Add notes describing findings

### 4.2 Reporting Results

**Leak Confirmed:**
1. Select "Yes - Leak Confirmed" 
2. Mark actual location on map
3. Estimate severity (small/medium/large)
4. Take photos of visible leak
5. Note if immediate repair needed

**No Leak Found:**
1. Select "No - Area Clear"
2. Document investigation steps taken
3. Note any factors that may explain AI detection
4. Suggest if more investigation needed

**Inconclusive:**
1. Select "Inconclusive - Need More Investigation"
2. Document what was checked
3. Recommend next steps (e.g., acoustic logger deployment)

---

## 5. Feedback and Model Improvement

### 5.1 Why Feedback Matters

Your field feedback directly improves the AI:

- **Confirmed leaks** → Teaches AI what real leaks look like
- **False positives** → Helps AI avoid similar mistakes
- **Location accuracy** → Improves localization algorithm

### 5.2 Quality Feedback

**Good feedback:**
```
"Leak found at pipe joint, approximately 20m east of predicted 
location. Visible water on surface, confirmed with acoustic stick. 
Approximately 100mm repair clamp needed."
```

**Poor feedback:**
```
"Checked area, nothing found"
```

**Best practices:**
- Be specific about location
- Describe investigation method
- Note any unusual conditions
- Include photos

---

## 6. Troubleshooting

### 6.1 Dashboard Issues

| Issue | Solution |
|-------|----------|
| Page won't load | Clear browser cache, try different browser |
| Data not updating | Check internet connection, wait 60 seconds |
| Map not showing | Enable location services, refresh page |
| Login failed | Check caps lock, reset password if needed |

### 6.2 Alert Issues

| Issue | Solution |
|-------|----------|
| Too many alerts | Adjust sensitivity settings (contact admin) |
| Duplicate alerts | System should auto-merge, report if persists |
| Alert for known issue | Mark as "Known Issue" in notes |
| Missing expected alert | Check sensor connectivity |

### 6.3 Field App Issues

| Issue | Solution |
|-------|----------|
| GPS not working | Move outdoors, wait for signal |
| Photos not uploading | Save offline, sync when connected |
| Cannot submit report | Save draft, submit when back in coverage |
| Battery dying | Carry power bank, enable power saving mode |

---

## 7. Escalation Procedures

### 7.1 When to Escalate

**Escalate to Supervisor:**
- Unable to locate predicted leak after thorough investigation
- Leak found but repair beyond capability
- Safety concerns at site
- AI detection seems significantly wrong

**Escalate to Manager:**
- Multiple false positives in same area
- System performance concerns
- Resource constraints preventing response
- Customer complaints about service

### 7.2 Escalation Contacts

| Role | Phone | Email | Availability |
|------|-------|-------|--------------|
| Shift Supervisor | +260 xxx xxxx | supervisor@utility.zm | 24/7 |
| Operations Manager | +260 xxx xxxx | ops.manager@utility.zm | Working hours |
| Technical Support | +260 xxx xxxx | support@aquawatch.africa | 8AM-6PM |
| Emergency Line | 112 | - | 24/7 |

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **DMA** | District Metered Area - a defined zone with measured inflows |
| **NRW** | Non-Revenue Water - water produced but not billed |
| **MNF** | Minimum Night Flow - lowest flow, typically 2-4 AM |
| **Anomaly** | Deviation from expected pattern |
| **Baseline** | Historical normal behavior used for comparison |
| **Confidence** | How certain the AI is about its prediction |
| **Probability** | Likelihood that a leak exists (0-100%) |
| **Gradient** | Pressure difference between two points |
| **Hypertable** | TimescaleDB term for time-series table |
| **Edge Device** | Local controller at sensor site |

---

## 9. Quick Troubleshooting Flowchart

```
Alert Received
     │
     ▼
Is sensor online? ──No──► Check sensor status, 
     │                     wait for reconnection
    Yes
     │
     ▼
Review AI evidence
     │
     ▼
Probability > 60%? ──No──► Monitor, set reminder
     │                       to recheck in 24h
    Yes
     │
     ▼
Create work order
     │
     ▼
Assign technician
     │
     ▼
Investigate on site
     │
     ▼
Leak found? ──Yes──► Document, initiate repair
     │
     No
     │
     ▼
Thorough check? ──No──► Continue investigation
     │
    Yes
     │
     ▼
Mark as false positive,
submit detailed feedback
```

---

## 10. Performance Metrics

### 10.1 Your Targets

| Metric | Target | How Measured |
|--------|--------|--------------|
| Alert response time | < SLA by severity | Time from alert to acknowledgement |
| Investigation completion | 95% within SLA | Work orders completed on time |
| Feedback quality | 100% with notes | Work orders with detailed notes |
| False positive rate | < 20% | Investigations with no leak found |

### 10.2 Dashboard Performance Indicators

Look for these on your dashboard:

- 🟢 **Green**: Meeting targets
- 🟡 **Yellow**: Approaching threshold
- 🔴 **Red**: Action required

---

## Support

**Technical Support:**
- Phone: +260 xxx xxxx
- Email: support@aquawatch.africa
- Hours: Monday-Friday, 8:00 AM - 6:00 PM

**Emergency (Water Main Break):**
- Call: 112
- Then: Log in system for tracking

**Feedback on this manual:**
- Email: training@aquawatch.africa
