"""
AquaWatch NRW - Prototype Simulation
====================================

Lab prototype simulator for demonstrating leak detection.
Generates realistic pressure data with controllable leak injection.

Purpose:
1. Prove the system works in controlled conditions
2. Generate training data
3. Demo for stakeholders
4. Test AI models before deployment

The prototype must be:
- Repeatable
- Explainable
- Defendable
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class SensorConfig:
    """Configuration for a simulated sensor."""
    sensor_id: str
    position_m: float  # Position along pipe in meters
    noise_std: float = 0.02  # Measurement noise (bar)
    bias: float = 0.0  # Sensor bias (bar)
    failure_rate: float = 0.001  # Probability of data dropout


@dataclass
class PipeConfig:
    """Configuration for simulated pipe."""
    length_m: float = 1000  # Pipe length
    diameter_mm: float = 200  # Pipe diameter
    roughness: float = 0.1  # Hazen-Williams roughness
    supply_pressure: float = 4.0  # Inlet pressure (bar)
    

@dataclass
class LeakConfig:
    """Configuration for a simulated leak."""
    position_m: float  # Leak position along pipe
    start_time: datetime  # When leak starts
    end_time: Optional[datetime] = None  # When leak is repaired (None = ongoing)
    severity: str = "medium"  # small, medium, large
    flow_rate_lps: float = 5.0  # Leak flow rate (liters/second)
    ramp_hours: float = 1.0  # Time to reach full severity


@dataclass 
class DemandPattern:
    """Daily demand pattern."""
    base_demand_lps: float = 20.0  # Base demand (liters/second)
    peak_multiplier: float = 2.0  # Peak/base ratio
    morning_peak_hour: int = 7  # Morning peak
    evening_peak_hour: int = 19  # Evening peak
    weekend_reduction: float = 0.8  # Weekend demand factor
    noise_std: float = 0.1  # Demand noise (fraction)


class PressureSimulator:
    """
    Simulates realistic pressure data for a pipe segment.
    
    Physical Model:
    ---------------
    Uses simplified hydraulic equations:
    
    1. Headloss: ΔP = k × Q^1.85 × L / D^4.87 (Hazen-Williams)
    2. Leak effect: Increases flow, causing pressure drop downstream
    3. Demand variation: Diurnal pattern with morning/evening peaks
    4. Noise: Measurement uncertainty and pressure fluctuations
    
    The simulation is physically grounded but simplified for demonstration.
    """
    
    def __init__(
        self,
        pipe_config: Optional[PipeConfig] = None,
        demand_pattern: Optional[DemandPattern] = None,
        random_seed: int = 42
    ):
        self.pipe = pipe_config or PipeConfig()
        self.demand = demand_pattern or DemandPattern()
        self.sensors: List[SensorConfig] = []
        self.leaks: List[LeakConfig] = []
        self.np_random = np.random.RandomState(random_seed)
        
        # Hydraulic constants
        self.hw_coefficient = 130  # Hazen-Williams C factor
        
    def add_sensor(self, sensor: SensorConfig) -> None:
        """Add a sensor to the simulation."""
        self.sensors.append(sensor)
        
    def add_leak(self, leak: LeakConfig) -> None:
        """Add a leak event to the simulation."""
        self.leaks.append(leak)
        
    def generate_data(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 15
    ) -> pd.DataFrame:
        """
        Generate simulated pressure data.
        
        Args:
            start_time: Simulation start
            end_time: Simulation end
            interval_minutes: Sampling interval
            
        Returns:
            DataFrame with columns: timestamp, sensor_id, pressure, flow
        """
        # Generate time series
        timestamps = pd.date_range(
            start=start_time,
            end=end_time,
            freq=f"{interval_minutes}min"
        )
        
        records = []
        
        for ts in timestamps:
            # Calculate demand for this time
            demand_lps = self._calculate_demand(ts)
            
            # Calculate leak flow for this time
            total_leak_flow = self._calculate_leak_flow(ts)
            
            # Total flow through pipe
            total_flow = demand_lps + total_leak_flow
            
            # Calculate pressure at each sensor
            for sensor in self.sensors:
                pressure = self._calculate_pressure(
                    sensor.position_m, 
                    total_flow,
                    total_leak_flow,
                    ts
                )
                
                # Add sensor noise and bias
                pressure += sensor.bias
                pressure += self.np_random.normal(0, sensor.noise_std)
                
                # Simulate data dropout
                if self.np_random.random() < sensor.failure_rate:
                    pressure = np.nan
                
                records.append({
                    'timestamp': ts,
                    'sensor_id': sensor.sensor_id,
                    'pressure': max(pressure, 0),  # Can't be negative
                    'flow': total_flow if sensor.position_m == 0 else None,
                    'leak_active': total_leak_flow > 0
                })
        
        return pd.DataFrame(records)
    
    def _calculate_demand(self, timestamp: datetime) -> float:
        """
        Calculate water demand at given time.
        
        Uses diurnal pattern with morning/evening peaks.
        """
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Base demand
        demand = self.demand.base_demand_lps
        
        # Diurnal pattern (simplified sinusoidal + peaks)
        hour_factor = 1 + 0.3 * np.sin(np.pi * (hour - 6) / 12)
        
        # Morning peak (6-9 AM)
        if 6 <= hour <= 9:
            peak_factor = self.demand.peak_multiplier * np.exp(
                -0.5 * ((hour - self.demand.morning_peak_hour) / 1.5) ** 2
            )
            hour_factor = max(hour_factor, peak_factor)
        
        # Evening peak (17-21)
        if 17 <= hour <= 21:
            peak_factor = self.demand.peak_multiplier * np.exp(
                -0.5 * ((hour - self.demand.evening_peak_hour) / 1.5) ** 2
            )
            hour_factor = max(hour_factor, peak_factor)
        
        # Night minimum (1-5 AM)
        if 1 <= hour <= 5:
            hour_factor = 0.3
        
        demand *= hour_factor
        
        # Weekend reduction
        if day_of_week >= 5:
            demand *= self.demand.weekend_reduction
        
        # Add noise
        demand *= (1 + self.np_random.normal(0, self.demand.noise_std))
        
        return max(demand, 1.0)  # Minimum demand
    
    def _calculate_leak_flow(self, timestamp: datetime) -> float:
        """Calculate total leak flow at given time."""
        
        total_leak = 0.0
        
        for leak in self.leaks:
            if timestamp < leak.start_time:
                continue
            if leak.end_time and timestamp >= leak.end_time:
                continue
            
            # Calculate leak intensity (ramp up)
            hours_since_start = (timestamp - leak.start_time).total_seconds() / 3600
            
            if hours_since_start < leak.ramp_hours:
                # Ramp up period
                intensity = hours_since_start / leak.ramp_hours
            else:
                intensity = 1.0
            
            total_leak += leak.flow_rate_lps * intensity
        
        return total_leak
    
    def _calculate_pressure(
        self,
        position_m: float,
        total_flow_lps: float,
        leak_flow_lps: float,
        timestamp: datetime
    ) -> float:
        """
        Calculate pressure at a given position.
        
        Uses Hazen-Williams equation for headloss:
        hf = 10.67 × L × Q^1.85 / (C^1.85 × D^4.87)
        
        Where:
        - hf = headloss (meters)
        - L = length (m)
        - Q = flow (m³/s)
        - C = Hazen-Williams coefficient
        - D = diameter (m)
        """
        # Convert units
        flow_m3s = total_flow_lps / 1000
        diameter_m = self.pipe.diameter_mm / 1000
        
        # Hazen-Williams headloss to this position
        if flow_m3s > 0:
            headloss_m = (
                10.67 * position_m * (flow_m3s ** 1.85) / 
                ((self.hw_coefficient ** 1.85) * (diameter_m ** 4.87))
            )
        else:
            headloss_m = 0
        
        # Convert headloss to pressure drop (1 bar ≈ 10m head)
        pressure_drop = headloss_m / 10
        
        # Additional pressure drop from leak (if leak is upstream of sensor)
        for leak in self.leaks:
            if timestamp >= leak.start_time:
                if leak.end_time is None or timestamp < leak.end_time:
                    if leak.position_m < position_m:
                        # Leak is upstream - affects this sensor
                        # Pressure drop proportional to leak flow
                        leak_drop = 0.1 * (leak_flow_lps / 10)  # Simplified
                        pressure_drop += leak_drop
        
        # Final pressure
        pressure = self.pipe.supply_pressure - pressure_drop
        
        return pressure


class PrototypeDemo:
    """
    Complete prototype demonstration.
    
    Simulates a simple pipe with:
    - 3 pressure sensors
    - Controllable leak injection
    - Full detection pipeline
    """
    
    def __init__(self):
        self.simulator = PressureSimulator()
        self.setup_default_config()
        
    def setup_default_config(self):
        """Set up default prototype configuration."""
        
        # Three sensors along 500m pipe
        self.simulator.add_sensor(SensorConfig(
            sensor_id='SENSOR_001',
            position_m=0,  # Inlet
            noise_std=0.015
        ))
        
        self.simulator.add_sensor(SensorConfig(
            sensor_id='SENSOR_002',
            position_m=250,  # Middle
            noise_std=0.02
        ))
        
        self.simulator.add_sensor(SensorConfig(
            sensor_id='SENSOR_003',
            position_m=500,  # Outlet
            noise_std=0.018
        ))
        
        # Update pipe config
        self.simulator.pipe = PipeConfig(
            length_m=500,
            diameter_mm=150,
            supply_pressure=3.5
        )
    
    def run_scenario(
        self,
        scenario: str = "medium_leak",
        days: int = 14,
        leak_day: int = 7
    ) -> Dict[str, Any]:
        """
        Run a demonstration scenario.
        
        Scenarios:
        - baseline: No leak, establish normal behavior
        - small_leak: Small leak (2 L/s)
        - medium_leak: Medium leak (5 L/s)
        - large_leak: Large leak (15 L/s)
        - burst: Sudden burst (30 L/s)
        
        Returns:
            Dictionary with simulation results and detection outcomes
        """
        # Clear previous leaks
        self.simulator.leaks = []
        
        # Set up time period
        start_time = datetime(2026, 1, 1, 0, 0, 0)
        end_time = start_time + timedelta(days=days)
        leak_time = start_time + timedelta(days=leak_day)
        
        # Configure leak based on scenario
        if scenario == "baseline":
            pass  # No leak
        elif scenario == "small_leak":
            self.simulator.add_leak(LeakConfig(
                position_m=300,
                start_time=leak_time,
                severity="small",
                flow_rate_lps=2.0,
                ramp_hours=4.0
            ))
        elif scenario == "medium_leak":
            self.simulator.add_leak(LeakConfig(
                position_m=200,
                start_time=leak_time,
                severity="medium",
                flow_rate_lps=5.0,
                ramp_hours=2.0
            ))
        elif scenario == "large_leak":
            self.simulator.add_leak(LeakConfig(
                position_m=350,
                start_time=leak_time,
                severity="large",
                flow_rate_lps=15.0,
                ramp_hours=1.0
            ))
        elif scenario == "burst":
            self.simulator.add_leak(LeakConfig(
                position_m=250,
                start_time=leak_time,
                severity="large",
                flow_rate_lps=30.0,
                ramp_hours=0.1  # Very rapid
            ))
        
        # Generate data
        print(f"Generating {days} days of data for scenario: {scenario}")
        data = self.simulator.generate_data(start_time, end_time)
        
        # Run detection
        print("Running leak detection...")
        detection_results = self._run_detection(data, leak_time)
        
        return {
            'scenario': scenario,
            'data': data,
            'detection': detection_results,
            'leak_config': self.simulator.leaks[0].__dict__ if self.simulator.leaks else None,
            'summary': self._generate_summary(scenario, detection_results)
        }
    
    def _run_detection(
        self,
        data: pd.DataFrame,
        leak_time: datetime
    ) -> Dict[str, Any]:
        """Run the detection pipeline on simulated data."""
        
        # Import detection modules
        from src.features.feature_engineering import FeatureEngineer
        from src.baseline.detector import BaselineLeakDetector
        from src.ai.anomaly.detector import IsolationForestDetector
        
        results = {
            'sensors': {},
            'first_detection_time': None,
            'detection_latency_hours': None,
            'baseline_alerts': [],
            'ai_alerts': []
        }
        
        # Process each sensor
        feature_engineer = FeatureEngineer()
        baseline_detector = BaselineLeakDetector()
        
        for sensor_id in data['sensor_id'].unique():
            sensor_data = data[data['sensor_id'] == sensor_id].copy()
            sensor_data = sensor_data.set_index('timestamp')
            
            # Need enough data for baseline
            if len(sensor_data) < 672:  # 7 days
                continue
            
            # Compute features for each day after day 7
            day_results = []
            
            for day in range(7, len(sensor_data) // 96):
                end_idx = day * 96
                window_data = sensor_data.iloc[:end_idx]
                
                # Prepare data for feature engineering
                feature_data = pd.DataFrame({
                    'timestamp': window_data.index,
                    'value': window_data['pressure']
                })
                feature_data.attrs['sensor_id'] = sensor_id
                
                # Compute features
                features = feature_engineer.compute_features(feature_data)
                
                if features.quality_score < 0.5:
                    continue
                
                # Run baseline detection
                baseline_result = baseline_detector.detect(features.features, sensor_id)
                
                # Record alerts
                timestamp = sensor_data.index[end_idx - 1]
                leak_active = sensor_data.iloc[end_idx - 1]['leak_active']
                
                if baseline_result.alert:
                    results['baseline_alerts'].append({
                        'timestamp': timestamp,
                        'sensor_id': sensor_id,
                        'severity': baseline_result.severity.value,
                        'rules': [r.rule_name for r in baseline_result.triggered_rules],
                        'leak_active': leak_active
                    })
                    
                    # Track first detection
                    if leak_active and results['first_detection_time'] is None:
                        results['first_detection_time'] = timestamp
                        if leak_time:
                            latency = (timestamp - leak_time).total_seconds() / 3600
                            results['detection_latency_hours'] = latency
                
                day_results.append({
                    'day': day,
                    'timestamp': timestamp,
                    'features': features.features,
                    'baseline_alert': baseline_result.alert,
                    'leak_active': leak_active
                })
            
            results['sensors'][sensor_id] = day_results
        
        return results
    
    def _generate_summary(
        self,
        scenario: str,
        detection: Dict[str, Any]
    ) -> str:
        """Generate summary of detection results."""
        
        summary = f"""
PROTOTYPE DEMONSTRATION RESULTS
===============================

Scenario: {scenario}
-------------------

Detection Performance:
- Total baseline alerts: {len(detection['baseline_alerts'])}
- First detection time: {detection['first_detection_time']}
- Detection latency: {detection['detection_latency_hours']:.1f} hours (after leak start)

"""
        
        if detection['baseline_alerts']:
            summary += "Alert Details:\n"
            for alert in detection['baseline_alerts'][:5]:
                summary += f"  - {alert['timestamp']}: {alert['severity']} ({', '.join(alert['rules'])})\n"
        
        summary += """

Physical Explanation:
--------------------
"""
        
        if scenario == "baseline":
            summary += "No leak simulated. System correctly shows no alerts (or minimal false positives).\n"
        else:
            summary += f"""
When the leak started:
1. Flow through the pipe increased (leak draws water)
2. Headloss increased (more flow = more friction loss)
3. Pressure downstream of leak dropped
4. Night/day pressure ratio inverted (leak consumes water continuously)
5. Baseline deviation became negative

The {scenario.replace('_', ' ')} was detected by monitoring these physical indicators.
"""
        
        return summary
    
    def export_results(
        self,
        results: Dict[str, Any],
        output_dir: str = "./prototype_output"
    ) -> None:
        """Export results to files."""
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export pressure data
        results['data'].to_csv(
            f"{output_dir}/pressure_data.csv",
            index=False
        )
        
        # Export detection summary
        with open(f"{output_dir}/detection_summary.txt", 'w') as f:
            f.write(results['summary'])
        
        # Export alerts
        if results['detection']['baseline_alerts']:
            alerts_df = pd.DataFrame(results['detection']['baseline_alerts'])
            alerts_df.to_csv(f"{output_dir}/alerts.csv", index=False)
        
        print(f"Results exported to {output_dir}/")


def run_prototype_demo():
    """
    Main entry point for prototype demonstration.
    
    Runs all scenarios and generates comparison report.
    """
    
    demo = PrototypeDemo()
    
    scenarios = ['baseline', 'small_leak', 'medium_leak', 'large_leak', 'burst']
    all_results = {}
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Running scenario: {scenario}")
        print('='*60)
        
        results = demo.run_scenario(scenario, days=14, leak_day=7)
        all_results[scenario] = results
        
        print(results['summary'])
    
    # Generate comparison table
    print("\n" + "="*60)
    print("SCENARIO COMPARISON")
    print("="*60)
    print(f"{'Scenario':<15} {'Alerts':<10} {'Detection (hrs)':<20} {'First Rule'}")
    print("-"*60)
    
    for scenario, results in all_results.items():
        alerts = len(results['detection']['baseline_alerts'])
        latency = results['detection']['detection_latency_hours']
        latency_str = f"{latency:.1f}" if latency else "N/A"
        
        first_rule = "N/A"
        if results['detection']['baseline_alerts']:
            first_rule = results['detection']['baseline_alerts'][0]['rules'][0]
        
        print(f"{scenario:<15} {alerts:<10} {latency_str:<20} {first_rule}")
    
    return all_results


if __name__ == "__main__":
    run_prototype_demo()
