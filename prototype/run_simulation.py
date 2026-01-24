"""Run the prototype pressure simulation and save results."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from prototype.simulator import PressureSimulator, PipeConfig, DemandPattern, SensorConfig, LeakConfig


def main() -> int:
    simulator = PressureSimulator(
        pipe_config=PipeConfig(length_m=1200, diameter_mm=200, supply_pressure=4.2),
        demand_pattern=DemandPattern(base_demand_lps=18.0, peak_multiplier=2.2),
        random_seed=42,
    )

    # Sensors
    simulator.add_sensor(SensorConfig(sensor_id="S-001", position_m=0, noise_std=0.02))
    simulator.add_sensor(SensorConfig(sensor_id="S-002", position_m=400, noise_std=0.03))
    simulator.add_sensor(SensorConfig(sensor_id="S-003", position_m=800, noise_std=0.03))
    simulator.add_sensor(SensorConfig(sensor_id="S-004", position_m=1200, noise_std=0.02))

    # Leak event
    start = datetime.now(timezone.utc) - timedelta(days=1)
    leak_start = start + timedelta(hours=6)
    simulator.add_leak(
        LeakConfig(position_m=650, start_time=leak_start, severity="medium", flow_rate_lps=6.5)
    )

    # Generate 24h data
    end = datetime.now(timezone.utc)
    data = simulator.generate_data(start_time=start, end_time=end, interval_minutes=5)

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    data.to_csv(out_path, index=False)

    # Quick summary
    print(f"Generated {len(data)} rows")
    print(f"Saved to {out_path}")
    print(data.head())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
