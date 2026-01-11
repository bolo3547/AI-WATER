"""
AquaWatch Enterprise - Supply Chain Water Footprint
===================================================

"Know your water footprint across your entire supply chain."

Features:
1. Product water footprint calculation (ISO 14046)
2. Supply chain mapping & risk assessment
3. Supplier water disclosure management
4. Water offset/credit matching
5. Scope 3 water accounting
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# WATER FOOTPRINT TYPES
# =============================================================================

class WaterFootprintType(Enum):
    BLUE = "blue"       # Surface & groundwater consumed
    GREEN = "green"     # Rainwater consumed (agriculture)
    GREY = "grey"       # Water needed to dilute pollutants


@dataclass
class WaterFootprint:
    """Water footprint breakdown."""
    blue_m3: float = 0.0
    green_m3: float = 0.0
    grey_m3: float = 0.0
    
    @property
    def total_m3(self) -> float:
        return self.blue_m3 + self.green_m3 + self.grey_m3
    
    def to_dict(self) -> Dict:
        return {
            "blue_m3": self.blue_m3,
            "green_m3": self.green_m3,
            "grey_m3": self.grey_m3,
            "total_m3": self.total_m3
        }


# =============================================================================
# SUPPLY CHAIN MODELS
# =============================================================================

@dataclass
class Supplier:
    """Supply chain supplier."""
    supplier_id: str
    name: str
    country: str
    region: str
    
    # Products/materials supplied
    materials: List[str] = field(default_factory=list)
    
    # Water data
    water_footprint_per_unit: WaterFootprint = None
    water_stress_score: float = 0.5  # 0-1
    
    # Disclosure status
    disclosure_level: str = "none"  # none, partial, full
    disclosed_data: Dict = field(default_factory=dict)
    
    # Certification
    certifications: List[str] = field(default_factory=list)  # AWS, ISO 14046, etc.
    
    # Risk
    risk_score: float = 0.0


@dataclass
class Product:
    """Product with water footprint."""
    product_id: str
    name: str
    category: str
    
    # Bill of materials
    materials: List[Dict] = field(default_factory=list)  # {material, quantity, supplier_id}
    
    # Direct operations footprint
    direct_footprint: WaterFootprint = None
    
    # Calculated total footprint
    total_footprint: WaterFootprint = None
    
    # Benchmarks
    industry_average_m3: float = 0.0


# =============================================================================
# WATER FOOTPRINT CALCULATOR
# =============================================================================

# Industry average water footprints (m³ per unit)
MATERIAL_FOOTPRINTS = {
    # Agricultural
    "cotton_kg": WaterFootprint(blue=2120, green=4029, grey=620),
    "sugar_kg": WaterFootprint(blue=110, green=1520, grey=130),
    "coffee_kg": WaterFootprint(blue=130, green=15800, grey=200),
    "cocoa_kg": WaterFootprint(blue=50, green=19200, grey=300),
    "wheat_kg": WaterFootprint(blue=70, green=1300, grey=160),
    "rice_kg": WaterFootprint(blue=410, green=1300, grey=130),
    "beef_kg": WaterFootprint(blue=550, green=14400, grey=450),
    "chicken_kg": WaterFootprint(blue=310, green=3500, grey=380),
    "milk_L": WaterFootprint(blue=86, green=915, grey=72),
    
    # Industrial
    "aluminum_kg": WaterFootprint(blue=35, green=0, grey=50),
    "steel_kg": WaterFootprint(blue=20, green=0, grey=15),
    "plastic_kg": WaterFootprint(blue=10, green=0, grey=45),
    "paper_kg": WaterFootprint(blue=25, green=400, grey=75),
    "glass_kg": WaterFootprint(blue=5, green=0, grey=10),
    
    # Electronics
    "semiconductor_wafer": WaterFootprint(blue=8000, green=0, grey=2000),
    "pcb_m2": WaterFootprint(blue=200, green=0, grey=500),
    "battery_kwh": WaterFootprint(blue=50, green=0, grey=100),
}


class WaterFootprintCalculator:
    """
    Calculate product and corporate water footprints.
    
    "What's the true water cost of your iPhone? We can tell you."
    """
    
    def __init__(self):
        self.material_footprints = MATERIAL_FOOTPRINTS
        self.suppliers: Dict[str, Supplier] = {}
        self.products: Dict[str, Product] = {}
    
    def add_supplier(self, supplier: Supplier):
        """Register a supplier."""
        self.suppliers[supplier.supplier_id] = supplier
    
    def add_product(self, product: Product):
        """Register a product."""
        self.products[product.product_id] = product
    
    def calculate_product_footprint(self, product_id: str) -> Dict:
        """Calculate total water footprint for a product."""
        
        product = self.products.get(product_id)
        if not product:
            return {"error": "Product not found"}
        
        total_blue = 0.0
        total_green = 0.0
        total_grey = 0.0
        
        material_breakdown = []
        supplier_breakdown = {}
        
        for material in product.materials:
            mat_name = material["material"]
            quantity = material["quantity"]
            supplier_id = material.get("supplier_id")
            
            # Get footprint from supplier if available, otherwise use default
            if supplier_id and supplier_id in self.suppliers:
                supplier = self.suppliers[supplier_id]
                if supplier.water_footprint_per_unit:
                    footprint = supplier.water_footprint_per_unit
                else:
                    footprint = self.material_footprints.get(mat_name, WaterFootprint())
                
                # Track by supplier
                if supplier_id not in supplier_breakdown:
                    supplier_breakdown[supplier_id] = {
                        "name": supplier.name,
                        "country": supplier.country,
                        "water_stress": supplier.water_stress_score,
                        "footprint_m3": 0
                    }
                supplier_breakdown[supplier_id]["footprint_m3"] += footprint.total_m3 * quantity
            else:
                footprint = self.material_footprints.get(mat_name, WaterFootprint())
            
            mat_blue = footprint.blue_m3 * quantity
            mat_green = footprint.green_m3 * quantity
            mat_grey = footprint.grey_m3 * quantity
            
            total_blue += mat_blue
            total_green += mat_green
            total_grey += mat_grey
            
            material_breakdown.append({
                "material": mat_name,
                "quantity": quantity,
                "blue_m3": mat_blue,
                "green_m3": mat_green,
                "grey_m3": mat_grey,
                "total_m3": mat_blue + mat_green + mat_grey,
                "pct_of_total": 0  # Calculated below
            })
        
        # Add direct operations
        if product.direct_footprint:
            total_blue += product.direct_footprint.blue_m3
            total_green += product.direct_footprint.green_m3
            total_grey += product.direct_footprint.grey_m3
        
        total = total_blue + total_green + total_grey
        
        # Calculate percentages
        for mat in material_breakdown:
            mat["pct_of_total"] = (mat["total_m3"] / total * 100) if total > 0 else 0
        
        # Update product
        product.total_footprint = WaterFootprint(total_blue, total_green, total_grey)
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "total_footprint": {
                "blue_m3": round(total_blue, 2),
                "green_m3": round(total_green, 2),
                "grey_m3": round(total_grey, 2),
                "total_m3": round(total, 2)
            },
            "footprint_breakdown": {
                "blue_pct": round(total_blue / total * 100, 1) if total > 0 else 0,
                "green_pct": round(total_green / total * 100, 1) if total > 0 else 0,
                "grey_pct": round(total_grey / total * 100, 1) if total > 0 else 0
            },
            "material_breakdown": sorted(material_breakdown, key=lambda x: x["total_m3"], reverse=True),
            "supplier_breakdown": list(supplier_breakdown.values()),
            "benchmark": {
                "industry_average_m3": product.industry_average_m3,
                "vs_average_pct": ((total - product.industry_average_m3) / product.industry_average_m3 * 100) if product.industry_average_m3 > 0 else 0
            },
            "hotspots": self._identify_hotspots(material_breakdown, supplier_breakdown)
        }
    
    def _identify_hotspots(self, 
                           material_breakdown: List[Dict],
                           supplier_breakdown: Dict) -> List[Dict]:
        """Identify water footprint hotspots."""
        hotspots = []
        
        # Top 3 materials by footprint
        top_materials = sorted(material_breakdown, key=lambda x: x["total_m3"], reverse=True)[:3]
        for mat in top_materials:
            if mat["pct_of_total"] > 10:
                hotspots.append({
                    "type": "material",
                    "item": mat["material"],
                    "contribution_pct": mat["pct_of_total"],
                    "recommendation": f"Consider alternative to {mat['material']} or improve supplier efficiency"
                })
        
        # High water stress suppliers
        for supplier in supplier_breakdown.values():
            if supplier["water_stress"] > 0.6:
                hotspots.append({
                    "type": "supplier_risk",
                    "item": supplier["name"],
                    "water_stress": supplier["water_stress"],
                    "recommendation": f"Engage {supplier['name']} on water efficiency or diversify sourcing"
                })
        
        return hotspots


# =============================================================================
# SUPPLIER DISCLOSURE MANAGEMENT
# =============================================================================

class SupplierDisclosureManager:
    """
    Manage supplier water data disclosure.
    
    "What gets measured gets managed."
    """
    
    def __init__(self):
        self.disclosure_requests: List[Dict] = []
        self.disclosure_responses: Dict[str, Dict] = {}
    
    def send_disclosure_request(self, 
                                supplier_id: str,
                                supplier_name: str,
                                supplier_email: str,
                                questions: List[str] = None) -> Dict:
        """Send water disclosure request to supplier."""
        
        default_questions = [
            "Total water withdrawal (m³/year)",
            "Total water discharge (m³/year)",
            "Water sources (municipal, groundwater, surface, etc.)",
            "Operations in water-stressed areas (Yes/No)",
            "Water recycling rate (%)",
            "Water-related targets and progress",
            "Third-party water certifications"
        ]
        
        request = {
            "request_id": f"REQ_{len(self.disclosure_requests)+1:05d}",
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "supplier_email": supplier_email,
            "questions": questions or default_questions,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "deadline": "30 days",
            "status": "sent"
        }
        
        self.disclosure_requests.append(request)
        
        return {
            "success": True,
            "request_id": request["request_id"],
            "message": f"Disclosure request sent to {supplier_name}"
        }
    
    def process_response(self, 
                        request_id: str,
                        supplier_id: str,
                        response_data: Dict) -> Dict:
        """Process supplier disclosure response."""
        
        self.disclosure_responses[supplier_id] = {
            "request_id": request_id,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "data": response_data,
            "completeness_score": self._calculate_completeness(response_data),
            "verified": False
        }
        
        return {
            "success": True,
            "completeness_score": self.disclosure_responses[supplier_id]["completeness_score"],
            "next_steps": "Data will be verified and integrated into footprint calculations"
        }
    
    def _calculate_completeness(self, data: Dict) -> float:
        """Calculate how complete the disclosure is."""
        expected_fields = [
            "total_withdrawal", "total_discharge", "water_sources",
            "water_stressed_operations", "recycling_rate", "targets"
        ]
        
        provided = sum(1 for field in expected_fields if field in data and data[field])
        return (provided / len(expected_fields)) * 100
    
    def get_disclosure_dashboard(self) -> Dict:
        """Get overview of supplier disclosure status."""
        
        total_requests = len(self.disclosure_requests)
        responses = len(self.disclosure_responses)
        
        return {
            "total_suppliers_requested": total_requests,
            "responses_received": responses,
            "response_rate_pct": (responses / total_requests * 100) if total_requests > 0 else 0,
            "average_completeness": sum(r["completeness_score"] for r in self.disclosure_responses.values()) / responses if responses > 0 else 0,
            "pending_requests": [r for r in self.disclosure_requests if r["supplier_id"] not in self.disclosure_responses]
        }


# =============================================================================
# WATER OFFSET MARKETPLACE
# =============================================================================

@dataclass
class WaterOffset:
    """Water offset/credit."""
    offset_id: str
    project_type: str  # restoration, efficiency, conservation
    location: str
    volume_m3: float
    price_per_m3: float
    vintage_year: int
    certification: str  # AWS, Gold Standard, etc.
    available: bool = True


class WaterOffsetMarketplace:
    """
    Connect companies with water offset projects.
    
    "Can't reduce? Offset responsibly."
    """
    
    def __init__(self):
        self.offsets: Dict[str, WaterOffset] = {}
        self.purchases: List[Dict] = []
        
        # Load sample offsets
        self._load_sample_offsets()
    
    def _load_sample_offsets(self):
        """Load sample offset projects."""
        sample_offsets = [
            WaterOffset("OFF_001", "watershed_restoration", "Kafue Basin, Zambia", 
                       500000, 0.05, 2024, "Alliance for Water Stewardship"),
            WaterOffset("OFF_002", "agricultural_efficiency", "Orange River Basin, South Africa",
                       1000000, 0.03, 2024, "Gold Standard"),
            WaterOffset("OFF_003", "wetland_conservation", "Okavango Delta, Botswana",
                       750000, 0.08, 2024, "Ramsar Certified"),
            WaterOffset("OFF_004", "industrial_efficiency", "Gujarat, India",
                       2000000, 0.02, 2024, "ISO 14046"),
            WaterOffset("OFF_005", "urban_leak_reduction", "Cape Town, South Africa",
                       300000, 0.04, 2024, "AquaWatch Verified"),
        ]
        
        for offset in sample_offsets:
            self.offsets[offset.offset_id] = offset
    
    def search_offsets(self,
                      location: str = None,
                      project_type: str = None,
                      min_volume: float = 0,
                      max_price: float = float('inf')) -> List[Dict]:
        """Search available offsets."""
        
        results = []
        for offset in self.offsets.values():
            if not offset.available:
                continue
            if location and location.lower() not in offset.location.lower():
                continue
            if project_type and offset.project_type != project_type:
                continue
            if offset.volume_m3 < min_volume:
                continue
            if offset.price_per_m3 > max_price:
                continue
            
            results.append({
                "offset_id": offset.offset_id,
                "project_type": offset.project_type,
                "location": offset.location,
                "volume_m3": offset.volume_m3,
                "price_per_m3": offset.price_per_m3,
                "total_price_usd": offset.volume_m3 * offset.price_per_m3,
                "vintage": offset.vintage_year,
                "certification": offset.certification
            })
        
        return sorted(results, key=lambda x: x["price_per_m3"])
    
    def purchase_offset(self, 
                       offset_id: str,
                       buyer_id: str,
                       volume_m3: float) -> Dict:
        """Purchase water offsets."""
        
        offset = self.offsets.get(offset_id)
        if not offset:
            return {"error": "Offset not found"}
        if not offset.available:
            return {"error": "Offset no longer available"}
        if volume_m3 > offset.volume_m3:
            return {"error": "Requested volume exceeds available"}
        
        total_cost = volume_m3 * offset.price_per_m3
        
        purchase = {
            "purchase_id": f"PUR_{len(self.purchases)+1:06d}",
            "offset_id": offset_id,
            "buyer_id": buyer_id,
            "volume_m3": volume_m3,
            "total_cost_usd": total_cost,
            "purchased_at": datetime.now(timezone.utc).isoformat(),
            "certificate_url": f"https://aquawatch.com/certificates/PUR_{len(self.purchases)+1:06d}.pdf"
        }
        
        self.purchases.append(purchase)
        
        # Update available volume
        offset.volume_m3 -= volume_m3
        if offset.volume_m3 <= 0:
            offset.available = False
        
        return {
            "success": True,
            "purchase_id": purchase["purchase_id"],
            "volume_m3": volume_m3,
            "total_cost_usd": total_cost,
            "certificate_url": purchase["certificate_url"],
            "message": f"Successfully purchased {volume_m3:,.0f} m³ of water offsets from {offset.location}"
        }
    
    def calculate_offset_need(self,
                             current_footprint_m3: float,
                             target_footprint_m3: float,
                             reduction_timeline_years: int = 5) -> Dict:
        """Calculate offset needs for a company."""
        
        gap = current_footprint_m3 - target_footprint_m3
        
        if gap <= 0:
            return {
                "offset_needed": False,
                "message": "You're already at or below your target!"
            }
        
        # Assume 60% can be reduced, 40% needs offsetting
        realistic_reduction = gap * 0.6
        offset_needed = gap * 0.4
        
        # Find best offsets
        available_offsets = self.search_offsets(min_volume=offset_needed * 0.1)
        
        # Calculate cost range
        if available_offsets:
            min_cost = min(o["price_per_m3"] for o in available_offsets) * offset_needed
            max_cost = max(o["price_per_m3"] for o in available_offsets) * offset_needed
        else:
            min_cost = max_cost = 0
        
        return {
            "current_footprint_m3": current_footprint_m3,
            "target_footprint_m3": target_footprint_m3,
            "gap_m3": gap,
            "recommended_strategy": {
                "internal_reduction_m3": realistic_reduction,
                "offset_needed_m3": offset_needed,
                "timeline_years": reduction_timeline_years
            },
            "offset_cost_estimate": {
                "min_usd": min_cost,
                "max_usd": max_cost,
                "average_usd": (min_cost + max_cost) / 2
            },
            "available_projects": len(available_offsets),
            "recommended_projects": available_offsets[:3]
        }


# =============================================================================
# DEMO
# =============================================================================

def demo_supply_chain():
    """Demo supply chain water footprint."""
    
    print("=" * 70)
    print("🌍 AQUAWATCH ENTERPRISE - SUPPLY CHAIN WATER FOOTPRINT")
    print("=" * 70)
    
    # Initialize calculator
    calc = WaterFootprintCalculator()
    
    # Add suppliers
    calc.add_supplier(Supplier(
        supplier_id="SUP_001",
        name="Brazilian Sugar Co",
        country="Brazil",
        region="São Paulo",
        materials=["sugar_kg"],
        water_stress_score=0.3,
        disclosure_level="full"
    ))
    
    calc.add_supplier(Supplier(
        supplier_id="SUP_002",
        name="Indian Aluminum Ltd",
        country="India",
        region="Gujarat",
        materials=["aluminum_kg"],
        water_stress_score=0.8,
        disclosure_level="partial"
    ))
    
    # Add product
    calc.add_product(Product(
        product_id="PROD_001",
        name="Energy Drink Can",
        category="Beverage",
        materials=[
            {"material": "sugar_kg", "quantity": 0.05, "supplier_id": "SUP_001"},
            {"material": "aluminum_kg", "quantity": 0.015, "supplier_id": "SUP_002"},
            {"material": "coffee_kg", "quantity": 0.002}
        ],
        direct_footprint=WaterFootprint(blue=0.5, green=0, grey=0.2),
        industry_average_m3=150
    ))
    
    # Calculate footprint
    print("\n📦 PRODUCT WATER FOOTPRINT:")
    print("-" * 50)
    
    footprint = calc.calculate_product_footprint("PROD_001")
    
    print(f"Product: {footprint['product_name']}")
    print(f"\nTotal Footprint: {footprint['total_footprint']['total_m3']:.2f} m³/unit")
    print(f"  Blue Water: {footprint['total_footprint']['blue_m3']:.2f} m³ ({footprint['footprint_breakdown']['blue_pct']}%)")
    print(f"  Green Water: {footprint['total_footprint']['green_m3']:.2f} m³ ({footprint['footprint_breakdown']['green_pct']}%)")
    print(f"  Grey Water: {footprint['total_footprint']['grey_m3']:.2f} m³ ({footprint['footprint_breakdown']['grey_pct']}%)")
    
    print(f"\n📊 Material Breakdown:")
    for mat in footprint['material_breakdown'][:5]:
        print(f"  {mat['material']}: {mat['total_m3']:.2f} m³ ({mat['pct_of_total']:.1f}%)")
    
    print(f"\n⚠️ Hotspots Identified:")
    for hotspot in footprint['hotspots']:
        print(f"  • {hotspot['type']}: {hotspot['item']}")
        print(f"    {hotspot['recommendation']}")
    
    # Offset marketplace
    print("\n\n💧 WATER OFFSET MARKETPLACE:")
    print("-" * 50)
    
    marketplace = WaterOffsetMarketplace()
    
    # Search offsets
    offsets = marketplace.search_offsets(location="Africa")
    print("Available offsets in Africa:")
    for o in offsets:
        print(f"  • {o['project_type']} - {o['location']}")
        print(f"    Volume: {o['volume_m3']:,} m³ @ ${o['price_per_m3']}/m³")
    
    # Calculate offset need
    print(f"\n📈 OFFSET RECOMMENDATION:")
    need = marketplace.calculate_offset_need(
        current_footprint_m3=5000000,
        target_footprint_m3=3000000,
        reduction_timeline_years=5
    )
    
    print(f"Current Footprint: {need['current_footprint_m3']:,} m³/year")
    print(f"Target Footprint: {need['target_footprint_m3']:,} m³/year")
    print(f"Gap: {need['gap_m3']:,} m³")
    print(f"\nRecommended Strategy:")
    print(f"  Internal Reduction: {need['recommended_strategy']['internal_reduction_m3']:,.0f} m³")
    print(f"  Offset Purchase: {need['recommended_strategy']['offset_needed_m3']:,.0f} m³")
    print(f"\nEstimated Offset Cost: ${need['offset_cost_estimate']['average_usd']:,.0f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_supply_chain()
