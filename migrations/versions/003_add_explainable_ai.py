"""Add explainable AI insights to leak_events

Revision ID: 003
Revises: 002_add_notification_system
Create Date: 2026-01-23

This migration adds:
1. ai_reason JSONB column to leak_events table for XAI insights

Step 8: Explainable AI - When AI creates leak events, store structured
explanations including:
- pressure_drop: Evidence for pressure-based detection
- flow_rise: Evidence for flow-based detection  
- multi_sensor_agreement: Corroboration from multiple sensors
- night_flow_deviation: Minimum night flow analysis
- confidence: Breakdown by statistical, ML, temporal, spatial methods
- top_signals: Ranked list of contributing factors
- evidence_timeline: Time-series of detection events
- explanation: Human-readable summary
- recommendations: Actionable next steps
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = '003_add_explainable_ai'
down_revision: Union[str, None] = '002_add_notification_system'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add explainable AI insights to leak_events.
    
    The ai_reason column stores a JSONB object with the following structure:
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
            "raw_data": {"values": [...], "baseline": 3.0}
        },
        "flow_rise": {
            "signal_type": "flow_rise",
            "contribution": 0.72,
            "value": 135,
            "threshold": 115,
            "deviation": 35,
            "description": "Flow increased by 35% above baseline...",
            "timestamp": "2026-01-23T10:30:00Z",
            "sensor_id": "FS-001"
        },
        "multi_sensor_agreement": {
            "signal_type": "multi_sensor_agreement",
            "contribution": 0.90,
            "value": 4,
            "threshold": 2,
            "deviation": 2,
            "description": "4 sensors showing correlated anomalies...",
            "timestamp": "2026-01-23T10:30:00Z",
            "raw_data": {"sensors": ["PS-001", "PS-002", "FS-001", "FS-002"]}
        },
        "night_flow_deviation": {
            "signal_type": "night_flow_deviation",
            "contribution": 0.65,
            "value": 18.5,
            "threshold": 12.0,
            "deviation": 6.5,
            "description": "Minimum night flow elevated at 18.5 L/min..."
        },
        "acoustic_anomaly": {
            "signal_type": "acoustic_anomaly",
            "contribution": 0.78,
            "value": 85,
            "threshold": 60,
            "description": "Acoustic signature detected at 85 dB..."
        },
        "confidence": {
            "statistical_confidence": 0.82,
            "ml_confidence": 0.78,
            "temporal_confidence": 0.65,
            "spatial_confidence": 0.90,
            "acoustic_confidence": 0.78,
            "overall_confidence": 0.85,
            "weights": {
                "statistical": 0.20,
                "ml": 0.25,
                "temporal": 0.20,
                "spatial": 0.25,
                "acoustic": 0.10
            }
        },
        "top_signals": ["multi_sensor_agreement", "pressure_drop", "acoustic_anomaly", "flow_rise"],
        "evidence_timeline": [
            {
                "timestamp": "2026-01-23T10:15:00Z",
                "signal_type": "pressure_drop",
                "value": 2.5,
                "anomaly_score": 0.6,
                "description": "Pressure beginning to decrease",
                "is_key_event": false
            },
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
        "explanation": "High confidence leak detection (85%). Primary indicator: Sustained pressure drop of 0.4 bar...",
        "recommendations": [
            "URGENT: Dispatch field team immediately for visual inspection.",
            "Use sensor triangulation data to narrow search area."
        ],
        "model_version": "3.0.0",
        "feature_importance": {
            "multi_sensor_agreement": 0.90,
            "pressure_drop": 0.85,
            "acoustic_anomaly": 0.78,
            "flow_rise": 0.72
        }
    }
    """
    
    # Add ai_reason column to leak_events table
    op.add_column(
        'leak_events',
        sa.Column(
            'ai_reason',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Explainable AI insights: signals, confidence breakdown, evidence timeline'
        )
    )
    
    # Add GIN index for efficient JSONB queries (e.g., filtering by detection method)
    op.create_index(
        'ix_leak_events_ai_reason_gin',
        'leak_events',
        ['ai_reason'],
        postgresql_using='gin',
        postgresql_ops={'ai_reason': 'jsonb_path_ops'}
    )
    
    # Add index on top_signals for analytics queries
    op.execute("""
        CREATE INDEX ix_leak_events_ai_reason_top_signals 
        ON leak_events 
        USING GIN ((ai_reason->'top_signals'))
    """)
    
    # Add index on confidence for filtering high-confidence detections
    op.execute("""
        CREATE INDEX ix_leak_events_confidence 
        ON leak_events 
        USING BTREE (((ai_reason->'confidence'->>'overall_confidence')::float))
        WHERE ai_reason IS NOT NULL
    """)
    
    print("✅ Added ai_reason JSONB column to leak_events table")
    print("✅ Created GIN index for efficient JSONB queries")
    print("✅ Created index on top_signals for analytics")
    print("✅ Created index on confidence for filtering")


def downgrade() -> None:
    """Remove explainable AI columns and indexes."""
    
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS ix_leak_events_confidence")
    op.execute("DROP INDEX IF EXISTS ix_leak_events_ai_reason_top_signals")
    op.drop_index('ix_leak_events_ai_reason_gin', table_name='leak_events')
    
    # Drop column
    op.drop_column('leak_events', 'ai_reason')
    
    print("✅ Removed ai_reason column and associated indexes")
