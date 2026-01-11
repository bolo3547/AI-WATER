"""
AquaWatch Customer Self-Service Portal
======================================
Consumer-facing portal with usage insights, billing, and leak reporting.
Empowers customers with real-time consumption data and conservation tools.

Features:
- Real-time consumption monitoring
- Bill prediction and management
- Leak alert notifications
- Conservation tips and gamification
- Service request submission
- Payment integration
- Usage comparison with neighbors
"""

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import hashlib
import json
from collections import defaultdict


class CustomerType(Enum):
    """Types of customers"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INSTITUTIONAL = "institutional"


class AlertType(Enum):
    """Types of customer alerts"""
    HIGH_CONSUMPTION = "high_consumption"
    SUSPECTED_LEAK = "suspected_leak"
    BILL_DUE = "bill_due"
    SERVICE_DISRUPTION = "service_disruption"
    WATER_QUALITY = "water_quality"
    CONSERVATION_TIP = "conservation_tip"
    ACHIEVEMENT = "achievement"


class ServiceRequestType(Enum):
    """Types of service requests"""
    LEAK_REPORT = "leak_report"
    METER_ISSUE = "meter_issue"
    BILLING_QUERY = "billing_query"
    NEW_CONNECTION = "new_connection"
    DISCONNECTION = "disconnection"
    RECONNECTION = "reconnection"
    WATER_QUALITY = "water_quality_complaint"
    PRESSURE_ISSUE = "pressure_issue"


class ServiceRequestStatus(Enum):
    """Status of service requests"""
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class CustomerProfile:
    """Customer profile with account details"""
    customer_id: str
    account_number: str
    name: str
    email: str
    phone: str
    customer_type: CustomerType
    
    # Address
    address: str
    zone: str
    dma: str
    
    # Meter details
    meter_id: str
    meter_type: str
    
    # Account status
    is_active: bool = True
    registration_date: datetime = field(default_factory=datetime.now)
    
    # Consumption baseline
    avg_daily_consumption: float = 0.0  # m³/day
    conservation_score: int = 50  # 0-100
    
    # Gamification
    points: int = 0
    badges: List[str] = field(default_factory=list)
    tier: str = "bronze"


@dataclass
class ConsumptionRecord:
    """Water consumption record"""
    timestamp: datetime
    meter_id: str
    reading: float  # m³
    consumption: float  # m³ in period
    period_hours: int = 24


@dataclass
class BillRecord:
    """Billing record"""
    bill_id: str
    customer_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    
    # Consumption
    opening_reading: float
    closing_reading: float
    consumption_m3: float
    
    # Charges (ZMW)
    water_charge: float
    sewerage_charge: float
    service_charge: float
    vat: float
    total_amount: float
    
    # Payment
    due_date: datetime
    paid: bool = False
    payment_date: Optional[datetime] = None
    
    # Status
    is_overdue: bool = False


@dataclass
class ServiceRequest:
    """Customer service request"""
    request_id: str
    customer_id: str
    request_type: ServiceRequestType
    status: ServiceRequestStatus
    
    # Details
    description: str
    location: str
    priority: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Assignment
    assigned_to: Optional[str] = None
    
    # Resolution
    resolution_notes: str = ""


@dataclass
class CustomerAlert:
    """Alert notification for customer"""
    alert_id: str
    customer_id: str
    alert_type: AlertType
    title: str
    message: str
    
    timestamp: datetime
    read: bool = False
    action_url: Optional[str] = None


class TariffEngine:
    """Water tariff calculation engine"""
    
    def __init__(self):
        # LWSC tariff structure (ZMW per m³)
        self.tariffs = {
            CustomerType.RESIDENTIAL: {
                "blocks": [
                    {"limit": 6, "rate": 3.50},      # 0-6 m³
                    {"limit": 30, "rate": 8.50},     # 7-30 m³
                    {"limit": 100, "rate": 12.00},   # 31-100 m³
                    {"limit": float('inf'), "rate": 15.00}  # >100 m³
                ],
                "service_charge": 25.00,
                "sewerage_rate": 0.30  # 30% of water charge
            },
            CustomerType.COMMERCIAL: {
                "blocks": [
                    {"limit": 50, "rate": 15.00},
                    {"limit": 200, "rate": 18.00},
                    {"limit": float('inf'), "rate": 22.00}
                ],
                "service_charge": 50.00,
                "sewerage_rate": 0.35
            },
            CustomerType.INDUSTRIAL: {
                "blocks": [
                    {"limit": 500, "rate": 12.00},
                    {"limit": float('inf'), "rate": 14.00}
                ],
                "service_charge": 100.00,
                "sewerage_rate": 0.40
            }
        }
        
        self.vat_rate = 0.16  # 16% VAT
    
    def calculate_bill(
        self,
        consumption_m3: float,
        customer_type: CustomerType
    ) -> Dict[str, float]:
        """Calculate water bill for given consumption"""
        tariff = self.tariffs.get(customer_type, self.tariffs[CustomerType.RESIDENTIAL])
        
        # Calculate water charge with block tariff
        water_charge = 0.0
        remaining = consumption_m3
        prev_limit = 0
        
        for block in tariff["blocks"]:
            if remaining <= 0:
                break
            
            block_consumption = min(remaining, block["limit"] - prev_limit)
            water_charge += block_consumption * block["rate"]
            remaining -= block_consumption
            prev_limit = block["limit"]
        
        # Sewerage charge
        sewerage_charge = water_charge * tariff["sewerage_rate"]
        
        # Service charge
        service_charge = tariff["service_charge"]
        
        # Subtotal
        subtotal = water_charge + sewerage_charge + service_charge
        
        # VAT
        vat = subtotal * self.vat_rate
        
        return {
            "consumption_m3": consumption_m3,
            "water_charge": water_charge,
            "sewerage_charge": sewerage_charge,
            "service_charge": service_charge,
            "subtotal": subtotal,
            "vat": vat,
            "total": subtotal + vat
        }


class ConsumptionAnalyzer:
    """Analyze customer consumption patterns"""
    
    def __init__(self):
        self.leak_threshold_multiplier = 2.0  # 200% of baseline = potential leak
    
    def analyze_consumption(
        self,
        readings: List[ConsumptionRecord],
        customer: CustomerProfile
    ) -> Dict:
        """Analyze consumption patterns"""
        if len(readings) < 2:
            return {"status": "insufficient_data"}
        
        # Sort by timestamp
        readings = sorted(readings, key=lambda r: r.timestamp)
        
        consumptions = [r.consumption for r in readings]
        
        # Statistics
        avg_consumption = np.mean(consumptions)
        std_consumption = np.std(consumptions)
        latest_consumption = consumptions[-1]
        
        # Trend analysis
        if len(consumptions) >= 7:
            recent_avg = np.mean(consumptions[-7:])
            previous_avg = np.mean(consumptions[-14:-7]) if len(consumptions) >= 14 else avg_consumption
            trend = (recent_avg - previous_avg) / previous_avg * 100 if previous_avg > 0 else 0
        else:
            trend = 0
        
        # Anomaly detection
        is_anomaly = False
        anomaly_type = None
        
        if latest_consumption > avg_consumption * self.leak_threshold_multiplier:
            is_anomaly = True
            anomaly_type = "suspected_leak"
        elif latest_consumption > avg_consumption + 2 * std_consumption:
            is_anomaly = True
            anomaly_type = "high_consumption"
        
        # Efficiency score
        # Compare with average for customer type
        type_averages = {
            CustomerType.RESIDENTIAL: 0.5,  # 500L/day
            CustomerType.COMMERCIAL: 5.0,
            CustomerType.INDUSTRIAL: 50.0
        }
        
        type_avg = type_averages.get(customer.customer_type, 0.5)
        efficiency = max(0, min(100, 100 - (avg_consumption - type_avg) / type_avg * 50))
        
        return {
            "average_daily_m3": avg_consumption,
            "latest_daily_m3": latest_consumption,
            "trend_percentage": trend,
            "trend_direction": "increasing" if trend > 5 else "decreasing" if trend < -5 else "stable",
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type,
            "efficiency_score": efficiency,
            "estimated_monthly_m3": avg_consumption * 30,
            "comparison_to_average": (avg_consumption / type_avg - 1) * 100 if type_avg > 0 else 0
        }
    
    def predict_bill(
        self,
        customer: CustomerProfile,
        days_remaining: int,
        current_consumption: float
    ) -> Dict:
        """Predict end-of-month bill"""
        tariff_engine = TariffEngine()
        
        # Project total consumption
        daily_rate = current_consumption / (30 - days_remaining) if days_remaining < 30 else customer.avg_daily_consumption
        projected_total = current_consumption + daily_rate * days_remaining
        
        # Calculate projected bill
        bill = tariff_engine.calculate_bill(projected_total, customer.customer_type)
        
        # Compare to last month
        last_month_consumption = customer.avg_daily_consumption * 30
        last_month_bill = tariff_engine.calculate_bill(last_month_consumption, customer.customer_type)
        
        return {
            "projected_consumption_m3": projected_total,
            "projected_total_zmw": bill["total"],
            "days_remaining": days_remaining,
            "daily_average_m3": daily_rate,
            "comparison": {
                "last_month_m3": last_month_consumption,
                "last_month_zmw": last_month_bill["total"],
                "difference_zmw": bill["total"] - last_month_bill["total"],
                "difference_percent": (bill["total"] / last_month_bill["total"] - 1) * 100 if last_month_bill["total"] > 0 else 0
            }
        }


class ConservationEngine:
    """Water conservation tips and gamification"""
    
    def __init__(self):
        self.tips = [
            {
                "category": "bathroom",
                "tip": "Fix leaky taps - a dripping tap wastes 15 litres per day",
                "savings_l_day": 15
            },
            {
                "category": "bathroom",
                "tip": "Take shorter showers - each minute saves 12 litres",
                "savings_l_day": 36
            },
            {
                "category": "bathroom",
                "tip": "Install a dual-flush toilet to save up to 80 litres daily",
                "savings_l_day": 80
            },
            {
                "category": "kitchen",
                "tip": "Only run dishwasher when full - saves 20 litres per load",
                "savings_l_day": 20
            },
            {
                "category": "kitchen",
                "tip": "Keep drinking water in the fridge instead of running tap",
                "savings_l_day": 5
            },
            {
                "category": "garden",
                "tip": "Water garden early morning or evening to reduce evaporation",
                "savings_l_day": 50
            },
            {
                "category": "garden",
                "tip": "Use mulch to retain soil moisture and reduce watering",
                "savings_l_day": 30
            },
            {
                "category": "laundry",
                "tip": "Only wash full loads of laundry - saves 50 litres per load",
                "savings_l_day": 50
            },
            {
                "category": "general",
                "tip": "Report public leaks to help save community water",
                "savings_l_day": 100
            }
        ]
        
        self.badges = {
            "water_saver": {
                "name": "Water Saver",
                "description": "Reduced consumption by 10%",
                "points": 100
            },
            "leak_reporter": {
                "name": "Leak Reporter",
                "description": "Reported a water leak",
                "points": 50
            },
            "early_payer": {
                "name": "Early Payer",
                "description": "Paid bill before due date",
                "points": 25
            },
            "conservation_champion": {
                "name": "Conservation Champion",
                "description": "Achieved top 10% efficiency",
                "points": 200
            },
            "community_hero": {
                "name": "Community Hero",
                "description": "Reported 5+ public leaks",
                "points": 500
            }
        }
        
        self.tiers = {
            "bronze": {"min_points": 0, "benefits": "Basic access"},
            "silver": {"min_points": 500, "benefits": "5% bill discount"},
            "gold": {"min_points": 1500, "benefits": "10% bill discount + priority support"},
            "platinum": {"min_points": 5000, "benefits": "15% discount + VIP support + rewards"}
        }
    
    def get_personalized_tips(
        self,
        customer: CustomerProfile,
        consumption_analysis: Dict
    ) -> List[Dict]:
        """Get personalized conservation tips"""
        tips = []
        
        # High consumer tips
        if consumption_analysis.get("comparison_to_average", 0) > 20:
            tips.append({
                "priority": "high",
                "tip": "Your usage is 20% above average. Consider these water-saving measures.",
                "potential_savings_m3": customer.avg_daily_consumption * 0.2 * 30
            })
        
        # Leak-related tips
        if consumption_analysis.get("anomaly_type") == "suspected_leak":
            tips.append({
                "priority": "urgent",
                "tip": "Possible leak detected! Check toilets, taps, and outdoor pipes.",
                "potential_savings_m3": (consumption_analysis["latest_daily_m3"] - 
                                         consumption_analysis["average_daily_m3"]) * 30
            })
        
        # General tips based on customer type
        if customer.customer_type == CustomerType.RESIDENTIAL:
            tips.extend([
                {"priority": "medium", "tip": t["tip"], "potential_savings_l": t["savings_l_day"] * 30}
                for t in self.tips[:5]
            ])
        
        return tips
    
    def award_badge(
        self,
        customer: CustomerProfile,
        badge_id: str
    ) -> Dict:
        """Award a badge to customer"""
        if badge_id not in self.badges:
            return {"success": False, "error": "Badge not found"}
        
        if badge_id in customer.badges:
            return {"success": False, "error": "Badge already earned"}
        
        badge = self.badges[badge_id]
        customer.badges.append(badge_id)
        customer.points += badge["points"]
        
        # Check tier upgrade
        new_tier = customer.tier
        for tier, info in sorted(self.tiers.items(), key=lambda x: x[1]["min_points"], reverse=True):
            if customer.points >= info["min_points"]:
                new_tier = tier
                break
        
        tier_upgraded = new_tier != customer.tier
        customer.tier = new_tier
        
        return {
            "success": True,
            "badge": badge,
            "new_points": customer.points,
            "tier_upgraded": tier_upgraded,
            "new_tier": new_tier if tier_upgraded else None
        }


class CustomerPortal:
    """Main customer self-service portal"""
    
    def __init__(self):
        self.customers: Dict[str, CustomerProfile] = {}
        self.consumption_records: Dict[str, List[ConsumptionRecord]] = defaultdict(list)
        self.bills: Dict[str, List[BillRecord]] = defaultdict(list)
        self.service_requests: Dict[str, List[ServiceRequest]] = defaultdict(list)
        self.alerts: Dict[str, List[CustomerAlert]] = defaultdict(list)
        
        self.tariff_engine = TariffEngine()
        self.consumption_analyzer = ConsumptionAnalyzer()
        self.conservation_engine = ConservationEngine()
        
        # Initialize demo data
        self._initialize_demo_data()
    
    def _initialize_demo_data(self):
        """Initialize demo customers and data"""
        demo_customers = [
            {
                "customer_id": "CUST001",
                "account": "50012345",
                "name": "John Banda",
                "email": "john.banda@email.com",
                "phone": "+260971234567",
                "type": CustomerType.RESIDENTIAL,
                "address": "Plot 123, Kabulonga Road",
                "zone": "Kabulonga",
                "dma": "DMA_KAB_01",
                "meter": "MTR_50012345",
                "avg_consumption": 0.45
            },
            {
                "customer_id": "CUST002",
                "account": "50012346",
                "name": "Mary Mwanza",
                "email": "mary.mwanza@email.com",
                "phone": "+260977654321",
                "type": CustomerType.RESIDENTIAL,
                "address": "House 45, Woodlands Extension",
                "zone": "Woodlands",
                "dma": "DMA_WDL_02",
                "meter": "MTR_50012346",
                "avg_consumption": 0.35
            },
            {
                "customer_id": "CUST003",
                "account": "50012347",
                "name": "Shoprite Manda Hill",
                "email": "facilities@shoprite.zm",
                "phone": "+260211234567",
                "type": CustomerType.COMMERCIAL,
                "address": "Manda Hill Mall",
                "zone": "CBD",
                "dma": "DMA_CBD_01",
                "meter": "MTR_50012347",
                "avg_consumption": 25.0
            },
            {
                "customer_id": "CUST004",
                "account": "50012348",
                "name": "Zambia Breweries",
                "email": "operations@zambrew.zm",
                "phone": "+260211987654",
                "type": CustomerType.INDUSTRIAL,
                "address": "Industrial Area, Lusaka South",
                "zone": "Industrial",
                "dma": "DMA_IND_01",
                "meter": "MTR_50012348",
                "avg_consumption": 150.0
            }
        ]
        
        for c in demo_customers:
            profile = CustomerProfile(
                customer_id=c["customer_id"],
                account_number=c["account"],
                name=c["name"],
                email=c["email"],
                phone=c["phone"],
                customer_type=c["type"],
                address=c["address"],
                zone=c["zone"],
                dma=c["dma"],
                meter_id=c["meter"],
                meter_type="Smart AMR" if c["type"] != CustomerType.RESIDENTIAL else "Digital",
                avg_daily_consumption=c["avg_consumption"]
            )
            self.customers[profile.customer_id] = profile
            
            # Generate consumption history (last 60 days)
            base_consumption = c["avg_consumption"]
            for days_ago in range(60, 0, -1):
                timestamp = datetime.now() - timedelta(days=days_ago)
                variation = np.random.normal(0, 0.15)  # 15% daily variation
                consumption = max(0, base_consumption * (1 + variation))
                
                record = ConsumptionRecord(
                    timestamp=timestamp,
                    meter_id=c["meter"],
                    reading=sum(r.consumption for r in self.consumption_records[c["customer_id"]]) + consumption,
                    consumption=consumption,
                    period_hours=24
                )
                self.consumption_records[c["customer_id"]].append(record)
            
            # Generate bills
            for month in range(3):
                start = datetime.now().replace(day=1) - timedelta(days=30 * (month + 1))
                end = start + timedelta(days=29)
                monthly_consumption = base_consumption * 30 * (1 + np.random.normal(0, 0.1))
                
                bill_details = self.tariff_engine.calculate_bill(monthly_consumption, c["type"])
                
                bill = BillRecord(
                    bill_id=f"BILL_{c['customer_id']}_{start.strftime('%Y%m')}",
                    customer_id=c["customer_id"],
                    billing_period_start=start,
                    billing_period_end=end,
                    opening_reading=0,
                    closing_reading=monthly_consumption,
                    consumption_m3=monthly_consumption,
                    water_charge=bill_details["water_charge"],
                    sewerage_charge=bill_details["sewerage_charge"],
                    service_charge=bill_details["service_charge"],
                    vat=bill_details["vat"],
                    total_amount=bill_details["total"],
                    due_date=end + timedelta(days=14),
                    paid=month > 0,
                    payment_date=end + timedelta(days=10) if month > 0 else None
                )
                self.bills[c["customer_id"]].append(bill)
    
    def get_customer_dashboard(self, customer_id: str) -> Dict:
        """Get complete customer dashboard"""
        if customer_id not in self.customers:
            return {"error": "Customer not found"}
        
        customer = self.customers[customer_id]
        records = self.consumption_records.get(customer_id, [])
        bills = self.bills.get(customer_id, [])
        alerts = self.alerts.get(customer_id, [])
        
        # Analyze consumption
        analysis = self.consumption_analyzer.analyze_consumption(records, customer)
        
        # Get latest bill
        latest_bill = max(bills, key=lambda b: b.billing_period_end) if bills else None
        
        # Predict next bill
        days_into_month = datetime.now().day
        current_month_consumption = sum(
            r.consumption for r in records
            if r.timestamp.month == datetime.now().month
        )
        prediction = self.consumption_analyzer.predict_bill(
            customer, 
            30 - days_into_month, 
            current_month_consumption
        )
        
        # Get tips
        tips = self.conservation_engine.get_personalized_tips(customer, analysis)
        
        # Unread alerts
        unread_alerts = [a for a in alerts if not a.read]
        
        return {
            "customer": {
                "id": customer.customer_id,
                "name": customer.name,
                "account_number": customer.account_number,
                "type": customer.customer_type.value,
                "zone": customer.zone,
                "meter_id": customer.meter_id
            },
            "consumption": {
                "today_m3": records[-1].consumption if records else 0,
                "this_month_m3": current_month_consumption,
                "average_daily_m3": analysis.get("average_daily_m3", 0),
                "trend": analysis.get("trend_direction", "stable"),
                "efficiency_score": analysis.get("efficiency_score", 50)
            },
            "billing": {
                "latest_bill": {
                    "period": f"{latest_bill.billing_period_start.strftime('%B %Y')}" if latest_bill else "N/A",
                    "amount_zmw": latest_bill.total_amount if latest_bill else 0,
                    "status": "Paid" if (latest_bill and latest_bill.paid) else "Unpaid",
                    "due_date": latest_bill.due_date.strftime('%Y-%m-%d') if latest_bill else None
                },
                "prediction": {
                    "estimated_m3": prediction["projected_consumption_m3"],
                    "estimated_zmw": prediction["projected_total_zmw"],
                    "vs_last_month": prediction["comparison"]["difference_percent"]
                }
            },
            "alerts": {
                "unread_count": len(unread_alerts),
                "recent": [
                    {"type": a.alert_type.value, "title": a.title, "time": a.timestamp.isoformat()}
                    for a in sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:5]
                ]
            },
            "gamification": {
                "points": customer.points,
                "tier": customer.tier,
                "badges": customer.badges,
                "conservation_score": customer.conservation_score
            },
            "tips": tips[:3]
        }
    
    def submit_service_request(
        self,
        customer_id: str,
        request_type: ServiceRequestType,
        description: str,
        location: str = None
    ) -> ServiceRequest:
        """Submit a service request"""
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        request = ServiceRequest(
            request_id=f"SR_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            customer_id=customer_id,
            request_type=request_type,
            status=ServiceRequestStatus.SUBMITTED,
            description=description,
            location=location or customer.address,
            priority="normal" if request_type != ServiceRequestType.LEAK_REPORT else "high",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.service_requests[customer_id].append(request)
        
        # Award badge for leak report
        if request_type == ServiceRequestType.LEAK_REPORT:
            self.conservation_engine.award_badge(customer, "leak_reporter")
        
        return request
    
    def get_consumption_history(
        self,
        customer_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get consumption history for charting"""
        records = self.consumption_records.get(customer_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = [r for r in records if r.timestamp >= cutoff]
        
        return [
            {
                "date": r.timestamp.strftime("%Y-%m-%d"),
                "consumption_m3": r.consumption,
                "reading": r.reading
            }
            for r in sorted(filtered, key=lambda x: x.timestamp)
        ]
    
    def get_billing_history(self, customer_id: str) -> List[Dict]:
        """Get billing history"""
        bills = self.bills.get(customer_id, [])
        
        return [
            {
                "bill_id": b.bill_id,
                "period": f"{b.billing_period_start.strftime('%b')} - {b.billing_period_end.strftime('%b %Y')}",
                "consumption_m3": b.consumption_m3,
                "total_zmw": b.total_amount,
                "paid": b.paid,
                "due_date": b.due_date.strftime("%Y-%m-%d")
            }
            for b in sorted(bills, key=lambda x: x.billing_period_end, reverse=True)
        ]
    
    def get_neighbor_comparison(self, customer_id: str) -> Dict:
        """Compare consumption with similar customers in zone"""
        customer = self.customers.get(customer_id)
        if not customer:
            return {"error": "Customer not found"}
        
        # Get similar customers in same zone
        similar = [
            c for c in self.customers.values()
            if c.zone == customer.zone and 
            c.customer_type == customer.customer_type and
            c.customer_id != customer_id
        ]
        
        if not similar:
            return {
                "your_consumption": customer.avg_daily_consumption,
                "comparison": "No similar customers in your area"
            }
        
        avg_similar = np.mean([c.avg_daily_consumption for c in similar])
        
        percentile = sum(
            1 for c in similar if c.avg_daily_consumption > customer.avg_daily_consumption
        ) / len(similar) * 100
        
        return {
            "your_consumption_m3": customer.avg_daily_consumption,
            "zone_average_m3": avg_similar,
            "difference_percent": (customer.avg_daily_consumption / avg_similar - 1) * 100,
            "percentile": percentile,
            "comparison_text": (
                f"You use {'less' if customer.avg_daily_consumption < avg_similar else 'more'} "
                f"water than {percentile:.0f}% of similar customers in {customer.zone}"
            )
        }
    
    def report_public_leak(
        self,
        customer_id: str,
        location: str,
        description: str,
        latitude: float = None,
        longitude: float = None
    ) -> Dict:
        """Report a public leak"""
        customer = self.customers.get(customer_id)
        if not customer:
            return {"error": "Customer not found"}
        
        request = self.submit_service_request(
            customer_id,
            ServiceRequestType.LEAK_REPORT,
            f"Public leak: {description}",
            location
        )
        request.priority = "high"
        
        # Award points
        customer.points += 25
        
        # Check for community hero badge
        leak_reports = [
            r for r in self.service_requests.get(customer_id, [])
            if r.request_type == ServiceRequestType.LEAK_REPORT
        ]
        if len(leak_reports) >= 5:
            self.conservation_engine.award_badge(customer, "community_hero")
        
        return {
            "request_id": request.request_id,
            "status": "submitted",
            "message": "Thank you for reporting! Your report helps save water for the community.",
            "points_earned": 25,
            "total_points": customer.points
        }


# Global instance
customer_portal = CustomerPortal()


def get_customer_portal() -> CustomerPortal:
    """Get global customer portal"""
    return customer_portal


if __name__ == "__main__":
    # Demo
    portal = CustomerPortal()
    
    print("=" * 60)
    print("AquaWatch Customer Self-Service Portal")
    print("=" * 60)
    
    # Get customer dashboard
    customer_id = "CUST001"
    dashboard = portal.get_customer_dashboard(customer_id)
    
    print(f"\nCustomer: {dashboard['customer']['name']}")
    print(f"Account: {dashboard['customer']['account_number']}")
    print(f"Zone: {dashboard['customer']['zone']}")
    
    print(f"\n📊 Consumption:")
    print(f"  Today: {dashboard['consumption']['today_m3']:.2f} m³")
    print(f"  This Month: {dashboard['consumption']['this_month_m3']:.2f} m³")
    print(f"  Average Daily: {dashboard['consumption']['average_daily_m3']:.2f} m³")
    print(f"  Trend: {dashboard['consumption']['trend']}")
    print(f"  Efficiency Score: {dashboard['consumption']['efficiency_score']:.0f}/100")
    
    print(f"\n💰 Billing:")
    print(f"  Latest Bill: K{dashboard['billing']['latest_bill']['amount_zmw']:.2f}")
    print(f"  Status: {dashboard['billing']['latest_bill']['status']}")
    print(f"  Predicted Next Bill: K{dashboard['billing']['prediction']['estimated_zmw']:.2f}")
    
    print(f"\n🏆 Gamification:")
    print(f"  Points: {dashboard['gamification']['points']}")
    print(f"  Tier: {dashboard['gamification']['tier'].title()}")
    
    print(f"\n💡 Conservation Tips:")
    for tip in dashboard['tips']:
        print(f"  • {tip['tip']}")
    
    # Neighbor comparison
    comparison = portal.get_neighbor_comparison(customer_id)
    print(f"\n🏘️ Neighbor Comparison:")
    print(f"  {comparison.get('comparison_text', 'N/A')}")
