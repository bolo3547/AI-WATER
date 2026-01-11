"""
AquaWatch Enterprise - Water-as-a-Service Platform
==================================================

"Netflix for water management."

Complete B2B SaaS platform for enterprise water management:
1. Multi-tenant architecture
2. API-first design
3. Usage-based pricing
4. White-label options
5. Integration marketplace
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# SUBSCRIPTION TIERS
# =============================================================================

class SubscriptionTier(Enum):
    STARTER = "starter"           # Small facilities
    PROFESSIONAL = "professional"  # Medium enterprises
    ENTERPRISE = "enterprise"      # Large corporations
    UNLIMITED = "unlimited"        # Fortune 500


@dataclass
class PricingPlan:
    """Subscription pricing plan."""
    tier: SubscriptionTier
    name: str
    monthly_base_usd: float
    
    # Usage limits
    max_facilities: int
    max_sensors_per_facility: int
    max_api_calls_month: int
    
    # Features
    features: List[str] = field(default_factory=list)
    
    # Usage-based pricing
    price_per_extra_sensor: float = 10.0
    price_per_1000_api_calls: float = 1.0
    price_per_report: float = 5.0


# Pricing plans
PRICING_PLANS = {
    SubscriptionTier.STARTER: PricingPlan(
        tier=SubscriptionTier.STARTER,
        name="Starter",
        monthly_base_usd=499,
        max_facilities=1,
        max_sensors_per_facility=50,
        max_api_calls_month=10000,
        features=[
            "Real-time monitoring",
            "Basic leak detection",
            "Email alerts",
            "Monthly reports",
            "Email support"
        ]
    ),
    SubscriptionTier.PROFESSIONAL: PricingPlan(
        tier=SubscriptionTier.PROFESSIONAL,
        name="Professional",
        monthly_base_usd=1999,
        max_facilities=5,
        max_sensors_per_facility=200,
        max_api_calls_month=100000,
        features=[
            "Everything in Starter",
            "AI-powered anomaly detection",
            "Predictive maintenance",
            "SMS & WhatsApp alerts",
            "Custom dashboards",
            "API access",
            "Weekly reports",
            "Priority support",
            "ESG reporting (basic)"
        ]
    ),
    SubscriptionTier.ENTERPRISE: PricingPlan(
        tier=SubscriptionTier.ENTERPRISE,
        name="Enterprise",
        monthly_base_usd=9999,
        max_facilities=50,
        max_sensors_per_facility=1000,
        max_api_calls_month=1000000,
        features=[
            "Everything in Professional",
            "Autonomous control",
            "Digital twin",
            "Drone integration",
            "Blockchain water credits",
            "Supply chain footprint",
            "Full ESG compliance suite",
            "White-label option",
            "Dedicated success manager",
            "24/7 support",
            "SLA guarantee"
        ]
    ),
    SubscriptionTier.UNLIMITED: PricingPlan(
        tier=SubscriptionTier.UNLIMITED,
        name="Unlimited",
        monthly_base_usd=49999,
        max_facilities=9999,
        max_sensors_per_facility=9999,
        max_api_calls_month=9999999,
        features=[
            "Everything in Enterprise",
            "Unlimited facilities & sensors",
            "Custom AI model training",
            "On-premise deployment option",
            "Custom integrations",
            "Board-level reporting",
            "Dedicated infrastructure",
            "Quarterly business reviews"
        ]
    )
}


# =============================================================================
# TENANT MANAGEMENT
# =============================================================================

@dataclass
class Tenant:
    """SaaS tenant (customer organization)."""
    tenant_id: str
    company_name: str
    industry: str
    country: str
    
    # Subscription
    subscription_tier: SubscriptionTier
    subscription_start: datetime
    subscription_end: datetime
    
    # Usage
    facilities_count: int = 0
    total_sensors: int = 0
    api_calls_this_month: int = 0
    
    # Billing
    billing_email: str = ""
    payment_method: str = ""
    
    # Settings
    white_label_enabled: bool = False
    custom_domain: str = ""
    branding: Dict = field(default_factory=dict)
    
    # Status
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class TenantManager:
    """
    Multi-tenant management system.
    
    "One platform, thousands of customers, complete isolation."
    """
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> tenant_id
    
    def create_tenant(self, 
                      company_name: str,
                      industry: str,
                      country: str,
                      tier: SubscriptionTier = SubscriptionTier.STARTER,
                      billing_email: str = "") -> Tenant:
        """Create new tenant."""
        
        tenant_id = f"TEN_{uuid.uuid4().hex[:12].upper()}"
        
        tenant = Tenant(
            tenant_id=tenant_id,
            company_name=company_name,
            industry=industry,
            country=country,
            subscription_tier=tier,
            subscription_start=datetime.now(timezone.utc),
            subscription_end=datetime.now(timezone.utc) + timedelta(days=365),
            billing_email=billing_email
        )
        
        self.tenants[tenant_id] = tenant
        
        # Generate API key
        api_key = self._generate_api_key(tenant_id)
        self.api_keys[api_key] = tenant_id
        
        logger.info(f"Created tenant: {company_name} ({tenant_id})")
        
        return tenant
    
    def _generate_api_key(self, tenant_id: str) -> str:
        """Generate API key for tenant."""
        raw = f"{tenant_id}:{datetime.now().isoformat()}:{uuid.uuid4()}"
        return f"awk_{hashlib.sha256(raw.encode()).hexdigest()[:32]}"
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant from API key."""
        tenant_id = self.api_keys.get(api_key)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None
    
    def upgrade_tier(self, tenant_id: str, new_tier: SubscriptionTier) -> Dict:
        """Upgrade tenant subscription."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        old_tier = tenant.subscription_tier
        tenant.subscription_tier = new_tier
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
            "new_monthly_cost": PRICING_PLANS[new_tier].monthly_base_usd
        }
    
    def calculate_monthly_bill(self, tenant_id: str) -> Dict:
        """Calculate monthly bill for tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        plan = PRICING_PLANS[tenant.subscription_tier]
        
        # Base cost
        base_cost = plan.monthly_base_usd
        
        # Extra sensors
        total_allowed_sensors = plan.max_facilities * plan.max_sensors_per_facility
        extra_sensors = max(0, tenant.total_sensors - total_allowed_sensors)
        sensor_cost = extra_sensors * plan.price_per_extra_sensor
        
        # Extra API calls
        extra_api_calls = max(0, tenant.api_calls_this_month - plan.max_api_calls_month)
        api_cost = (extra_api_calls / 1000) * plan.price_per_1000_api_calls
        
        total = base_cost + sensor_cost + api_cost
        
        return {
            "tenant_id": tenant_id,
            "company": tenant.company_name,
            "billing_period": datetime.now().strftime("%B %Y"),
            "subscription": {
                "tier": tenant.subscription_tier.value,
                "base_cost": base_cost
            },
            "usage": {
                "facilities": tenant.facilities_count,
                "sensors": tenant.total_sensors,
                "api_calls": tenant.api_calls_this_month
            },
            "overages": {
                "extra_sensors": extra_sensors,
                "sensor_overage_cost": sensor_cost,
                "extra_api_calls": extra_api_calls,
                "api_overage_cost": api_cost
            },
            "total_usd": total
        }


# =============================================================================
# API GATEWAY
# =============================================================================

@dataclass
class RateLimit:
    """API rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000


class APIGateway:
    """
    Enterprise API gateway.
    
    Features:
    - Rate limiting
    - Authentication
    - Usage tracking
    - Webhooks
    """
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.usage_log: List[Dict] = []
        
        # Rate limits by tier
        self.rate_limits = {
            SubscriptionTier.STARTER: RateLimit(30, 500, 5000),
            SubscriptionTier.PROFESSIONAL: RateLimit(60, 2000, 20000),
            SubscriptionTier.ENTERPRISE: RateLimit(300, 10000, 100000),
            SubscriptionTier.UNLIMITED: RateLimit(1000, 50000, 500000)
        }
    
    def authenticate(self, api_key: str) -> Dict:
        """Authenticate API request."""
        tenant = self.tenant_manager.get_tenant_by_api_key(api_key)
        
        if not tenant:
            return {"authenticated": False, "error": "Invalid API key"}
        
        if not tenant.is_active:
            return {"authenticated": False, "error": "Subscription inactive"}
        
        if tenant.subscription_end < datetime.now(timezone.utc):
            return {"authenticated": False, "error": "Subscription expired"}
        
        return {
            "authenticated": True,
            "tenant_id": tenant.tenant_id,
            "company": tenant.company_name,
            "tier": tenant.subscription_tier.value,
            "rate_limit": self.rate_limits[tenant.subscription_tier]
        }
    
    def log_request(self, 
                    tenant_id: str,
                    endpoint: str,
                    method: str,
                    response_code: int):
        """Log API request for billing."""
        self.usage_log.append({
            "tenant_id": tenant_id,
            "endpoint": endpoint,
            "method": method,
            "response_code": response_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Update tenant usage
        tenant = self.tenant_manager.tenants.get(tenant_id)
        if tenant:
            tenant.api_calls_this_month += 1
    
    def get_api_endpoints(self, tier: SubscriptionTier) -> List[Dict]:
        """Get available API endpoints for tier."""
        
        base_endpoints = [
            {"path": "/v1/sensors", "methods": ["GET", "POST"], "description": "Manage sensors"},
            {"path": "/v1/readings", "methods": ["GET", "POST"], "description": "Sensor readings"},
            {"path": "/v1/alerts", "methods": ["GET"], "description": "View alerts"},
            {"path": "/v1/reports", "methods": ["GET"], "description": "Generate reports"},
        ]
        
        professional_endpoints = [
            {"path": "/v1/analytics", "methods": ["GET"], "description": "Advanced analytics"},
            {"path": "/v1/predictions", "methods": ["GET"], "description": "AI predictions"},
            {"path": "/v1/dashboards", "methods": ["GET", "POST"], "description": "Custom dashboards"},
        ]
        
        enterprise_endpoints = [
            {"path": "/v1/twin", "methods": ["GET", "POST"], "description": "Digital twin"},
            {"path": "/v1/autonomous", "methods": ["GET", "POST"], "description": "Autonomous control"},
            {"path": "/v1/drones", "methods": ["GET", "POST"], "description": "Drone fleet"},
            {"path": "/v1/blockchain", "methods": ["GET", "POST"], "description": "Water credits"},
            {"path": "/v1/esg", "methods": ["GET"], "description": "ESG reports"},
            {"path": "/v1/supply-chain", "methods": ["GET", "POST"], "description": "Supply chain"},
        ]
        
        endpoints = base_endpoints.copy()
        
        if tier in [SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE, SubscriptionTier.UNLIMITED]:
            endpoints.extend(professional_endpoints)
        
        if tier in [SubscriptionTier.ENTERPRISE, SubscriptionTier.UNLIMITED]:
            endpoints.extend(enterprise_endpoints)
        
        return endpoints


# =============================================================================
# INTEGRATION MARKETPLACE
# =============================================================================

@dataclass
class Integration:
    """Third-party integration."""
    integration_id: str
    name: str
    category: str  # ERP, CRM, IoT, Analytics, etc.
    provider: str
    description: str
    
    # Pricing
    monthly_cost: float = 0.0
    setup_cost: float = 0.0
    
    # Technical
    api_type: str = "REST"  # REST, GraphQL, SOAP, Webhook
    documentation_url: str = ""
    
    # Status
    is_certified: bool = True
    min_tier: SubscriptionTier = SubscriptionTier.PROFESSIONAL


class IntegrationMarketplace:
    """
    Marketplace for third-party integrations.
    
    "Connect AquaWatch to your entire tech stack."
    """
    
    def __init__(self):
        self.integrations: Dict[str, Integration] = {}
        self.tenant_integrations: Dict[str, List[str]] = {}  # tenant_id -> [integration_ids]
        
        self._load_integrations()
    
    def _load_integrations(self):
        """Load available integrations."""
        integrations = [
            # ERP
            Integration("INT_SAP", "SAP S/4HANA", "ERP", "SAP",
                       "Sync water data with SAP for cost allocation and sustainability reporting",
                       monthly_cost=500, setup_cost=2000, min_tier=SubscriptionTier.ENTERPRISE),
            Integration("INT_ORACLE", "Oracle ERP Cloud", "ERP", "Oracle",
                       "Connect water metrics to Oracle financial and operations modules",
                       monthly_cost=400, setup_cost=1500, min_tier=SubscriptionTier.ENTERPRISE),
            
            # IoT Platforms
            Integration("INT_AWS_IOT", "AWS IoT Core", "IoT", "Amazon",
                       "Connect sensors through AWS IoT for global scale",
                       monthly_cost=0, setup_cost=500, min_tier=SubscriptionTier.PROFESSIONAL),
            Integration("INT_AZURE_IOT", "Azure IoT Hub", "IoT", "Microsoft",
                       "Enterprise IoT connectivity with Azure",
                       monthly_cost=0, setup_cost=500, min_tier=SubscriptionTier.PROFESSIONAL),
            
            # SCADA
            Integration("INT_SCADA", "SCADA Systems", "Industrial", "Various",
                       "Connect to existing SCADA infrastructure via OPC-UA",
                       monthly_cost=200, setup_cost=3000, min_tier=SubscriptionTier.ENTERPRISE),
            
            # Analytics
            Integration("INT_POWERBI", "Power BI", "Analytics", "Microsoft",
                       "Advanced visualizations and executive dashboards",
                       monthly_cost=50, setup_cost=200, min_tier=SubscriptionTier.PROFESSIONAL),
            Integration("INT_TABLEAU", "Tableau", "Analytics", "Salesforce",
                       "Enterprise analytics and data visualization",
                       monthly_cost=100, setup_cost=500, min_tier=SubscriptionTier.PROFESSIONAL),
            
            # Communication
            Integration("INT_SLACK", "Slack", "Communication", "Salesforce",
                       "Send alerts and reports to Slack channels",
                       monthly_cost=0, setup_cost=0, min_tier=SubscriptionTier.STARTER),
            Integration("INT_TEAMS", "Microsoft Teams", "Communication", "Microsoft",
                       "Integrate with Teams for notifications and bot commands",
                       monthly_cost=0, setup_cost=0, min_tier=SubscriptionTier.STARTER),
            
            # ESG
            Integration("INT_CDP", "CDP Reporter", "ESG", "AquaWatch",
                       "Automatic CDP Water Security questionnaire generation",
                       monthly_cost=200, setup_cost=0, min_tier=SubscriptionTier.ENTERPRISE),
            Integration("INT_ECOVADIS", "EcoVadis", "ESG", "EcoVadis",
                       "Sync water data with EcoVadis sustainability ratings",
                       monthly_cost=150, setup_cost=500, min_tier=SubscriptionTier.ENTERPRISE),
        ]
        
        for integration in integrations:
            self.integrations[integration.integration_id] = integration
    
    def search_integrations(self,
                           category: str = None,
                           tenant_tier: SubscriptionTier = None) -> List[Dict]:
        """Search available integrations."""
        results = []
        
        tier_order = [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, 
                     SubscriptionTier.ENTERPRISE, SubscriptionTier.UNLIMITED]
        
        for integration in self.integrations.values():
            if category and integration.category.lower() != category.lower():
                continue
            
            # Check tier eligibility
            if tenant_tier:
                tenant_index = tier_order.index(tenant_tier)
                min_index = tier_order.index(integration.min_tier)
                if tenant_index < min_index:
                    continue
            
            results.append({
                "id": integration.integration_id,
                "name": integration.name,
                "category": integration.category,
                "provider": integration.provider,
                "description": integration.description,
                "monthly_cost": integration.monthly_cost,
                "setup_cost": integration.setup_cost,
                "min_tier": integration.min_tier.value,
                "is_certified": integration.is_certified
            })
        
        return results
    
    def enable_integration(self, 
                          tenant_id: str,
                          integration_id: str) -> Dict:
        """Enable integration for tenant."""
        
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"error": "Integration not found"}
        
        if tenant_id not in self.tenant_integrations:
            self.tenant_integrations[tenant_id] = []
        
        if integration_id in self.tenant_integrations[tenant_id]:
            return {"error": "Integration already enabled"}
        
        self.tenant_integrations[tenant_id].append(integration_id)
        
        return {
            "success": True,
            "integration": integration.name,
            "setup_cost": integration.setup_cost,
            "monthly_cost": integration.monthly_cost,
            "next_steps": f"Configure {integration.name} in your dashboard settings"
        }


# =============================================================================
# WHITE LABEL CONFIGURATION
# =============================================================================

@dataclass
class WhiteLabelConfig:
    """White-label branding configuration."""
    tenant_id: str
    
    # Branding
    company_name: str
    logo_url: str
    favicon_url: str
    
    # Colors
    primary_color: str = "#0066FF"
    secondary_color: str = "#00CC88"
    background_color: str = "#FFFFFF"
    text_color: str = "#333333"
    
    # Custom domain
    custom_domain: str = ""  # e.g., water.clientcompany.com
    ssl_enabled: bool = True
    
    # Email
    from_email: str = ""  # e.g., alerts@clientcompany.com
    email_footer: str = ""
    
    # Reports
    report_header: str = ""
    report_footer: str = ""
    hide_aquawatch_branding: bool = False


class WhiteLabelManager:
    """
    White-label configuration manager.
    
    "Your brand, our technology."
    """
    
    def __init__(self):
        self.configs: Dict[str, WhiteLabelConfig] = {}
    
    def configure(self, config: WhiteLabelConfig) -> Dict:
        """Configure white-label for tenant."""
        self.configs[config.tenant_id] = config
        
        return {
            "success": True,
            "tenant_id": config.tenant_id,
            "custom_domain": config.custom_domain,
            "branding_applied": True,
            "next_steps": [
                f"Point DNS for {config.custom_domain} to platform.aquawatch.com",
                "SSL certificate will be automatically provisioned",
                "Allow 24-48 hours for full propagation"
            ]
        }
    
    def get_branding(self, tenant_id: str) -> Dict:
        """Get branding for tenant."""
        config = self.configs.get(tenant_id)
        
        if not config:
            # Return default AquaWatch branding
            return {
                "company_name": "AquaWatch",
                "logo_url": "https://aquawatch.com/logo.svg",
                "primary_color": "#0066FF",
                "is_white_label": False
            }
        
        return {
            "company_name": config.company_name,
            "logo_url": config.logo_url,
            "primary_color": config.primary_color,
            "secondary_color": config.secondary_color,
            "custom_domain": config.custom_domain,
            "is_white_label": True
        }


# =============================================================================
# DEMO
# =============================================================================

def demo_waas():
    """Demo Water-as-a-Service platform."""
    
    print("=" * 70)
    print("☁️ AQUAWATCH ENTERPRISE - WATER-AS-A-SERVICE PLATFORM")
    print("=" * 70)
    
    # Pricing
    print("\n💰 SUBSCRIPTION PLANS:")
    print("-" * 50)
    
    for tier, plan in PRICING_PLANS.items():
        print(f"\n{plan.name.upper()} - ${plan.monthly_base_usd:,}/month")
        print(f"  Facilities: {plan.max_facilities}")
        print(f"  Sensors/facility: {plan.max_sensors_per_facility}")
        print(f"  API calls/month: {plan.max_api_calls_month:,}")
        print(f"  Features: {', '.join(plan.features[:3])}...")
    
    # Create tenant
    print("\n\n👥 TENANT MANAGEMENT:")
    print("-" * 50)
    
    tm = TenantManager()
    tenant = tm.create_tenant(
        company_name="Coca-Cola Africa",
        industry="Beverage Manufacturing",
        country="South Africa",
        tier=SubscriptionTier.ENTERPRISE,
        billing_email="water-ops@coca-cola.com"
    )
    
    # Simulate usage
    tenant.facilities_count = 12
    tenant.total_sensors = 1500
    tenant.api_calls_this_month = 250000
    
    print(f"Created: {tenant.company_name}")
    print(f"Tenant ID: {tenant.tenant_id}")
    print(f"Tier: {tenant.subscription_tier.value}")
    
    # Calculate bill
    print("\n📄 MONTHLY BILL:")
    bill = tm.calculate_monthly_bill(tenant.tenant_id)
    print(f"  Base: ${bill['subscription']['base_cost']:,}")
    print(f"  Sensor overage: ${bill['overages']['sensor_overage_cost']:,.0f}")
    print(f"  API overage: ${bill['overages']['api_overage_cost']:,.0f}")
    print(f"  TOTAL: ${bill['total_usd']:,.0f}")
    
    # Integration marketplace
    print("\n\n🔌 INTEGRATION MARKETPLACE:")
    print("-" * 50)
    
    marketplace = IntegrationMarketplace()
    integrations = marketplace.search_integrations(tenant_tier=SubscriptionTier.ENTERPRISE)
    
    print(f"Available integrations for Enterprise tier: {len(integrations)}")
    for i in integrations[:5]:
        print(f"  • {i['name']} ({i['category']}) - ${i['monthly_cost']}/mo")
    
    # API info
    print("\n\n🔑 API ACCESS:")
    print("-" * 50)
    
    api = APIGateway(tm)
    endpoints = api.get_api_endpoints(SubscriptionTier.ENTERPRISE)
    print(f"Available endpoints: {len(endpoints)}")
    for ep in endpoints[:5]:
        print(f"  {ep['methods']} {ep['path']} - {ep['description']}")
    
    # White label
    print("\n\n🏷️ WHITE-LABEL:")
    print("-" * 50)
    
    wl = WhiteLabelManager()
    wl.configure(WhiteLabelConfig(
        tenant_id=tenant.tenant_id,
        company_name="Coca-Cola Water Intelligence",
        logo_url="https://coca-cola.com/water-logo.svg",
        favicon_url="https://coca-cola.com/favicon.ico",
        primary_color="#FE001A",
        custom_domain="water.coca-cola.com"
    ))
    
    branding = wl.get_branding(tenant.tenant_id)
    print(f"Custom domain: {branding['custom_domain']}")
    print(f"Brand color: {branding['primary_color']}")
    print(f"White-labeled: {branding['is_white_label']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_waas()
