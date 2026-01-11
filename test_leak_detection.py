"""
TEST: Does the AI ACTUALLY detect leaks?
=========================================
This script tests the anomaly detection with real-like data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from datetime import datetime, timedelta

# Import our AI module
from src.ai.anomaly_detector import (
    AnomalyDetectionEngine,
    AnomalyType,
    StatisticalDetector,
    PressureBaseline
)

print("=" * 60)
print("  LEAK DETECTION TEST - Does the AI Actually Work?")
print("=" * 60)

# Initialize the detection engine
engine = AnomalyDetectionEngine()

# ============================================================
# TEST 1: Learn what NORMAL looks like
# ============================================================
print("\n📊 TEST 1: Training on NORMAL pressure data...")
print("-" * 40)

# Simulate 24 hours of normal data (1 reading per minute)
np.random.seed(42)
normal_pressures = []
normal_flows = []

for hour in range(24):
    for minute in range(60):
        # Normal pressure varies by time of day
        base_pressure = 3.0  # 3 bar base
        
        # Higher demand (lower pressure) during peak hours
        if 6 <= hour <= 9 or 18 <= hour <= 21:
            base_pressure -= 0.3  # Morning/evening peak
        elif 0 <= hour <= 5:
            base_pressure += 0.2  # Night (minimum flow)
        
        # Add realistic noise
        pressure = base_pressure + np.random.normal(0, 0.1)
        flow = 100 + np.random.normal(0, 10)  # ~100 L/min average
        
        normal_pressures.append(pressure)
        normal_flows.append(flow)
        
        # Feed to engine
        timestamp = datetime.now() - timedelta(hours=24) + timedelta(hours=hour, minutes=minute)
        result = engine.process_reading(
            pipe_id="PIPE-001",
            pressure=pressure,
            flow=flow,
            timestamp=timestamp
        )

print(f"✅ Trained on {len(normal_pressures)} normal readings")
print(f"   Normal pressure range: {min(normal_pressures):.2f} - {max(normal_pressures):.2f} bar")
print(f"   Average pressure: {np.mean(normal_pressures):.2f} bar")

# ============================================================
# TEST 2: Can it detect a SUDDEN LEAK (pressure drop)?
# ============================================================
print("\n🔴 TEST 2: Simulating SUDDEN LEAK (pressure drop)...")
print("-" * 40)

# Simulate a leak - sudden pressure drop of 0.8 bar
leak_pressure = 2.2  # Dropped from ~3.0 to 2.2
leak_flow = 150  # Flow increased (water escaping)

timestamp = datetime.now()
result = engine.process_reading(
    pipe_id="PIPE-001",
    pressure=leak_pressure,
    flow=leak_flow,
    timestamp=timestamp
)

print(f"   Input: Pressure={leak_pressure} bar, Flow={leak_flow} L/min")
print(f"   Detected: {result.anomaly_type.value}")
print(f"   Confidence: {result.confidence*100:.1f}%")
print(f"   Severity: {result.severity}")
print(f"   Expected pressure: {result.expected_pressure:.2f} bar")
print(f"   Deviation: {result.deviation:.2f} bar")

if result.anomaly_type != AnomalyType.NORMAL:
    print("   ✅ LEAK DETECTED!")
else:
    print("   ❌ MISSED THE LEAK!")

# ============================================================
# TEST 3: Can it detect a GRADUAL LEAK?
# ============================================================
print("\n🟡 TEST 3: Simulating GRADUAL LEAK (slow pressure drop)...")
print("-" * 40)

# Reset for new pipe
engine2 = AnomalyDetectionEngine()

# Train on normal
for i in range(500):
    pressure = 3.0 + np.random.normal(0, 0.1)
    flow = 100 + np.random.normal(0, 10)
    engine2.process_reading("PIPE-002", pressure, flow, datetime.now() - timedelta(minutes=500-i))

# Now simulate gradual leak - pressure drops slowly over 30 minutes
gradual_detections = []
for i in range(30):
    # Pressure drops 0.03 bar per minute
    pressure = 3.0 - (i * 0.03) + np.random.normal(0, 0.05)
    flow = 100 + (i * 2) + np.random.normal(0, 5)  # Flow increases slowly
    
    result = engine2.process_reading("PIPE-002", pressure, flow, datetime.now() + timedelta(minutes=i))
    
    if result.anomaly_type != AnomalyType.NORMAL:
        gradual_detections.append(i)
        print(f"   Minute {i}: Pressure={pressure:.2f} bar → {result.anomaly_type.value} (confidence: {result.confidence*100:.1f}%)")

if gradual_detections:
    print(f"   ✅ Gradual leak detected at minute {gradual_detections[0]}")
else:
    print("   ❌ Gradual leak NOT detected")

# ============================================================
# TEST 4: Does it avoid FALSE POSITIVES?
# ============================================================
print("\n🟢 TEST 4: Testing FALSE POSITIVE rate...")
print("-" * 40)

# Feed 100 normal readings and count false alarms
false_positives = 0
for i in range(100):
    pressure = 3.0 + np.random.normal(0, 0.1)
    flow = 100 + np.random.normal(0, 10)
    
    result = engine.process_reading("PIPE-001", pressure, flow, datetime.now() + timedelta(minutes=i))
    
    if result.anomaly_type != AnomalyType.NORMAL:
        false_positives += 1

print(f"   Normal readings tested: 100")
print(f"   False alarms: {false_positives}")
print(f"   False positive rate: {false_positives}%")

if false_positives < 10:
    print("   ✅ Low false positive rate - GOOD!")
else:
    print("   ⚠️ High false positive rate - needs tuning")

# ============================================================
# TEST 5: Statistical Detection Test
# ============================================================
print("\n📈 TEST 5: Statistical Detection (Z-score)...")
print("-" * 40)

stat_detector = StatisticalDetector(z_threshold=2.5)

# Normal reading
is_anomaly, score = stat_detector.detect(
    value=3.0,      # Current pressure
    mean=3.0,       # Historical mean
    std=0.1,        # Historical std dev
    q25=2.9,
    q75=3.1
)
print(f"   Normal reading (3.0 bar, mean=3.0): Anomaly={is_anomaly}, Score={score:.2f}")

# Anomalous reading
is_anomaly, score = stat_detector.detect(
    value=2.2,      # Dropped pressure
    mean=3.0,       # Historical mean
    std=0.1,        # Historical std dev
    q25=2.9,
    q75=3.1
)
print(f"   Leak reading (2.2 bar, mean=3.0): Anomaly={is_anomaly}, Score={score:.2f}")

if is_anomaly:
    print("   ✅ Statistical detection WORKS!")
else:
    print("   ❌ Statistical detection FAILED!")


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("  SUMMARY: Does the AI Work?")
print("=" * 60)

tests_passed = 0
total_tests = 4

# Check results
if result.anomaly_type != AnomalyType.NORMAL:
    tests_passed += 1
    print("✅ TEST 2 (Sudden leak): PASSED")
else:
    print("❌ TEST 2 (Sudden leak): FAILED")

if gradual_detections:
    tests_passed += 1
    print("✅ TEST 3 (Gradual leak): PASSED")
else:
    print("❌ TEST 3 (Gradual leak): FAILED")

if false_positives < 10:
    tests_passed += 1
    print("✅ TEST 4 (Low false positives): PASSED")
else:
    print("❌ TEST 4 (Low false positives): FAILED")

if is_anomaly:
    tests_passed += 1
    print("✅ TEST 5 (Statistical): PASSED")
else:
    print("❌ TEST 5 (Statistical): FAILED")

print(f"\nResult: {tests_passed}/{total_tests} tests passed")

if tests_passed >= 3:
    print("\n🎉 YES - The AI CAN detect leaks!")
else:
    print("\n⚠️ The AI needs more work")
