#!/usr/bin/env python3
"""
DEMONSTRATION: How AI Distinguishes USAGE vs LEAKAGE
=====================================================

The hardest problem in water leak detection:
"Is this pressure drop because someone is using water, or because there's a leak?"

This script shows the AI's approach to solving this.
"""

import sys
sys.path.insert(0, '.')
import numpy as np
from datetime import datetime, timedelta

print("=" * 70)
print("   🚿 USAGE vs 💧 LEAKAGE - How Does the AI Know the Difference?")
print("=" * 70)

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    THE CORE PROBLEM                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  When pressure drops, it could mean:                                │
│    A) Someone opened a tap (NORMAL USAGE) ✓                         │
│    B) A pipe is leaking (LEAK) ⚠️                                   │
│                                                                     │
│  Both cause pressure to drop!                                       │
│  How does the AI tell them apart?                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "─" * 70)
print("METHOD 1: MINIMUM NIGHT FLOW (MNF) ANALYSIS")
print("─" * 70)
print("""
The SMARTEST technique: Analyze water flow at 2am-4am

At 2am-4am:
  • Most people are sleeping
  • Almost NO legitimate water usage
  • Any flow during this time = LEAKAGE!

This is the IWA (International Water Association) standard method.
""")

# Simulate MNF analysis
print("SIMULATION: 24-Hour Flow Pattern")
print("-" * 50)

hours = list(range(24))
usage_pattern = {
    0: 5, 1: 3, 2: 2, 3: 2, 4: 3, 5: 8,        # Night/early morning
    6: 45, 7: 80, 8: 65, 9: 40, 10: 30,         # Morning peak
    11: 35, 12: 50, 13: 45, 14: 35, 15: 30,     # Midday
    16: 40, 17: 60, 18: 85, 19: 75, 20: 55,     # Evening peak
    21: 40, 22: 25, 23: 10                       # Night
}

# Add some base leakage (10 m³/h)
LEAKAGE_RATE = 10  # This is the hidden leak!

print("\nHour  | Usage | + Leak | Total Flow | Analysis")
print("-" * 60)
for hour in hours:
    usage = usage_pattern[hour]
    total = usage + LEAKAGE_RATE
    
    if 2 <= hour <= 4:
        analysis = f"⚠️ MNF={total} m³/h (should be ~2) → LEAK DETECTED!"
    elif hour in [7, 18, 19]:
        analysis = "Peak usage time - hard to detect leak"
    else:
        analysis = "Normal"
    
    bar = "█" * (total // 5)
    print(f" {hour:02d}:00 |  {usage:3d}  |  +{LEAKAGE_RATE}   |    {total:3d}     | {analysis}")

print("""
📊 RESULT: 
   - Expected MNF (no leak): ~2-5 m³/h (toilet flushes, fridge, etc.)
   - Actual MNF measured: 12-15 m³/h
   - Excess flow: 10 m³/h = THE LEAK!
   
The AI monitors MNF every night to detect leaks!
""")

print("\n" + "─" * 70)
print("METHOD 2: PRESSURE-FLOW CORRELATION")
print("─" * 70)
print("""
KEY INSIGHT: Usage and leaks create DIFFERENT patterns

┌─────────────────────────────────────────────────────────────────────┐
│  NORMAL USAGE (someone opens tap):                                  │
│    • Pressure drops ↓                                               │
│    • Flow INCREASES ↑ (water going to customer)                     │
│    • Customer meter REGISTERS the water                             │
│    • Pattern: SHORT duration, then RECOVERS                         │
│                                                                     │
│  LEAK:                                                              │
│    • Pressure drops ↓                                               │
│    • Flow increases but NOT to customer meters                      │
│    • Customer meters DON'T register this water                      │
│    • Pattern: CONTINUOUS, doesn't recover                           │
└─────────────────────────────────────────────────────────────────────┘
""")

print("SIMULATION: Usage Event vs Leak Event")
print("-" * 50)

print("\n📊 Scenario A: Someone takes a shower (7:15 AM)")
print("Time     | Pressure | Flow  | Customer Meter | Status")
print("-" * 60)
events_usage = [
    ("07:14", 3.2, 50, 50, "Normal baseline"),
    ("07:15", 3.0, 65, 65, "Shower started - pressure drops, meter reads"),
    ("07:16", 2.9, 70, 70, "Shower continues"),
    ("07:20", 2.9, 68, 68, "Still showering"),
    ("07:25", 3.1, 52, 52, "Shower ended - RECOVERS!"),
    ("07:30", 3.2, 50, 50, "Back to normal ✓"),
]
for time, pressure, flow, meter, status in events_usage:
    print(f" {time}  |  {pressure:.1f} bar |  {flow} m³/h |     {meter} m³/h     | {status}")

print("\n→ AI VERDICT: NORMAL USAGE (flow matches meter, pattern recovers)")

print("\n" + "-" * 50)
print("\n📊 Scenario B: Underground pipe leak")
print("Time     | Pressure | Flow  | Customer Meter | Status")
print("-" * 60)
events_leak = [
    ("07:14", 3.2, 50, 50, "Normal baseline"),
    ("07:15", 3.0, 65, 50, "⚠️ Flow up but meter SAME!"),
    ("07:16", 2.9, 68, 50, "⚠️ Gap increasing..."),
    ("07:20", 2.8, 70, 51, "⚠️ 19 m³/h UNACCOUNTED!"),
    ("07:25", 2.7, 72, 52, "⚠️ Still leaking - NO RECOVERY"),
    ("07:30", 2.6, 74, 52, "⚠️ Getting worse!"),
]
for time, pressure, flow, meter, status in events_leak:
    diff = flow - meter
    marker = "⚠️" if diff > 5 else ""
    print(f" {time}  |  {pressure:.1f} bar |  {flow} m³/h |     {meter} m³/h     | {status}")

print("\n→ AI VERDICT: LEAK DETECTED!")
print("   • Flow increased by 24 m³/h")
print("   • Customer meters only show 2 m³/h increase")
print("   • 22 m³/h is UNACCOUNTED = LEAKAGE!")

print("\n" + "─" * 70)
print("METHOD 3: PATTERN RECOGNITION")
print("─" * 70)
print("""
The AI learns typical USAGE patterns:

┌─────────────────────────────────────────────────────────────────────┐
│  USAGE SIGNATURES (AI learns these):                                │
│                                                                     │
│  🚿 Shower:    ~10 min, 8-12 L/min, morning/evening                 │
│  🚽 Toilet:    ~30 sec spike, 6-9 L, random times                   │
│  🍽️ Dishes:    ~15 min, 6-8 L/min, after meals                      │
│  🌱 Garden:    ~30-60 min, 10-15 L/min, morning/evening             │
│  🏭 Industrial: Scheduled patterns, large volumes                    │
│                                                                     │
│  LEAK SIGNATURES (different!):                                      │
│                                                                     │
│  💧 Small leak:   Constant 1-5 L/min, 24/7, no pattern              │
│  💦 Medium leak:  Constant 5-20 L/min, pressure-dependent           │
│  🌊 Major leak:   Sudden onset, continuous, growing                  │
└─────────────────────────────────────────────────────────────────────┘
""")

print("SIMULATION: Pattern Analysis")
print("-" * 50)

patterns = [
    ("Toilet flush", "▁▁▁█████▁▁▁", "30 sec spike, then stops", "USAGE ✓"),
    ("Shower", "▁▂▄██████▄▂▁", "10 min plateau, then stops", "USAGE ✓"),
    ("Small leak", "▃▃▃▃▃▃▃▃▃▃▃▃", "Constant, never stops", "LEAK! ⚠️"),
    ("Burst pipe", "▁▁▁▁████████", "Sudden start, continuous", "LEAK! ⚠️"),
]

print("\nEvent Type    | Flow Pattern (1 hour) | Description              | AI Verdict")
print("-" * 85)
for name, pattern, desc, verdict in patterns:
    print(f" {name:12} | {pattern:21} | {desc:24} | {verdict}")

print("\n" + "─" * 70)
print("METHOD 4: IWA WATER BALANCE")
print("─" * 70)
print("""
The mathematical proof of leakage:

┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   WATER BALANCE EQUATION:                                           │
│                                                                     │
│   System Input (bulk meter)                                         │
│        -                                                            │
│   Authorized Consumption (customer meters + unbilled)               │
│        =                                                            │
│   WATER LOSSES (leakage + theft + meter errors)                     │
│                                                                     │
│   If Input = 1000 m³/day                                            │
│   And Consumption = 700 m³/day                                      │
│   Then Losses = 300 m³/day (30% NRW!)                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")

print("EXAMPLE CALCULATION:")
print("-" * 50)
print("  System Input (DMA bulk meter):     1,000 m³/day")
print("  - Billed metered consumption:      - 650 m³/day")
print("  - Unbilled authorized (flushing):  -  50 m³/day")
print("  " + "-" * 45)
print("  = WATER LOSSES:                      300 m³/day")
print("")
print("  Of which:")
print("    Real Losses (leakage):           ~250 m³/day (estimated from MNF)")
print("    Apparent Losses (theft, errors): ~ 50 m³/day")

print("\n" + "=" * 70)
print("   🎯 SUMMARY: How AI Knows It's NOT Just Usage")
print("=" * 70)
print("""
The AI uses MULTIPLE methods together:

1. ⏰ TIME CHECK
   → Is it 2-4am? Any flow = likely leakage (MNF method)
   
2. 📊 FLOW vs METER CHECK  
   → Does bulk meter match sum of customer meters?
   → Difference = unaccounted water = leakage
   
3. 📈 PATTERN CHECK
   → Usage: starts, runs, STOPS
   → Leak: starts, runs FOREVER
   
4. ⚖️ WATER BALANCE CHECK
   → Input - Consumption = Losses
   → Math doesn't lie!
   
5. 🔄 RECOVERY CHECK
   → Usage: pressure recovers after event
   → Leak: pressure stays low or gets worse

When MULTIPLE indicators agree → HIGH CONFIDENCE leak detection!
""")
print("=" * 70)
