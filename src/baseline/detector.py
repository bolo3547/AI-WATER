"""
AquaWatch NRW - Physics-Based Baseline System
=============================================

Rule-based leak detection using pressure thresholds and domain knowledge.
Serves as benchmark for AI system performance.

Purpose:
1. Provide baseline performance metrics
2. Demonstrate AI value-add
3. Serve as fallback when AI fails
4. Build operator trust through familiar logic

This represents what an experienced operator would detect manually.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class RuleSeverity(str, Enum):
    """Severity levels for rule-based detection."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    """Result from a single rule evaluation."""
    rule_name: str
    triggered: bool
    severity: RuleSeverity
    value: float
    threshold: float
    description: str


@dataclass
class BaselineDetectionResult:
    """Result from baseline detection system."""
    sensor_id: str
    timestamp: datetime
    alert: bool
    severity: RuleSeverity
    triggered_rules: List[RuleResult]
    summary: str
    recommended_action: str
    confidence: float  # For comparison with AI


@dataclass
class ThresholdConfig:
    """Configuration for threshold-based detection."""
    
    # Absolute pressure thresholds
    pressure_min_critical: float = 1.0      # bar - below this is critical
    pressure_min_warning: float = 1.5       # bar - below this is warning
    
    # Pressure drop thresholds
    drop_1h_warning: float = 0.3            # bar/hour - sudden drop warning
    drop_1h_critical: float = 0.5           # bar/hour - sudden drop critical
    drop_24h_warning: float = 0.5           # bar over 24h - gradual decline
    
    # Baseline deviation thresholds
    deviation_warning: float = 0.3          # bar below 7-day average
    deviation_critical: float = 0.5         # bar below 7-day average
    
    # Night/day ratio thresholds (key leak indicator)
    night_day_ratio_warning: float = 0.98   # Slight inversion
    night_day_ratio_critical: float = 0.95  # Significant inversion
    
    # MNF deviation thresholds
    mnf_deviation_warning: float = -0.2     # bar below normal
    mnf_deviation_critical: float = -0.4    # bar below normal
    
    # Gradient thresholds
    gradient_change_warning: float = 0.05   # bar/km change
    gradient_change_critical: float = 0.1   # bar/km change
    
    # Variance thresholds
    variance_ratio_warning: float = 2.0     # Current/baseline variance ratio
    variance_ratio_critical: float = 3.0
    
    # Consecutive anomalies threshold
    consecutive_anomalies_warning: int = 3  # Number of consecutive anomalies


class BaselineLeakDetector:
    """
    Physics-based leak detection using threshold rules.
    
    This system uses domain knowledge about water network behavior:
    
    1. PRESSURE THRESHOLDS:
       - Minimum acceptable pressure for service
       - Maximum expected daily variation
    
    2. TEMPORAL PATTERNS:
       - Night pressure should be HIGHER than day (less demand)
       - Sudden drops indicate bursts
       - Gradual declines indicate developing leaks
    
    3. SPATIAL PATTERNS:
       - Gradient changes between sensors indicate leaks between them
       - Multiple sensors affected = larger leak
    
    These rules represent operator expertise encoded in code.
    """
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig()
        self.consecutive_anomalies: Dict[str, int] = {}
        
    def detect(
        self,
        features: Dict[str, float],
        sensor_id: str = 'unknown'
    ) -> BaselineDetectionResult:
        """
        Apply all rules to detect potential leaks.
        
        Args:
            features: Feature dictionary from feature engineering
            sensor_id: Sensor identifier
            
        Returns:
            BaselineDetectionResult with all triggered rules
        """
        triggered_rules: List[RuleResult] = []
        
        # Rule 1: Absolute pressure minimum
        rule = self._check_min_pressure(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 2: Sudden pressure drop (1 hour)
        rule = self._check_sudden_drop(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 3: Gradual pressure decline (24 hours)
        rule = self._check_gradual_decline(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 4: Baseline deviation
        rule = self._check_baseline_deviation(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 5: Night/day ratio (critical indicator)
        rule = self._check_night_day_ratio(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 6: MNF deviation
        rule = self._check_mnf_deviation(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 7: Gradient change
        rule = self._check_gradient_change(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Rule 8: Variance increase
        rule = self._check_variance(features)
        if rule.triggered:
            triggered_rules.append(rule)
        
        # Determine overall severity
        overall_severity = self._determine_severity(triggered_rules)
        
        # Track consecutive anomalies
        if triggered_rules:
            self.consecutive_anomalies[sensor_id] = \
                self.consecutive_anomalies.get(sensor_id, 0) + 1
        else:
            self.consecutive_anomalies[sensor_id] = 0
        
        # Check consecutive anomaly rule
        if self.consecutive_anomalies[sensor_id] >= self.config.consecutive_anomalies_warning:
            triggered_rules.append(RuleResult(
                rule_name='consecutive_anomalies',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=float(self.consecutive_anomalies[sensor_id]),
                threshold=float(self.config.consecutive_anomalies_warning),
                description=f"Anomalies detected for {self.consecutive_anomalies[sensor_id]} consecutive periods"
            ))
            if overall_severity == RuleSeverity.NONE:
                overall_severity = RuleSeverity.MEDIUM
        
        # Generate summary and recommendation
        alert = len(triggered_rules) > 0
        summary = self._generate_summary(triggered_rules, overall_severity)
        action = self._generate_recommendation(triggered_rules, overall_severity)
        
        # Calculate confidence (for AI comparison)
        confidence = self._calculate_confidence(triggered_rules)
        
        return BaselineDetectionResult(
            sensor_id=sensor_id,
            timestamp=datetime.utcnow(),
            alert=alert,
            severity=overall_severity,
            triggered_rules=triggered_rules,
            summary=summary,
            recommended_action=action,
            confidence=confidence
        )
    
    def _check_min_pressure(self, features: Dict[str, float]) -> RuleResult:
        """Rule 1: Check if pressure is below minimum threshold."""
        
        pressure = features.get('pressure_min', features.get('pressure_mean', 999))
        
        if pressure < self.config.pressure_min_critical:
            return RuleResult(
                rule_name='min_pressure',
                triggered=True,
                severity=RuleSeverity.CRITICAL,
                value=pressure,
                threshold=self.config.pressure_min_critical,
                description=f"Pressure critically low at {pressure:.2f} bar (min: {self.config.pressure_min_critical} bar)"
            )
        elif pressure < self.config.pressure_min_warning:
            return RuleResult(
                rule_name='min_pressure',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=pressure,
                threshold=self.config.pressure_min_warning,
                description=f"Pressure below warning level at {pressure:.2f} bar"
            )
        
        return RuleResult(
            rule_name='min_pressure',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=pressure,
            threshold=self.config.pressure_min_warning,
            description="Pressure within acceptable range"
        )
    
    def _check_sudden_drop(self, features: Dict[str, float]) -> RuleResult:
        """Rule 2: Check for sudden pressure drop (burst detection)."""
        
        drop_rate = features.get('pressure_1h_change_rate', 0)
        
        # Negative drop rate means pressure is falling
        if drop_rate < -self.config.drop_1h_critical:
            return RuleResult(
                rule_name='sudden_drop',
                triggered=True,
                severity=RuleSeverity.CRITICAL,
                value=abs(drop_rate),
                threshold=self.config.drop_1h_critical,
                description=f"Rapid pressure drop: {abs(drop_rate):.2f} bar/hour (possible burst)"
            )
        elif drop_rate < -self.config.drop_1h_warning:
            return RuleResult(
                rule_name='sudden_drop',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=abs(drop_rate),
                threshold=self.config.drop_1h_warning,
                description=f"Significant pressure drop: {abs(drop_rate):.2f} bar/hour"
            )
        
        return RuleResult(
            rule_name='sudden_drop',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=abs(drop_rate),
            threshold=self.config.drop_1h_warning,
            description="No sudden pressure changes"
        )
    
    def _check_gradual_decline(self, features: Dict[str, float]) -> RuleResult:
        """Rule 3: Check for gradual pressure decline over 24 hours."""
        
        change_24h = features.get('pressure_24h_change', 0)
        
        if change_24h < -self.config.drop_24h_warning:
            return RuleResult(
                rule_name='gradual_decline',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=abs(change_24h),
                threshold=self.config.drop_24h_warning,
                description=f"Gradual pressure decline: {abs(change_24h):.2f} bar over 24 hours"
            )
        
        return RuleResult(
            rule_name='gradual_decline',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=abs(change_24h),
            threshold=self.config.drop_24h_warning,
            description="No significant 24-hour pressure trend"
        )
    
    def _check_baseline_deviation(self, features: Dict[str, float]) -> RuleResult:
        """Rule 4: Check deviation from 7-day baseline."""
        
        deviation = features.get('deviation_from_baseline', 0)
        
        if deviation < -self.config.deviation_critical:
            return RuleResult(
                rule_name='baseline_deviation',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=abs(deviation),
                threshold=self.config.deviation_critical,
                description=f"Pressure {abs(deviation):.2f} bar below 7-day average"
            )
        elif deviation < -self.config.deviation_warning:
            return RuleResult(
                rule_name='baseline_deviation',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=abs(deviation),
                threshold=self.config.deviation_warning,
                description=f"Pressure {abs(deviation):.2f} bar below 7-day average"
            )
        
        return RuleResult(
            rule_name='baseline_deviation',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=abs(deviation),
            threshold=self.config.deviation_warning,
            description="Pressure consistent with baseline"
        )
    
    def _check_night_day_ratio(self, features: Dict[str, float]) -> RuleResult:
        """
        Rule 5: Check night/day pressure ratio.
        
        CRITICAL LEAK INDICATOR
        
        Physics:
        - At night, demand is low (people sleeping)
        - Therefore, headloss is low
        - Therefore, pressure should be HIGHER at night
        
        If night pressure is LOWER than day:
        - Something is consuming water at night
        - High probability of leak (or large night consumer)
        """
        
        ratio = features.get('night_day_ratio', 1.0)
        
        if ratio < self.config.night_day_ratio_critical:
            return RuleResult(
                rule_name='night_day_ratio',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=ratio,
                threshold=self.config.night_day_ratio_critical,
                description=f"Night pressure lower than day (ratio: {ratio:.3f}) - strong leak indicator"
            )
        elif ratio < self.config.night_day_ratio_warning:
            return RuleResult(
                rule_name='night_day_ratio',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=ratio,
                threshold=self.config.night_day_ratio_warning,
                description=f"Night/day pressure ratio concerning ({ratio:.3f})"
            )
        
        return RuleResult(
            rule_name='night_day_ratio',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=ratio,
            threshold=self.config.night_day_ratio_warning,
            description=f"Night/day ratio healthy ({ratio:.3f})"
        )
    
    def _check_mnf_deviation(self, features: Dict[str, float]) -> RuleResult:
        """Rule 6: Check Minimum Night Flow pressure deviation."""
        
        mnf_dev = features.get('mnf_deviation', 0)
        
        if mnf_dev < self.config.mnf_deviation_critical:
            return RuleResult(
                rule_name='mnf_deviation',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=mnf_dev,
                threshold=self.config.mnf_deviation_critical,
                description=f"Night pressure {abs(mnf_dev):.2f} bar below normal"
            )
        elif mnf_dev < self.config.mnf_deviation_warning:
            return RuleResult(
                rule_name='mnf_deviation',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=mnf_dev,
                threshold=self.config.mnf_deviation_warning,
                description=f"Night pressure {abs(mnf_dev):.2f} bar below normal"
            )
        
        return RuleResult(
            rule_name='mnf_deviation',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=mnf_dev,
            threshold=self.config.mnf_deviation_warning,
            description="Night pressure within normal range"
        )
    
    def _check_gradient_change(self, features: Dict[str, float]) -> RuleResult:
        """Rule 7: Check for gradient changes between sensors."""
        
        # Look for any gradient features
        gradient_changes = []
        for key, value in features.items():
            if 'gradient' in key.lower() and 'to_' in key:
                gradient_changes.append(abs(value))
        
        max_gradient = max(gradient_changes) if gradient_changes else 0
        
        if max_gradient > self.config.gradient_change_critical:
            return RuleResult(
                rule_name='gradient_change',
                triggered=True,
                severity=RuleSeverity.HIGH,
                value=max_gradient,
                threshold=self.config.gradient_change_critical,
                description=f"High pressure gradient: {max_gradient:.3f} bar/km"
            )
        elif max_gradient > self.config.gradient_change_warning:
            return RuleResult(
                rule_name='gradient_change',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=max_gradient,
                threshold=self.config.gradient_change_warning,
                description=f"Elevated pressure gradient: {max_gradient:.3f} bar/km"
            )
        
        return RuleResult(
            rule_name='gradient_change',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=max_gradient,
            threshold=self.config.gradient_change_warning,
            description="Pressure gradients normal"
        )
    
    def _check_variance(self, features: Dict[str, float]) -> RuleResult:
        """Rule 8: Check for increased pressure variance."""
        
        current_std = features.get('pressure_std', 0)
        baseline_std = features.get('baseline_std', current_std)
        
        if baseline_std > 0:
            variance_ratio = current_std / baseline_std
        else:
            variance_ratio = 1.0
        
        if variance_ratio > self.config.variance_ratio_critical:
            return RuleResult(
                rule_name='variance_increase',
                triggered=True,
                severity=RuleSeverity.MEDIUM,
                value=variance_ratio,
                threshold=self.config.variance_ratio_critical,
                description=f"Pressure variance {variance_ratio:.1f}x higher than baseline"
            )
        elif variance_ratio > self.config.variance_ratio_warning:
            return RuleResult(
                rule_name='variance_increase',
                triggered=True,
                severity=RuleSeverity.LOW,
                value=variance_ratio,
                threshold=self.config.variance_ratio_warning,
                description=f"Pressure variance elevated ({variance_ratio:.1f}x baseline)"
            )
        
        return RuleResult(
            rule_name='variance_increase',
            triggered=False,
            severity=RuleSeverity.NONE,
            value=variance_ratio,
            threshold=self.config.variance_ratio_warning,
            description="Pressure variance normal"
        )
    
    def _determine_severity(self, triggered_rules: List[RuleResult]) -> RuleSeverity:
        """Determine overall severity from triggered rules."""
        
        if not triggered_rules:
            return RuleSeverity.NONE
        
        # Get highest severity
        severities = [r.severity for r in triggered_rules]
        
        if RuleSeverity.CRITICAL in severities:
            return RuleSeverity.CRITICAL
        elif RuleSeverity.HIGH in severities:
            return RuleSeverity.HIGH
        elif RuleSeverity.MEDIUM in severities:
            return RuleSeverity.MEDIUM
        elif RuleSeverity.LOW in severities:
            return RuleSeverity.LOW
        
        return RuleSeverity.NONE
    
    def _generate_summary(
        self,
        triggered_rules: List[RuleResult],
        severity: RuleSeverity
    ) -> str:
        """Generate human-readable summary."""
        
        if not triggered_rules:
            return "All pressure indicators within normal range. No action required."
        
        rule_names = [r.rule_name for r in triggered_rules]
        count = len(triggered_rules)
        
        severity_text = {
            RuleSeverity.LOW: "Minor anomaly detected",
            RuleSeverity.MEDIUM: "Moderate anomaly detected",
            RuleSeverity.HIGH: "Significant anomaly detected",
            RuleSeverity.CRITICAL: "CRITICAL: Immediate attention required"
        }
        
        summary = f"{severity_text.get(severity, 'Anomaly detected')}. "
        summary += f"{count} rule(s) triggered: {', '.join(rule_names)}. "
        
        # Add specific details for critical rules
        for rule in triggered_rules:
            if rule.severity == RuleSeverity.CRITICAL:
                summary += f"{rule.description}. "
        
        return summary
    
    def _generate_recommendation(
        self,
        triggered_rules: List[RuleResult],
        severity: RuleSeverity
    ) -> str:
        """Generate recommended action."""
        
        if not triggered_rules:
            return "Continue routine monitoring."
        
        recommendations = {
            RuleSeverity.LOW: "Monitor for persistence. Review again in 24 hours.",
            RuleSeverity.MEDIUM: "Investigate within 72 hours. Check for operational changes.",
            RuleSeverity.HIGH: "Investigate within 24 hours. Prepare for field inspection.",
            RuleSeverity.CRITICAL: "IMMEDIATE: Dispatch field team. Possible burst or major leak."
        }
        
        base_rec = recommendations.get(severity, "Investigate as needed.")
        
        # Add specific recommendations based on rules
        rule_names = [r.rule_name for r in triggered_rules]
        
        if 'night_day_ratio' in rule_names:
            base_rec += " Night analysis suggests leak - deploy acoustic equipment."
        
        if 'sudden_drop' in rule_names:
            base_rec += " Rapid pressure drop may indicate burst - check visible pipe sections."
        
        if 'gradient_change' in rule_names:
            base_rec += " Gradient change suggests leak between sensors."
        
        return base_rec
    
    def _calculate_confidence(self, triggered_rules: List[RuleResult]) -> float:
        """
        Calculate confidence score for comparison with AI.
        
        Baseline confidence is simpler than AI:
        - Based on rule count and severity
        - Does not account for complex interactions
        """
        if not triggered_rules:
            return 0.0
        
        # Base confidence from severity
        severity_confidence = {
            RuleSeverity.LOW: 0.3,
            RuleSeverity.MEDIUM: 0.5,
            RuleSeverity.HIGH: 0.7,
            RuleSeverity.CRITICAL: 0.9
        }
        
        max_severity = max(r.severity for r in triggered_rules)
        base = severity_confidence.get(max_severity, 0.3)
        
        # Boost for multiple rules agreeing
        rule_boost = min(len(triggered_rules) * 0.05, 0.1)
        
        return min(base + rule_boost, 1.0)


class BaselineVsAIComparison:
    """
    Compare baseline and AI system performance.
    
    This class provides the mandatory comparison between:
    1. Physics-based threshold rules (baseline)
    2. AI-based detection (Layers 1-3)
    
    Metrics compared:
    - True positive rate (leak detection)
    - False positive rate (false alarms)
    - Detection latency (time to detect)
    - Localization accuracy
    """
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        
    def log_comparison(
        self,
        sensor_id: str,
        baseline_result: BaselineDetectionResult,
        ai_probability: float,
        ai_anomaly_score: float,
        actual_leak: Optional[bool] = None
    ) -> None:
        """Log a comparison result."""
        
        self.results.append({
            'timestamp': datetime.utcnow(),
            'sensor_id': sensor_id,
            'baseline_alert': baseline_result.alert,
            'baseline_severity': baseline_result.severity.value,
            'baseline_confidence': baseline_result.confidence,
            'ai_probability': ai_probability,
            'ai_anomaly_score': ai_anomaly_score,
            'ai_alert': ai_probability > 0.5,
            'actual_leak': actual_leak,
            'baseline_rules_triggered': len(baseline_result.triggered_rules)
        })
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comparative metrics."""
        
        if not self.results:
            return {'status': 'insufficient_data'}
        
        df = pd.DataFrame(self.results)
        
        metrics = {
            'total_samples': len(df),
            'baseline': {},
            'ai': {},
            'comparison': {}
        }
        
        # Calculate baseline metrics
        baseline_alerts = df['baseline_alert'].sum()
        metrics['baseline']['alert_count'] = int(baseline_alerts)
        metrics['baseline']['alert_rate'] = float(baseline_alerts / len(df))
        
        # Calculate AI metrics
        ai_alerts = df['ai_alert'].sum()
        metrics['ai']['alert_count'] = int(ai_alerts)
        metrics['ai']['alert_rate'] = float(ai_alerts / len(df))
        
        # If we have ground truth
        confirmed = df[df['actual_leak'].notna()]
        if len(confirmed) > 0:
            # True positives (correctly detected leaks)
            baseline_tp = ((confirmed['baseline_alert']) & (confirmed['actual_leak'])).sum()
            ai_tp = ((confirmed['ai_alert']) & (confirmed['actual_leak'])).sum()
            
            # False positives (alerts when no leak)
            baseline_fp = ((confirmed['baseline_alert']) & (~confirmed['actual_leak'])).sum()
            ai_fp = ((confirmed['ai_alert']) & (~confirmed['actual_leak'])).sum()
            
            # Actual leaks
            actual_leaks = confirmed['actual_leak'].sum()
            actual_non_leaks = (~confirmed['actual_leak']).sum()
            
            if actual_leaks > 0:
                metrics['baseline']['true_positive_rate'] = float(baseline_tp / actual_leaks)
                metrics['ai']['true_positive_rate'] = float(ai_tp / actual_leaks)
            
            if actual_non_leaks > 0:
                metrics['baseline']['false_positive_rate'] = float(baseline_fp / actual_non_leaks)
                metrics['ai']['false_positive_rate'] = float(ai_fp / actual_non_leaks)
            
            # AI improvement
            if metrics['baseline'].get('true_positive_rate', 0) > 0:
                tpr_improvement = (
                    metrics['ai'].get('true_positive_rate', 0) - 
                    metrics['baseline']['true_positive_rate']
                )
                metrics['comparison']['tpr_improvement'] = float(tpr_improvement)
            
            if metrics['baseline'].get('false_positive_rate', 0) > 0:
                fpr_reduction = (
                    metrics['baseline']['false_positive_rate'] - 
                    metrics['ai'].get('false_positive_rate', 0)
                )
                metrics['comparison']['fpr_reduction'] = float(fpr_reduction)
        
        # Agreement rate
        agreement = (df['baseline_alert'] == df['ai_alert']).mean()
        metrics['comparison']['agreement_rate'] = float(agreement)
        
        # AI only detections (caught by AI, missed by baseline)
        ai_only = ((df['ai_alert']) & (~df['baseline_alert'])).sum()
        metrics['comparison']['ai_only_detections'] = int(ai_only)
        
        # Baseline only (caught by baseline, missed by AI)
        baseline_only = ((df['baseline_alert']) & (~df['ai_alert'])).sum()
        metrics['comparison']['baseline_only_detections'] = int(baseline_only)
        
        return metrics
    
    def generate_report(self) -> str:
        """Generate comparison report."""
        
        metrics = self.calculate_metrics()
        
        if metrics.get('status') == 'insufficient_data':
            return "Insufficient data for comparison report."
        
        report = """
BASELINE VS AI COMPARISON REPORT
================================

Overview:
---------
Total samples analyzed: {total}

Alert Rates:
-----------
Baseline system: {baseline_alerts} alerts ({baseline_rate:.1%})
AI system: {ai_alerts} alerts ({ai_rate:.1%})

""".format(
            total=metrics['total_samples'],
            baseline_alerts=metrics['baseline']['alert_count'],
            baseline_rate=metrics['baseline']['alert_rate'],
            ai_alerts=metrics['ai']['alert_count'],
            ai_rate=metrics['ai']['alert_rate']
        )
        
        if 'true_positive_rate' in metrics.get('baseline', {}):
            report += """
Performance (on confirmed events):
----------------------------------
                    Baseline    AI      Improvement
True Positive Rate: {base_tpr:.1%}     {ai_tpr:.1%}    {tpr_imp:+.1%}
False Positive Rate: {base_fpr:.1%}     {ai_fpr:.1%}    {fpr_red:+.1%}

""".format(
                base_tpr=metrics['baseline'].get('true_positive_rate', 0),
                ai_tpr=metrics['ai'].get('true_positive_rate', 0),
                tpr_imp=metrics['comparison'].get('tpr_improvement', 0),
                base_fpr=metrics['baseline'].get('false_positive_rate', 0),
                ai_fpr=metrics['ai'].get('false_positive_rate', 0),
                fpr_red=metrics['comparison'].get('fpr_reduction', 0)
            )
        
        report += """
Agreement Analysis:
-------------------
Baseline and AI agree: {agreement:.1%}
AI-only detections: {ai_only} (leaks caught by AI, missed by baseline)
Baseline-only detections: {baseline_only} (caught by baseline, missed by AI)

Conclusion:
-----------
""".format(
            agreement=metrics['comparison']['agreement_rate'],
            ai_only=metrics['comparison']['ai_only_detections'],
            baseline_only=metrics['comparison']['baseline_only_detections']
        )
        
        # Generate conclusion
        tpr_imp = metrics['comparison'].get('tpr_improvement', 0)
        fpr_red = metrics['comparison'].get('fpr_reduction', 0)
        
        if tpr_imp > 0.05 and fpr_red > 0.05:
            report += "AI system significantly outperforms baseline on both detection rate and false alarm reduction."
        elif tpr_imp > 0.05:
            report += "AI system detects more leaks than baseline. Similar false alarm rates."
        elif fpr_red > 0.05:
            report += "AI system reduces false alarms compared to baseline. Similar detection rates."
        else:
            report += "AI and baseline systems show similar performance. Continue data collection."
        
        return report
