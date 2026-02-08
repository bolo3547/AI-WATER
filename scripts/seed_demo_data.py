#!/usr/bin/env python3
"""
AquaWatch NRW - Demo Data Seeding Script
========================================

Creates realistic demo data for testing and first-time deployment.

Usage:
    python scripts/seed_demo_data.py

Creates:
    - 2 DMAs (District Metered Areas) with realistic Zambian locations
    - 6 sensors per DMA (pressure, flow, acoustic)
    - 24 hours of sensor readings at 15-minute intervals
    - 3 sample alerts (leak detected, pressure anomaly, sensor offline)
    - 2 work orders linked to alerts
    - 1 community report
"""

import json
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def generate_sensor_readings(
    sensor_id: str,
    sensor_type: str,
    start_time: datetime,
    hours: int = 24,
    interval_minutes: int = 15,
) -> list:
    """Generate realistic sensor readings for a given period."""
    readings = []
    current = start_time

    # Base values by sensor type
    base_values = {
        "pressure": {"mean": 3.5, "std": 0.3, "unit": "bar"},
        "flow": {"mean": 45.0, "std": 5.0, "unit": "m3/h"},
        "acoustic": {"mean": 25.0, "std": 8.0, "unit": "dB"},
    }

    config = base_values.get(sensor_type, base_values["pressure"])
    steps = (hours * 60) // interval_minutes

    for i in range(steps):
        # Add time-of-day pattern (higher during day, lower at night)
        hour = current.hour
        if 6 <= hour <= 22:
            day_factor = 1.0 + 0.2 * (1 - abs(hour - 14) / 8)
        else:
            day_factor = 0.7  # night reduction

        value = config["mean"] * day_factor + random.gauss(0, config["std"] * 0.3)
        value = max(0, round(value, 3))

        readings.append({
            "sensor_id": sensor_id,
            "timestamp": current.isoformat(),
            "value": value,
            "unit": config["unit"],
            "quality_score": random.randint(85, 100),
        })
        current += timedelta(minutes=interval_minutes)

    return readings


def generate_demo_data() -> dict:
    """Generate complete demo dataset."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=24)

    # =========================================================================
    # DMAs (District Metered Areas) - Real Zambian locations
    # =========================================================================
    dmas = [
        {
            "dma_id": "DMA-LUSAKA-001",
            "name": "Kabulonga Zone A",
            "description": "Residential area in Kabulonga, Lusaka",
            "latitude": -15.4050,
            "longitude": 28.3228,
            "area_km2": 4.2,
            "connections": 1850,
            "pipe_length_km": 23.5,
            "status": "active",
        },
        {
            "dma_id": "DMA-LUSAKA-002",
            "name": "Chilenje Industrial",
            "description": "Mixed residential and industrial zone in Chilenje",
            "latitude": -15.4383,
            "longitude": 28.2919,
            "area_km2": 3.8,
            "connections": 1200,
            "pipe_length_km": 18.7,
            "status": "active",
        },
    ]

    # =========================================================================
    # Sensors
    # =========================================================================
    sensors = []
    sensor_types = ["pressure", "pressure", "flow", "flow", "acoustic", "acoustic"]

    for dma in dmas:
        for i, stype in enumerate(sensor_types):
            sensor_id = f"SENSOR-{dma['dma_id'][-3:]}-{i+1:02d}"
            sensors.append({
                "sensor_id": sensor_id,
                "dma_id": dma["dma_id"],
                "type": stype,
                "latitude": dma["latitude"] + random.uniform(-0.005, 0.005),
                "longitude": dma["longitude"] + random.uniform(-0.005, 0.005),
                "status": "online",
                "battery_percent": random.randint(65, 100),
                "firmware_version": "2.1.0",
                "last_reading": now.isoformat(),
            })

    # =========================================================================
    # Sensor Readings (24 hours)
    # =========================================================================
    all_readings = []
    for sensor in sensors:
        readings = generate_sensor_readings(
            sensor["sensor_id"],
            sensor["type"],
            start_time,
            hours=24,
        )
        all_readings.extend(readings)

    # =========================================================================
    # Alerts
    # =========================================================================
    alerts = [
        {
            "alert_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
            "dma_id": "DMA-LUSAKA-001",
            "sensor_id": "SENSOR-001-01",
            "type": "leak_suspected",
            "severity": "high",
            "title": "Suspected Leak in Kabulonga Zone A",
            "description": "Pressure drop of 1.2 bar detected with correlated flow spike. AI confidence: 87%.",
            "ai_confidence": 0.87,
            "estimated_loss_m3_day": 45.0,
            "latitude": -15.4050,
            "longitude": 28.3228,
            "status": "active",
            "created_at": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "alert_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
            "dma_id": "DMA-LUSAKA-002",
            "sensor_id": "SENSOR-002-03",
            "type": "pressure_anomaly",
            "severity": "medium",
            "title": "Pressure Anomaly in Chilenje",
            "description": "Sustained low pressure detected during peak hours. Possible distribution issue.",
            "ai_confidence": 0.72,
            "estimated_loss_m3_day": 12.0,
            "latitude": -15.4383,
            "longitude": 28.2919,
            "status": "active",
            "created_at": (now - timedelta(hours=6)).isoformat(),
        },
        {
            "alert_id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
            "dma_id": "DMA-LUSAKA-001",
            "sensor_id": "SENSOR-001-06",
            "type": "sensor_offline",
            "severity": "low",
            "title": "Acoustic Sensor Offline",
            "description": "Sensor SENSOR-001-06 has not reported for 2 hours. Battery: 12%.",
            "ai_confidence": None,
            "estimated_loss_m3_day": None,
            "latitude": -15.4070,
            "longitude": 28.3250,
            "status": "active",
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
    ]

    # =========================================================================
    # Work Orders
    # =========================================================================
    work_orders = [
        {
            "work_order_id": f"WO-{now.strftime('%Y%m%d')}-001",
            "alert_id": alerts[0]["alert_id"],
            "dma_id": "DMA-LUSAKA-001",
            "type": "leak_repair",
            "priority": "high",
            "title": "Investigate and repair suspected leak - Kabulonga",
            "description": "AI detected pressure drop with 87% confidence. Dispatch field team to investigate.",
            "status": "assigned",
            "assigned_to": "John Mwale",
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "work_order_id": f"WO-{now.strftime('%Y%m%d')}-002",
            "alert_id": alerts[2]["alert_id"],
            "dma_id": "DMA-LUSAKA-001",
            "type": "sensor_maintenance",
            "priority": "medium",
            "title": "Replace battery on acoustic sensor",
            "description": "Sensor SENSOR-001-06 battery critically low. Replace and recalibrate.",
            "status": "created",
            "assigned_to": None,
            "created_at": (now - timedelta(hours=1)).isoformat(),
        },
    ]

    # =========================================================================
    # Community Report
    # =========================================================================
    community_reports = [
        {
            "report_id": f"CR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "user_name": "Grace Tembo",
            "phone": "+260971234567",
            "type": "leak",
            "description": "Water flowing on the road near Kabulonga Shopping Centre for 2 days",
            "latitude": -15.4065,
            "longitude": 28.3240,
            "urgency": "high",
            "status": "submitted",
            "created_at": (now - timedelta(hours=8)).isoformat(),
        },
    ]

    # =========================================================================
    # NRW Summary
    # =========================================================================
    nrw_summary = {
        "period": "last_24h",
        "system_input_volume_m3": 12500,
        "billed_authorized_m3": 8750,
        "unbilled_authorized_m3": 625,
        "apparent_losses_m3": 875,
        "real_losses_m3": 2250,
        "nrw_percent": 30.0,
        "nrw_cost_usd": 3375.0,
        "infrastructure_leakage_index": 4.2,
        "target_nrw_percent": 25.0,
    }

    return {
        "generated_at": now.isoformat(),
        "description": "AquaWatch NRW Demo Data - Lusaka, Zambia",
        "dmas": dmas,
        "sensors": sensors,
        "readings_count": len(all_readings),
        "readings_sample": all_readings[:10],  # First 10 as sample
        "alerts": alerts,
        "work_orders": work_orders,
        "community_reports": community_reports,
        "nrw_summary": nrw_summary,
    }


def main():
    """Generate and save demo data."""
    logger.info("Generating AquaWatch NRW demo data...")

    data = generate_demo_data()

    output_path = "demo_data.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Demo data saved to {output_path}")
    logger.info(f"  DMAs: {len(data['dmas'])}")
    logger.info(f"  Sensors: {len(data['sensors'])}")
    logger.info(f"  Readings: {data['readings_count']}")
    logger.info(f"  Alerts: {len(data['alerts'])}")
    logger.info(f"  Work Orders: {len(data['work_orders'])}")
    logger.info(f"  Community Reports: {len(data['community_reports'])}")
    logger.info(f"  NRW Rate: {data['nrw_summary']['nrw_percent']}%")


if __name__ == "__main__":
    main()
