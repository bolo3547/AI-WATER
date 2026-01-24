"""
Seed script for Public Engagement demo data
Run: python -m src.public_engagement.seed_data
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Sample data pools
CATEGORIES = ['leak', 'burst', 'no_water', 'low_pressure', 'illegal_connection', 'overflow', 'contamination', 'other']
SOURCES = ['web', 'whatsapp', 'ussd', 'mobile_app', 'call_center']
STATUSES = ['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved', 'closed']
VERIFICATIONS = ['pending', 'confirmed', 'duplicate', 'false_report', 'needs_review']

# Lusaka areas with approximate coordinates
AREAS = [
    {'name': 'Central Business District', 'lat': -15.4167, 'lon': 28.2833},
    {'name': 'Kabulonga', 'lat': -15.4333, 'lon': 28.3167},
    {'name': 'Chilenje South', 'lat': -15.4500, 'lon': 28.2667},
    {'name': 'Matero', 'lat': -15.3833, 'lon': 28.2500},
    {'name': 'Garden Compound', 'lat': -15.4000, 'lon': 28.3000},
    {'name': 'Kamwala', 'lat': -15.4333, 'lon': 28.2833},
    {'name': 'Kalingalinga', 'lat': -15.4167, 'lon': 28.3333},
    {'name': 'Woodlands', 'lat': -15.4000, 'lon': 28.3333},
    {'name': 'Roma', 'lat': -15.3833, 'lon': 28.3167},
    {'name': 'Olympia Park', 'lat': -15.4167, 'lon': 28.3000},
    {'name': 'Chawama', 'lat': -15.4667, 'lon': 28.2667},
    {'name': 'Mandevu', 'lat': -15.4000, 'lon': 28.2167},
    {'name': 'Mtendere', 'lat': -15.4333, 'lon': 28.3500},
    {'name': 'Chelstone', 'lat': -15.3667, 'lon': 28.3667},
    {'name': 'Avondale', 'lat': -15.3833, 'lon': 28.2833},
]

DESCRIPTIONS = {
    'leak': [
        'Water leaking from underground pipe near the road',
        'Small leak from meter connection',
        'Steady drip from exposed pipe',
        'Water seeping through pavement',
        'Leak at pipe joint near house',
    ],
    'burst': [
        'Main burst, water gushing onto road',
        'Pipe burst at junction, flooding area',
        'Major burst near school',
        'Water spraying from broken pipe',
        'Burst pipe causing road damage',
    ],
    'no_water': [
        'No water supply since yesterday',
        'Water cut off suddenly this morning',
        'No water in taps for 3 days',
        'Entire street without water',
        'Water supply interrupted',
    ],
    'low_pressure': [
        'Very low water pressure, can barely fill bucket',
        'Pressure drops in evening hours',
        'Water trickles from tap',
        'Not enough pressure to reach upper floor',
        'Pressure much lower than normal',
    ],
    'illegal_connection': [
        'Suspicious connection to main pipe',
        'Neighbor tapping water illegally',
        'Unauthorized pipe connection spotted',
        'Possible water theft from meter',
        'Bypassed meter connection',
    ],
    'overflow': [
        'Tank overflowing onto street',
        'Reservoir overflow flooding area',
        'Water overflowing from manhole',
        'Storage tank constantly overflowing',
        'Pump station overflow',
    ],
    'contamination': [
        'Water has brown color',
        'Strange smell in tap water',
        'Water appears cloudy',
        'Possible contamination from sewage',
        'Unusual taste in water',
    ],
    'other': [
        'Water meter not working',
        'Need meter reading',
        'Billing inquiry',
        'Request for new connection',
        'General water supply question',
    ],
}

ZAMBIAN_NAMES = [
    'John Mwansa', 'Mary Banda', 'Peter Phiri', 'Grace Tembo', 'David Sakala',
    'Sarah Mulenga', 'James Zulu', 'Ruth Chomba', 'Joseph Mutale', 'Elizabeth Bwalya',
    'Michael Chanda', 'Joyce Mwila', 'Robert Lungu', 'Beatrice Ngoma', 'Emmanuel Mwape',
    'Veronica Simwanza', 'Patrick Siame', 'Agnes Chilufya', 'Kenneth Mulemba', 'Florence Kapata',
]


def generate_ticket() -> str:
    """Generate a random ticket number"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return 'TKT-' + ''.join(random.choice(chars) for _ in range(6))


def generate_phone() -> str:
    """Generate a random Zambian phone number"""
    prefixes = ['97', '96', '95', '77', '76', '75']
    return f"+260{random.choice(prefixes)}{random.randint(1000000, 9999999)}"


def generate_report(tenant_id: str, days_back: int = 90) -> dict:
    """Generate a single random report"""
    
    # Select random values
    category = random.choice(CATEGORIES)
    source = random.choice(SOURCES)
    area = random.choice(AREAS)
    
    # Time distribution - more recent reports more likely
    days_ago = int(random.expovariate(1/15))  # Exponential distribution, mean 15 days
    days_ago = min(days_ago, days_back)
    created_at = datetime.utcnow() - timedelta(
        days=days_ago,
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    # Status depends on age - older reports more likely resolved
    if days_ago > 30:
        status = random.choices(STATUSES, weights=[5, 10, 10, 15, 50, 10])[0]
    elif days_ago > 7:
        status = random.choices(STATUSES, weights=[10, 20, 20, 25, 20, 5])[0]
    else:
        status = random.choices(STATUSES, weights=[40, 30, 15, 10, 5, 0])[0]
    
    # Verification depends on status
    if status in ['resolved', 'closed']:
        verification = random.choices(VERIFICATIONS, weights=[5, 60, 15, 15, 5])[0]
    elif status == 'received':
        verification = 'pending'
    else:
        verification = random.choices(VERIFICATIONS, weights=[50, 20, 10, 10, 10])[0]
    
    # Add some location variance
    lat = area['lat'] + random.uniform(-0.005, 0.005)
    lon = area['lon'] + random.uniform(-0.005, 0.005)
    
    # Description
    description = random.choice(DESCRIPTIONS.get(category, DESCRIPTIONS['other']))
    
    # Reporter info (70% provide name, 80% provide phone)
    reporter_name = random.choice(ZAMBIAN_NAMES) if random.random() < 0.7 else None
    reporter_phone = generate_phone() if random.random() < 0.8 else None
    reporter_consent = random.random() < 0.6
    
    # Spam flag (2% of reports)
    spam_flag = random.random() < 0.02
    quarantine = spam_flag or (random.random() < 0.01)
    
    # Duplicate count (10% of reports have duplicates)
    duplicate_count = random.randint(1, 4) if random.random() < 0.1 else 0
    
    return {
        'id': str(uuid.uuid4()),
        'ticket': generate_ticket(),
        'tenant_id': tenant_id,
        'category': category,
        'description': description,
        'latitude': round(lat, 6),
        'longitude': round(lon, 6),
        'area_text': area['name'],
        'source': source,
        'reporter_name': reporter_name,
        'reporter_phone': reporter_phone,
        'reporter_email': None,
        'reporter_consent': reporter_consent,
        'status': status,
        'verification': verification,
        'trust_score_delta': 0,
        'spam_flag': spam_flag,
        'quarantine': quarantine,
        'master_report_id': None,
        'is_master': True,
        'duplicate_count': duplicate_count,
        'linked_leak_id': str(uuid.uuid4()) if random.random() < 0.15 else None,
        'linked_work_order_id': str(uuid.uuid4()) if status in ['in_progress', 'resolved'] and random.random() < 0.5 else None,
        'admin_notes': None,
        'assigned_to_user_id': str(uuid.uuid4()) if status not in ['received', 'closed'] else None,
        'assigned_team': f"Team {'Alpha' if random.random() < 0.5 else 'Beta'}" if status not in ['received', 'closed'] else None,
        'assigned_at': (created_at + timedelta(hours=random.randint(1, 24))).isoformat() if status not in ['received', 'closed'] else None,
        'resolved_at': (created_at + timedelta(days=random.randint(1, 7))).isoformat() if status in ['resolved', 'closed'] else None,
        'created_at': created_at.isoformat(),
        'updated_at': (created_at + timedelta(hours=random.randint(0, 48))).isoformat(),
    }


def generate_seed_data(tenant_id: str, count: int = 100) -> list:
    """Generate multiple seed reports"""
    reports = []
    tickets = set()
    
    for _ in range(count):
        report = generate_report(tenant_id)
        
        # Ensure unique tickets
        while report['ticket'] in tickets:
            report['ticket'] = generate_ticket()
        tickets.add(report['ticket'])
        
        reports.append(report)
    
    # Sort by created_at (newest first)
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    
    return reports


def seed_to_database(tenant_id: str, count: int = 100):
    """Seed reports directly to database"""
    try:
        from src.database import SessionLocal
        from src.public_engagement.models import PublicReport, ReportCategory, ReportStatus, ReportSource, ReportVerification
        
        db = SessionLocal()
        reports = generate_seed_data(tenant_id, count)
        
        for r in reports:
            report = PublicReport(
                id=uuid.UUID(r['id']),
                ticket=r['ticket'],
                tenant_id=tenant_id,
                category=ReportCategory(r['category']),
                description=r['description'],
                latitude=r['latitude'],
                longitude=r['longitude'],
                area_text=r['area_text'],
                source=ReportSource(r['source']),
                reporter_name=r['reporter_name'],
                reporter_phone=r['reporter_phone'],
                reporter_consent=r['reporter_consent'],
                status=ReportStatus(r['status']),
                verification=ReportVerification(r['verification']),
                spam_flag=r['spam_flag'],
                quarantine=r['quarantine'],
                duplicate_count=r['duplicate_count'],
                created_at=datetime.fromisoformat(r['created_at']),
                updated_at=datetime.fromisoformat(r['updated_at']),
            )
            db.add(report)
        
        db.commit()
        print(f"✅ Seeded {count} reports for tenant {tenant_id}")
        
    except ImportError as e:
        print(f"❌ Database module not available: {e}")
        print("Generating JSON seed file instead...")
        
        import json
        reports = generate_seed_data(tenant_id, count)
        filename = f"seed_data_{tenant_id}.json"
        with open(filename, 'w') as f:
            json.dump(reports, f, indent=2)
        print(f"✅ Saved {count} reports to {filename}")


if __name__ == '__main__':
    import sys
    
    tenant = sys.argv[1] if len(sys.argv) > 1 else 'lwsc-zambia'
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    print(f"Generating {count} seed reports for tenant: {tenant}")
    seed_to_database(tenant, count)
