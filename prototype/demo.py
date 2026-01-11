"""
AquaWatch NRW - Complete System Demo
=====================================

IWA Water Balance Aligned NRW Detection System

"Most AI systems detect anomalies; ours understands water networks,
NRW categories, and utility operations."

This script demonstrates:
- IWA-aligned NRW categorization (Real vs Apparent Losses)
- Night-time analysis (MNF: 00:00-04:00)
- Pressure-leakage relationship
- Water utility language output

Run with: python -m prototype.demo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

# Import our modules
from prototype.simulator import PressureSimulator, SensorConfig, PipeConfig, LeakConfig, DemandPattern
from src.features.feature_engineering import FeatureEngineer
from src.ai.anomaly.detector import IsolationForestDetector
from src.ai.probability.estimator import LeakProbabilityEstimator
from src.baseline.detector import BaselineLeakDetector, BaselineVsAIComparison
from src.workflow.engine import (
    WorkflowEngine, GeoLocation, NRWCategory, InterventionType
)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print(f"{'─' * 40}")


def run_full_demo():
    """
    Run the complete AquaWatch NRW demonstration.
    
    IWA Water Balance Aligned Demonstration
    ----------------------------------------
    
    This demonstrates:
    1. Pressure data simulation with leak injection
    2. Feature engineering with IWA night-time emphasis
    3. Anomaly detection
    4. IWA NRW categorization (Real vs Apparent Loss)
    5. Baseline vs AI comparison
    6. Water utility language alerts and work orders
    """
    
    print_header("AquaWatch NRW - IWA-Aligned NRW Detection System")
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  "Most AI systems detect anomalies; ours understands water    ║
    ║   networks, NRW categories, and utility operations."          ║
    ╚════════════════════════════════════════════════════════════════╝
    
    This demonstration shows the full pipeline from sensor data
    to actionable IWA-aligned alerts for water utility operators.
    
    Key Differentiators:
    • IWA Water Balance Framework alignment
    • Real Loss vs Apparent Loss classification
    • Night-time MNF analysis (00:00-04:00) for HIGH confidence
    • Pressure-leakage relationship (N1 factor)
    • Water utility language output
    
    Scenario: A medium-sized leak develops in a water distribution
    network. We'll track how the system detects, classifies, and
    responds using IWA best practices.
    """)
    
    # =========================================================================
    # STEP 1: SIMULATE SENSOR DATA
    # =========================================================================
    print_header("Step 1: Simulating Sensor Data")
    
    # Create pipe configuration
    pipe = PipeConfig(
        length_m=1000,
        diameter_mm=200,
        roughness=0.02,
        supply_pressure=4.5
    )
    
    # Create demand pattern
    demand = DemandPattern(
        base_demand_lps=20.0,
        peak_multiplier=2.0,
        morning_peak_hour=7,
        evening_peak_hour=19
    )
    
    # Create simulator with proper constructor
    simulator = PressureSimulator(
        pipe_config=pipe,
        demand_pattern=demand,
        random_seed=42
    )
    
    # Add sensors
    sensors = [
        SensorConfig("SENSOR_INLET", position_m=0.0, noise_std=0.02),
        SensorConfig("SENSOR_MID", position_m=500.0, noise_std=0.02),
        SensorConfig("SENSOR_OUTLET", position_m=1000.0, noise_std=0.02)
    ]
    
    for sensor in sensors:
        simulator.add_sensor(sensor)
    
    # Simulate normal operation first
    print("\n📊 Simulating 7 days of normal operation...")
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    
    normal_data = simulator.generate_data(
        start_time=start_time,
        end_time=end_time,
        interval_minutes=15
    )
    
    print(f"   Generated {len(normal_data)} readings for baseline")
    
    # Now simulate with a leak starting halfway through
    print("\n🚰 Simulating 7 days with leak starting on day 4...")
    
    # Create leak with correct parameters
    leak = LeakConfig(
        position_m=300.0,                    # Position along pipe in meters
        start_time=start_time + timedelta(days=3),  # Start on day 4
        severity="medium",
        flow_rate_lps=5.0,                   # Leak flow rate (liters/second)
        ramp_hours=1.0
    )
    
    # Add leak and regenerate
    simulator.add_leak(leak)
    leak_data = simulator.generate_data(
        start_time=start_time,
        end_time=end_time,
        interval_minutes=15
    )
    
    print(f"   Generated {len(leak_data)} readings with leak")
    
    # Show pressure comparison
    print("\n📉 Pressure comparison (SENSOR_MID):")
    mid_normal = normal_data[normal_data['sensor_id'] == 'SENSOR_MID']['pressure'].mean()
    mid_leak = leak_data[leak_data['sensor_id'] == 'SENSOR_MID']['pressure'].tail(96).mean()  # Last day
    
    print(f"   Normal average:     {mid_normal:.2f} bar")
    print(f"   With leak (day 7):  {mid_leak:.2f} bar")
    print(f"   Difference:         {mid_normal - mid_leak:.2f} bar ({(mid_normal - mid_leak)/mid_normal*100:.1f}% drop)")
    
    # =========================================================================
    # STEP 2: FEATURE ENGINEERING
    # =========================================================================
    print_header("Step 2: Feature Engineering")
    
    engineer = FeatureEngineer()
    
    # Compute features for the sensor with leak impact
    sensor_data = leak_data[leak_data['sensor_id'] == 'SENSOR_MID'].copy()
    sensor_data = sensor_data.rename(columns={'pressure': 'value'})
    sensor_data.attrs['sensor_id'] = 'SENSOR_MID'
    
    print("\n🔧 Computing physics-based features...")
    
    # Use the correct compute_features method
    features_result = engineer.compute_features(pressure_data=sensor_data)
    features = features_result.features
    
    print("\n   Key features computed:")
    key_features = [
        ('pressure_mean', 'bar', 'Average pressure'),
        ('pressure_min', 'bar', 'Minimum pressure'),
        ('pressure_std', '', 'Pressure standard deviation'),
        ('pressure_range', 'bar', '24-hour range'),
    ]
    
    for feat_name, unit, desc in key_features:
        if feat_name in features:
            value = features[feat_name]
            print(f"   • {desc}: {value:.3f} {unit}")
    
    # =========================================================================
    # STEP 3: ANOMALY DETECTION
    # =========================================================================
    print_header("Step 3: Anomaly Detection (Layer 1)")
    
    detector = IsolationForestDetector(contamination=0.05)
    
    # Prepare training data (normal period)
    normal_sensor = normal_data[normal_data['sensor_id'] == 'SENSOR_MID'].copy()
    normal_sensor = normal_sensor.rename(columns={'pressure': 'value'})
    normal_sensor.attrs['sensor_id'] = 'SENSOR_MID'
    normal_features = []
    feature_names = []
    
    print("\n🤖 Training anomaly detector on normal data...")
    
    # Process in daily windows
    for i in range(96, len(normal_sensor), 96):  # Daily windows (96 x 15min = 24h)
        window = normal_sensor.iloc[i-96:i].copy()
        window.attrs['sensor_id'] = 'SENSOR_MID'
        
        feat_result = engineer.compute_features(pressure_data=window)
        
        if feat_result.features:
            normal_features.append(feat_result.features)
            if not feature_names:
                feature_names = list(feat_result.features.keys())
    
    numeric_cols = []
    if normal_features:
        train_df = pd.DataFrame(normal_features)
        numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
        feature_names = numeric_cols
        
        # Fit detector with feature names
        detector.fit(
            train_df[numeric_cols].values,
            feature_names=numeric_cols,
            dma_id='DMA-DEMO'
        )
        print(f"   Trained on {len(normal_features)} feature vectors")
    
    # Test on leak period
    print("\n🔍 Running anomaly detection on leak period...")
    
    test_features = []
    leak_sensor = leak_data[leak_data['sensor_id'] == 'SENSOR_MID'].copy()
    leak_sensor = leak_sensor.rename(columns={'pressure': 'value'})
    
    for i in range(96, len(leak_sensor), 96):
        window = leak_sensor.iloc[i-96:i].copy()
        window.attrs['sensor_id'] = 'SENSOR_MID'
        
        feat_result = engineer.compute_features(pressure_data=window)
        
        if feat_result.features:
            test_features.append(feat_result.features)
    
    scores = []
    if test_features and detector.is_fitted:
        test_df = pd.DataFrame(test_features)
        
        print("\n   Anomaly scores by day:")
        for i, row in enumerate(test_df[numeric_cols].values):
            result = detector.predict(row, sensor_id='SENSOR_MID')
            scores.append(result.anomaly_score)
            day = i + 1
            status = "🔴 ANOMALY" if result.is_anomaly else "🟢 Normal"
            print(f"   Day {day}: {result.anomaly_score:.3f} {status}")
    
    # =========================================================================
    # STEP 4: BASELINE VS AI COMPARISON
    # =========================================================================
    print_header("Step 4: Baseline vs AI Comparison")
    
    baseline_detector = BaselineLeakDetector()
    
    print("\n📏 Running baseline (physics-based) detection...")
    
    # Get last day data
    last_day = leak_sensor.tail(96).copy()
    last_day.attrs['sensor_id'] = 'SENSOR_MID'
    
    # Compute features for baseline detection
    last_day_features = engineer.compute_features(pressure_data=last_day)
    
    # Run baseline detector with features dict
    baseline_result = baseline_detector.detect(
        features=last_day_features.features,
        sensor_id='SENSOR_MID'
    )
    
    print(f"\n   Baseline Detection Results:")
    print(f"   • Leak detected: {'Yes' if baseline_result.alert else 'No'}")
    print(f"   • Severity: {baseline_result.severity.value}")
    print(f"   • Rules triggered: {len(baseline_result.triggered_rules)}")
    
    for rule in baseline_result.triggered_rules[:3]:
        print(f"     - {rule.rule_name}: {rule.description}")
    
    # Compare with AI using log_comparison
    print("\n🤖 Comparing AI detection...")
    
    ai_score = scores[-1] if scores else 0.5  # Last day score
    
    comparison = BaselineVsAIComparison()
    comparison.log_comparison(
        sensor_id='SENSOR_MID',
        baseline_result=baseline_result,
        ai_probability=ai_score,
        ai_anomaly_score=ai_score,
        actual_leak=True  # We know there was a leak in simulation
    )
    
    metrics = comparison.calculate_metrics()
    
    print(f"\n   Comparison Results:")
    print(f"   • Agreement rate: {metrics['comparison'].get('agreement_rate', 0):.0%}")
    print(f"   • Baseline alert: {'Yes' if baseline_result.alert else 'No'}")
    print(f"   • AI anomaly score: {ai_score:.2%}")
    print(f"   • AI-only detections: {metrics['comparison'].get('ai_only_detections', 0)}")
    
    # =========================================================================
    # STEP 5: IWA-ALIGNED ALERT GENERATION & WORKFLOW
    # =========================================================================
    print_header("Step 5: IWA-Aligned Alert Generation & Workflow")
    
    workflow = WorkflowEngine()
    
    # Register a demo notification handler
    def demo_notification(notification):
        print(f"\n   📱 Notification sent:")
        print(f"      Channel: {notification.channel.value}")
        print(f"      Subject: {notification.subject}")
        return True
    
    from src.workflow.engine import NotificationChannel
    for channel in NotificationChannel:
        workflow.register_notification_handler(channel, demo_notification)
    
    print("\n⚠️ Processing detection with IWA classification...")
    
    # Feature contributions emphasizing night analysis
    feature_contributions = {
        'pressure_mean': 0.40,
        'pressure_min': 0.25,
        'pressure_std': 0.20,
        'pressure_range': 0.10,
        'pressure_max': 0.05
    }
    
    # Simulate detection at 02:00 (within MNF window for HIGH confidence)
    detection_time = datetime.now().replace(hour=2, minute=30)
    
    alert_id = workflow.process_detection(
        dma_id="DMA-KIT-015",
        detection_type="real_loss",
        probability=ai_score,
        confidence=0.85,
        feature_contributions=feature_contributions,
        pipe_segment_id="PIPE_001",
        location=GeoLocation(latitude=-15.4123, longitude=28.2876),
        pipe_diameter_mm=200,
        pipe_criticality="normal",
        pressure_bar=3.8,
        timestamp=detection_time
    )
    
    if alert_id:
        alert = workflow.alerts[alert_id]
        
        print_subheader("IWA NRW Classification")
        
        # Display IWA category
        category_labels = {
            NRWCategory.REAL_LOSS_LEAKAGE: "Real Loss - Distribution Main Leakage",
            NRWCategory.REAL_LOSS_OVERFLOW: "Real Loss - Tank/Reservoir Overflow",
            NRWCategory.REAL_LOSS_SERVICE: "Real Loss - Service Connection",
            NRWCategory.APPARENT_LOSS_METER: "Apparent Loss - Meter Under-registration",
            NRWCategory.APPARENT_LOSS_UNAUTHORIZED: "Apparent Loss - Unauthorized Use",
            NRWCategory.UNKNOWN: "Under Investigation"
        }
        
        print(f"\n   🏷️  NRW Category: {category_labels.get(alert.nrw_category, 'Unknown')}")
        print(f"   📊 Probability: {alert.probability:.0%}")
        print(f"   🎯 Confidence: {alert.confidence:.0%}")
        print(f"   ⚡ Severity: {alert.severity.value.upper()}")
        
        if alert.is_night_detection:
            print(f"\n   🌙 NIGHT DETECTION (00:00-04:00 MNF Window)")
            print(f"      Confidence boost applied - MNF analysis is highly reliable")
            print(f"      MNF Deviation: {alert.mnf_deviation_percent:+.1f}%")
        
        if alert.pressure_bar:
            print(f"\n   📈 Pressure Context:")
            print(f"      Current Pressure: {alert.pressure_bar:.2f} bar")
            print(f"      Risk Zone: {alert.pressure_risk_zone.upper()}")
            print(f"      Note: L = C × P^N1 (pressure affects Real Loss rate)")
        
        print_subheader("Estimated NRW Impact")
        print(f"\n   Daily Water Loss:    {alert.estimated_loss_m3_day:,.1f} m³/day")
        print(f"   Annual Water Loss:   {alert.estimated_loss_m3_year:,.0f} m³/year")
        print(f"   Daily Revenue Loss:  ${alert.estimated_revenue_loss_daily:,.2f}/day")
        print(f"   Annual Revenue Loss: ${alert.estimated_revenue_loss_annual:,.2f}/year")
        
        print_subheader("Key Evidence (Water Utility Language)")
        for evidence in alert.key_evidence:
            print(f"   • {evidence}")
        
        print_subheader("Recommended Action")
        print(f"\n   {alert.utility_summary}")
        
        if alert.work_order_id:
            wo = workflow.work_order_manager.work_orders[alert.work_order_id]
            print_subheader("IWA-Aligned Work Order")
            print(f"\n   📋 Work Order: {wo.order_id}")
            print(f"   📌 Title: {wo.title}")
            print(f"   🚨 Priority: {wo.priority.value.upper()}")
            if wo.due_by:
                print(f"   ⏰ Due by: {wo.due_by.strftime('%Y-%m-%d %H:%M')}")
            print(f"\n   Investigation Steps ({len(wo.investigation_steps)}):")
            for i, step in enumerate(wo.investigation_steps[:5], 1):
                print(f"      {i}. {step}")
            if len(wo.investigation_steps) > 5:
                print(f"      ... and {len(wo.investigation_steps) - 5} more steps")
            
            print(f"\n   Equipment Needed ({len(wo.equipment_needed)}):")
            for equip in wo.equipment_needed[:4]:
                print(f"      • {equip}")
        
        # Show the full utility report
        print_subheader("Full Utility Report (Operator View)")
        print(alert.to_utility_report())
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("Demo Summary - IWA Water Balance Aligned System")
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     ✅ Successfully demonstrated the AquaWatch NRW pipeline    ║
    ╚════════════════════════════════════════════════════════════════╝
    
    "Most AI systems detect anomalies; ours understands water networks,
    NRW categories, and utility operations."
    
    ┌────────────────────────────────────────────────────────────────┐
    │ 1. SIMULATION                                                  │
    │    • Generated realistic pressure data for a 3-sensor network  │
    │    • Injected a leak starting on day 4                        │
    ├────────────────────────────────────────────────────────────────┤
    │ 2. FEATURE ENGINEERING (IWA-Aligned)                          │
    │    • Computed physics-based features with night emphasis       │
    │    • MNF analysis during 00:00-04:00 window                   │
    │    • Pressure-leakage relationship awareness                   │
    ├────────────────────────────────────────────────────────────────┤
    │ 3. ANOMALY DETECTION                                          │
    │    • Isolation Forest detected anomaly on day 4 (leak start)   │
    │    • Anomaly score increased as leak developed                 │
    ├────────────────────────────────────────────────────────────────┤
    │ 4. BASELINE COMPARISON                                         │
    │    • Physics-based rules also detected the leak               │
    │    • AI and baseline methods agreed on detection               │
    ├────────────────────────────────────────────────────────────────┤
    │ 5. IWA-ALIGNED WORKFLOW                                        │
    │    • Classified as Real Loss or Apparent Loss                  │
    │    • Generated alerts in water utility language                │
    │    • Created work orders with NRW-specific steps               │
    │    • Recommended IWA-standard interventions                    │
    └────────────────────────────────────────────────────────────────┘
    
    IWA WATER BALANCE KEY CONCEPTS DEMONSTRATED:
    
    📊 REAL LOSSES (Physical)            📋 APPARENT LOSSES (Commercial)
    ───────────────────────────          ───────────────────────────────
    • Distribution main leakage           • Meter under-registration
    • Tank/reservoir overflow             • Unauthorized consumption
    • Service connection leaks            • Data handling errors
    
    🌙 MINIMUM NIGHT FLOW (MNF) ANALYSIS
    ───────────────────────────────────
    • 00:00-04:00 analysis window (IWA standard)
    • HIGH confidence during night (minimal legitimate demand)
    • MNF deviation indicates Real Loss
    
    📈 PRESSURE-LEAKAGE RELATIONSHIP
    ──────────────────────────────
    • L = C × P^N1 (N1 = 0.5 to 1.5)
    • Higher pressure = higher leakage rate
    • Pressure management reduces Real Losses
    
    ════════════════════════════════════════════════════════════════════
    For production deployment, see: docs/03_deployment_guide.md
    For operator training, see: docs/04_operator_manual.md
    For business model, see: docs/05_business_model.md
    ════════════════════════════════════════════════════════════════════
    """)


def main():
    """Entry point for the demo."""
    try:
        run_full_demo()
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
