#!/usr/bin/env python3
"""
LWSC NRW Detection System - Production API Server
=================================================
Complete backend API with in-memory storage (upgradeable to MongoDB).
Ready for deployment to Railway, Render, or any cloud platform.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
import uuid
import random

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins for API

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'lwsc-nrw-secret-2026')
PORT = int(os.environ.get('PORT', 8000))
USE_MONGODB = os.environ.get('USE_MONGODB', 'false').lower() == 'true'

# Try MongoDB if enabled
client = None
db = None
MONGODB_AVAILABLE = False

if USE_MONGODB:
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        from bson import ObjectId
        MONGODB_URI = os.environ.get('MONGODB_URI', '')
        MONGODB_DB = os.environ.get('MONGODB_DB', 'lwsc_nrw')
        if MONGODB_URI:
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            db = client[MONGODB_DB]
            MONGODB_AVAILABLE = True
            print(f"✅ Connected to MongoDB: {MONGODB_DB}")
    except Exception as e:
        print(f"⚠️ MongoDB not available, using in-memory storage: {e}")

def get_db():
    """Get database (returns None if using in-memory)"""
    return db if MONGODB_AVAILABLE else None

def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, '__str__'):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# In-memory token store (use Redis in production)
TOKENS = {}

# Default users (will be seeded to DB)
DEFAULT_USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "System Administrator",
        "email": "admin@lwsc.co.zm"
    },
    "operator": {
        "password": "operator123",
        "role": "operator",
        "name": "Control Room Operator",
        "email": "operator@lwsc.co.zm"
    },
    "technician": {
        "password": "technician123",
        "role": "technician",
        "name": "Field Technician",
        "email": "technician@lwsc.co.zm"
    }
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(username):
    token = secrets.token_hex(32)
    TOKENS[token] = {
        "username": username,
        "expires": datetime.now() + timedelta(hours=24)
    }
    return token

def verify_token(token):
    if token in TOKENS:
        if TOKENS[token]["expires"] > datetime.now():
            return TOKENS[token]["username"]
        del TOKENS[token]
    return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        username = verify_token(token)
        if not username:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

def seed_database():
    """Seed initial data to MongoDB including multi-tenancy support"""
    database = get_db()
    if database is None:
        print("⚠️ Running without database - using in-memory storage")
        return
    
    # =========================================================================
    # STEP 1: Seed default tenant for multi-tenancy
    # =========================================================================
    DEFAULT_TENANT_ID = 'default-tenant'
    
    tenants_col = database.tenants
    existing_tenant = tenants_col.find_one({"_id": DEFAULT_TENANT_ID})
    if not existing_tenant:
        tenants_col.insert_one({
            "_id": DEFAULT_TENANT_ID,
            "name": "LWSC Zambia (Default)",
            "country": "ZMB",
            "timezone": "Africa/Lusaka",
            "plan": "professional",
            "contact_email": "admin@lwsc.co.zm",
            "settings": {},
            "created_at": datetime.now().isoformat(),
            "is_active": True
        })
        print(f"  Created default tenant: {DEFAULT_TENANT_ID}")
    
    # =========================================================================
    # STEP 2: Seed users and link to default tenant
    # =========================================================================
    users_col = database.users
    tenant_users_col = database.tenant_users
    
    for username, data in DEFAULT_USERS.items():
        existing = users_col.find_one({"username": username})
        if not existing:
            user_id = str(uuid.uuid4())
            users_col.insert_one({
                "_id": user_id,
                "username": username,
                "password_hash": hash_password(data["password"]),
                "role": data["role"],
                "name": data["name"],
                "email": data["email"],
                "created_at": datetime.now().isoformat(),
                "status": "active"
            })
            print(f"  Created user: {username}")
            
            # Link user to default tenant
            tenant_users_col.insert_one({
                "tenant_id": DEFAULT_TENANT_ID,
                "user_id": user_id,
                "role": data["role"],
                "status": "active",
                "created_at": datetime.now().isoformat()
            })
            print(f"    Linked {username} to tenant: {DEFAULT_TENANT_ID}")
        else:
            # Ensure existing users are linked to tenant
            user_id = existing.get("_id")
            if user_id and not tenant_users_col.find_one({"tenant_id": DEFAULT_TENANT_ID, "user_id": user_id}):
                tenant_users_col.insert_one({
                    "tenant_id": DEFAULT_TENANT_ID,
                    "user_id": user_id,
                    "role": existing.get("role", "operator"),
                    "status": "active",
                    "created_at": datetime.now().isoformat()
                })
                print(f"    Linked existing user {username} to tenant: {DEFAULT_TENANT_ID}")
    
    # =========================================================================
    # STEP 3: Seed DMAs with tenant_id
    # =========================================================================
    dmas_col = database.dmas
    if dmas_col.count_documents({}) == 0:
        default_dmas = [
            {"dma_id": "dma-001", "name": "Kabulonga North", "nrw_percent": 28.5, "priority_score": 85, "status": "warning", "tenant_id": DEFAULT_TENANT_ID},
            {"dma_id": "dma-002", "name": "Woodlands Central", "nrw_percent": 35.2, "priority_score": 92, "status": "critical", "tenant_id": DEFAULT_TENANT_ID},
            {"dma_id": "dma-003", "name": "Roma Industrial", "nrw_percent": 22.1, "priority_score": 65, "status": "healthy", "tenant_id": DEFAULT_TENANT_ID},
            {"dma_id": "dma-004", "name": "Chelstone East", "nrw_percent": 31.8, "priority_score": 78, "status": "warning", "tenant_id": DEFAULT_TENANT_ID},
            {"dma_id": "dma-005", "name": "Matero South", "nrw_percent": 42.5, "priority_score": 95, "status": "critical", "tenant_id": DEFAULT_TENANT_ID},
            {"dma_id": "dma-006", "name": "Chilenje", "nrw_percent": 19.3, "priority_score": 45, "status": "healthy", "tenant_id": DEFAULT_TENANT_ID},
        ]
        dmas_col.insert_many(default_dmas)
        print("  Seeded DMAs with tenant_id")
    else:
        # Backfill existing DMAs with tenant_id
        result = dmas_col.update_many(
            {"tenant_id": {"$exists": False}},
            {"$set": {"tenant_id": DEFAULT_TENANT_ID}}
        )
        if result.modified_count > 0:
            print(f"  Backfilled {result.modified_count} DMAs with tenant_id")
    
    print("✅ Database seeded successfully with multi-tenancy support")

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        database = get_db()
        password_hash = hash_password(password)
        
        # Try database first
        if database:
            users_col = database.users
            user = users_col.find_one({"username": username, "password_hash": password_hash})
            if user:
                token = generate_token(username)
                users_col.update_one({"username": username}, {"$set": {"last_login": datetime.now().isoformat()}})
                return jsonify({
                    "success": True,
                    "access_token": token,
                    "user": {
                        "username": username,
                        "name": user.get("name", username),
                        "role": user.get("role", "operator"),
                        "email": user.get("email", "")
                    }
                })
        
        # Fallback to default users
        if username in DEFAULT_USERS and DEFAULT_USERS[username]["password"] == password:
            token = generate_token(username)
            return jsonify({
                "success": True,
                "access_token": token,
                "user": {
                    "username": username,
                    "name": DEFAULT_USERS[username]["name"],
                    "role": DEFAULT_USERS[username]["role"]
                }
            })
        
        return jsonify({"error": "Invalid credentials"}), 401
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in TOKENS:
        del TOKENS[token]
    return jsonify({"success": True})

# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    database = get_db()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "connected" if database else "disconnected",
        "services": {
            "api": "running",
            "database": "connected" if database else "disconnected",
            "ai_engine": "ready"
        }
    })

# ============================================================================
# SENSORS ENDPOINTS
# ============================================================================

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    database = get_db()
    
    if database:
        sensors_col = database.sensors
        sensors = list(sensors_col.find({}, {"_id": 0}))
        if sensors:
            return jsonify({"success": True, "sensors": sensors, "source": "database"})
    
    # Return simulated sensors if no database
    sensors = generate_simulated_sensors()
    return jsonify({"success": True, "sensors": sensors, "source": "simulated"})

@app.route('/api/sensors/<sensor_id>/readings', methods=['POST'])
def post_sensor_reading(sensor_id):
    """Receive sensor reading from ESP32"""
    database = get_db()
    if not database:
        return jsonify({"error": "Database not connected"}), 503
    
    data = request.get_json()
    reading = {
        "sensor_id": sensor_id,
        "timestamp": datetime.now().isoformat(),
        "flow_rate": data.get("flow_rate"),
        "pressure": data.get("pressure"),
        "temperature": data.get("temperature"),
        "battery": data.get("battery"),
        "signal": data.get("signal"),
        "dma_id": data.get("dma_id")
    }
    
    database.sensor_readings.insert_one(reading)
    
    # Update sensor last_seen
    database.sensors.update_one(
        {"sensor_id": sensor_id},
        {"$set": {"last_reading": datetime.now().isoformat(), "status": "online"}},
        upsert=True
    )
    
    return jsonify({"success": True, "reading_id": str(reading.get("_id", ""))})

# ============================================================================
# LEAKS ENDPOINTS
# ============================================================================

@app.route('/api/leaks', methods=['GET'])
def get_leaks():
    database = get_db()
    
    if database:
        leaks_col = database.leaks
        leaks = list(leaks_col.find({"status": {"$ne": "resolved"}}, {"_id": 0}).sort("detected_at", -1))
        return jsonify({"success": True, "data": leaks, "total": len(leaks), "source": "database"})
    
    return jsonify({"success": True, "data": [], "total": 0, "message": "No active leaks", "source": "fallback"})

@app.route('/api/leaks', methods=['POST'])
def create_leak():
    database = get_db()
    data = request.get_json()
    
    leak = {
        "id": f"LEAK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "location": data.get("location", "Unknown"),
        "dma_id": data.get("dma_id", ""),
        "estimated_loss": data.get("estimated_loss", 0),
        "priority": data.get("priority", "medium"),
        "confidence": data.get("confidence", 75),
        "detected_at": datetime.now().isoformat(),
        "status": "new",
        "source": data.get("source", "manual")
    }
    
    if database:
        database.leaks.insert_one(leak)
    
    return jsonify({"success": True, "data": leak})

@app.route('/api/leaks', methods=['PATCH'])
def update_leak():
    database = get_db()
    data = request.get_json()
    
    leak_id = data.get("id")
    action = data.get("action")
    user = data.get("user", "Operator")
    
    if not leak_id or not action:
        return jsonify({"error": "id and action required"}), 400
    
    update = {}
    if action == "acknowledge":
        update = {"status": "acknowledged", "acknowledged_by": user, "acknowledged_at": datetime.now().isoformat()}
    elif action == "dispatch":
        update = {"status": "dispatched", "dispatched_at": datetime.now().isoformat()}
    elif action == "resolve":
        update = {"status": "resolved", "resolved_at": datetime.now().isoformat(), "resolved_by": user}
    
    if database:
        result = database.leaks.find_one_and_update(
            {"id": leak_id},
            {"$set": update},
            return_document=True
        )
        if result:
            result.pop("_id", None)
            return jsonify({"success": True, "data": result})
    
    return jsonify({"success": False, "error": "Leak not found"}), 404

# ============================================================================
# WORK ORDERS ENDPOINTS
# ============================================================================

@app.route('/api/work-orders', methods=['GET'])
def get_work_orders():
    database = get_db()
    
    if database:
        orders = list(database.work_orders.find({}, {"_id": 0}).sort("created_at", -1))
        return jsonify({"success": True, "data": orders, "total": len(orders), "source": "database"})
    
    return jsonify({"success": True, "data": [], "total": 0, "source": "fallback"})

@app.route('/api/work-orders', methods=['POST'])
def create_work_order():
    database = get_db()
    data = request.get_json()
    
    order = {
        "id": f"WO-{datetime.now().strftime('%Y')}-{secrets.token_hex(4).upper()}",
        "title": data.get("title"),
        "dma": data.get("dma"),
        "priority": data.get("priority", "medium"),
        "status": "pending",
        "assignee": data.get("assignee", "Unassigned"),
        "created_at": datetime.now().isoformat(),
        "due_date": data.get("due_date", (datetime.now() + timedelta(days=3)).isoformat()),
        "estimated_loss": data.get("estimated_loss", 0),
        "source": data.get("source", "Manual Entry"),
        "description": data.get("description", ""),
        "created_by": data.get("created_by", "System")
    }
    
    if database:
        database.work_orders.insert_one(order)
    
    return jsonify({"success": True, "data": order})

# ============================================================================
# DMAS ENDPOINTS
# ============================================================================

@app.route('/api/dmas', methods=['GET'])
def get_dmas():
    database = get_db()
    
    if database:
        dmas = list(database.dmas.find({}, {"_id": 0}))
        if dmas:
            return jsonify({"success": True, "dmas": dmas, "source": "database"})
    
    # Fallback DMAs
    dmas = [
        {"dma_id": "dma-001", "name": "Kabulonga North", "nrw_percent": 28.5, "priority_score": 85, "status": "warning"},
        {"dma_id": "dma-002", "name": "Woodlands Central", "nrw_percent": 35.2, "priority_score": 92, "status": "critical"},
        {"dma_id": "dma-003", "name": "Roma Industrial", "nrw_percent": 22.1, "priority_score": 65, "status": "healthy"},
        {"dma_id": "dma-004", "name": "Chelstone East", "nrw_percent": 31.8, "priority_score": 78, "status": "warning"},
        {"dma_id": "dma-005", "name": "Matero South", "nrw_percent": 42.5, "priority_score": 95, "status": "critical"},
        {"dma_id": "dma-006", "name": "Chilenje", "nrw_percent": 19.3, "priority_score": 45, "status": "healthy"},
    ]
    return jsonify({"success": True, "dmas": dmas, "source": "fallback"})

# ============================================================================
# METRICS ENDPOINT
# ============================================================================

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    database = get_db()
    
    # Calculate metrics from database or use defaults
    metrics = {
        "total_nrw_percent": 32.5,
        "sensor_count": 12,
        "dma_count": 6,
        "active_high_priority_leaks": 0,
        "ai_confidence": 94,
        "last_data_received": datetime.now().isoformat()
    }
    
    if database:
        # Get actual counts
        metrics["sensor_count"] = database.sensors.count_documents({})
        metrics["dma_count"] = database.dmas.count_documents({})
        metrics["active_high_priority_leaks"] = database.leaks.count_documents({"priority": "high", "status": {"$ne": "resolved"}})
        
        # Calculate average NRW from DMAs
        dmas = list(database.dmas.find({}, {"nrw_percent": 1}))
        if dmas:
            metrics["total_nrw_percent"] = round(sum(d.get("nrw_percent", 0) for d in dmas) / len(dmas), 1)
    
    return jsonify({"success": True, "metrics": metrics})

# ============================================================================
# REALTIME ENDPOINT (for dashboard compatibility)
# ============================================================================

@app.route('/api/realtime', methods=['GET'])
def realtime():
    data_type = request.args.get('type', 'all')
    database = get_db()
    
    if data_type == 'metrics':
        return get_metrics()
    elif data_type == 'sensors':
        return get_sensors()
    elif data_type == 'dmas':
        return get_dmas()
    elif data_type == 'leaks':
        return get_leaks()
    else:
        return jsonify({
            "metrics": get_metrics().get_json().get("metrics"),
            "sensors": get_sensors().get_json().get("sensors"),
            "dmas": get_dmas().get_json().get("dmas")
        })

# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    database = get_db()
    
    if database:
        alerts = list(database.alerts.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
        return jsonify({"success": True, "data": alerts, "total": len(alerts)})
    
    return jsonify({"success": True, "data": [], "total": 0})

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    database = get_db()
    data = request.get_json()
    
    alert = {
        "id": f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": data.get("type", "system"),
        "severity": data.get("severity", "info"),
        "title": data.get("title", "System Alert"),
        "message": data.get("message", ""),
        "dma": data.get("dma"),
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    if database:
        database.alerts.insert_one(alert)
    
    return jsonify({"success": True, "data": alert})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_simulated_sensors():
    """Generate simulated sensor data"""
    now = datetime.now()
    hour = now.hour
    day_factor = 1.0 if 6 <= hour <= 22 else 0.4
    
    import random
    sensors = []
    sensor_configs = [
        ("ESP32-047", "Kabulonga North - Node A", "dma-001"),
        ("ESP32-048", "Kabulonga North - Node B", "dma-001"),
        ("ESP32-049", "Woodlands Central - Node A", "dma-002"),
        ("ESP32-050", "Woodlands Central - Node B", "dma-002"),
        ("ESP32-051", "Roma Industrial - Node A", "dma-003"),
        ("ESP32-052", "Roma Industrial - Node B", "dma-003"),
        ("ESP32-053", "Chelstone East - Node A", "dma-004"),
        ("ESP32-054", "Chelstone East - Node B", "dma-004"),
        ("ESP32-055", "Matero South - Node A", "dma-005"),
        ("ESP32-056", "Matero South - Node B", "dma-005"),
        ("ESP32-057", "Chilenje - Node A", "dma-006"),
        ("ESP32-058", "Chilenje - Node B", "dma-006"),
    ]
    
    for sensor_id, name, dma_id in sensor_configs:
        base_flow = 850 * day_factor
        sensors.append({
            "id": sensor_id,
            "name": name,
            "dma_id": dma_id,
            "status": "healthy" if random.random() > 0.1 else "warning",
            "battery": random.randint(60, 95),
            "signal": random.randint(70, 100),
            "flow_rate": round(base_flow + random.uniform(-100, 100), 1),
            "pressure": round(3.0 + random.uniform(-0.5, 0.5), 2),
            "last_reading": (now - timedelta(seconds=random.randint(30, 300))).isoformat()
        })
    
    return sensors

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  LWSC NRW Detection System - API Server")
    print("=" * 60)
    
    # Seed database
    seed_database()
    
    print(f"\n🚀 Starting server on port {PORT}")
    print(f"📊 API Documentation: http://localhost:{PORT}/api/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=PORT, debug=os.environ.get('DEBUG', 'false').lower() == 'true')
