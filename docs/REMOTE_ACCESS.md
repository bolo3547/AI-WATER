# AquaWatch NRW - Remote Access Setup Guide
# ==========================================

This guide explains how to control your NRW system from anywhere in the world.

## 🌍 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YOUR LOCATION (Anywhere)                          │
│                                                                             │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐        │
│   │  Laptop   │    │  Phone    │    │  Tablet   │    │  Desktop  │        │
│   │  Browser  │    │  App      │    │  Browser  │    │  Browser  │        │
│   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘        │
│         └────────────────┴────────────────┴────────────────┘              │
│                                    │                                       │
│                              INTERNET                                      │
└────────────────────────────────────┼───────────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        CLOUD SERVER (DigitalOcean/AWS)                     │
│                         aquawatch.example.com                              │
│                                                                            │
│    ┌─────────────────────────────────────────────────────────────────┐    │
│    │                      NGINX (SSL/HTTPS)                           │    │
│    │              api.aquawatch.com    app.aquawatch.com              │    │
│    └─────────────────────────┬───────────────────────────────────────┘    │
│                              │                                            │
│    ┌─────────────┬───────────┴───────────┬─────────────┐                  │
│    │             │                       │             │                  │
│    ▼             ▼                       ▼             ▼                  │
│  ┌─────┐     ┌───────┐              ┌─────────┐    ┌───────┐             │
│  │ API │     │ Dash  │              │TimescaleDB│   │ MQTT  │             │
│  │:8000│     │ :8050 │              │  :5432   │   │ :1883 │             │
│  └─────┘     └───────┘              └─────────┘    └───┬───┘             │
└────────────────────────────────────────────────────────┼────────────────────┘
                                                         │
                                                    INTERNET
                                                         │
┌────────────────────────────────────────────────────────┼────────────────────┐
│                            ZAMBIA (Field)              │                    │
│                                                        ▼                    │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐        │
│   │  ESP32    │    │  ESP32    │    │  ESP32    │    │  ESP32    │        │
│   │ Pressure  │    │  Flow     │    │  Level    │    │ Pressure  │        │
│   └───────────┘    └───────────┘    └───────────┘    └───────────┘        │
│                                                                            │
│                    Water Network Infrastructure                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Options

### Option 1: DigitalOcean (Recommended - $20/month)

1. **Create Droplet**
   ```bash
   # 2GB RAM, 1 vCPU, 50GB SSD
   # Region: London (lon1) - closest to Africa
   # Image: Ubuntu 22.04
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

3. **Clone and Deploy**
   ```bash
   git clone https://github.com/your-org/aquawatch-nrw.git
   cd aquawatch-nrw
   
   # Create .env file
   cat > .env << EOF
   DB_PASSWORD=your_secure_password_here
   SECRET_KEY=$(openssl rand -hex 32)
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=+1234567890
   SENDGRID_API_KEY=your_sendgrid_key
   EOF
   
   # Deploy
   docker-compose up -d
   ```

4. **Setup SSL with Let's Encrypt**
   ```bash
   docker-compose run --rm certbot certonly \
     --webroot \
     --webroot-path=/var/www/certbot \
     -d aquawatch.example.com \
     -d api.aquawatch.example.com \
     -d app.aquawatch.example.com
   ```

### Option 2: AWS (Enterprise)

Use AWS services for scalability:
- **EC2** or **ECS** for containers
- **RDS** for TimescaleDB
- **ElastiCache** for Redis
- **IoT Core** for MQTT
- **CloudFront** for CDN

### Option 3: Self-Hosted with Cloudflare Tunnel

For on-premise servers with remote access:

```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create aquawatch

# Configure
cat > ~/.cloudflared/config.yml << EOF
tunnel: aquawatch
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: api.aquawatch.example.com
    service: http://localhost:8000
  - hostname: app.aquawatch.example.com
    service: http://localhost:8050
  - service: http_status:404
EOF

# Run
cloudflared tunnel run aquawatch
```

## 📱 Mobile Access

### Access Dashboard from Phone

1. Open browser on your phone
2. Navigate to `https://app.aquawatch.example.com`
3. Login with your credentials
4. Add to Home Screen for app-like experience

### REST API for Custom Apps

```bash
# Login
curl -X POST https://api.aquawatch.example.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your_password"}'

# Get dashboard summary
curl https://api.aquawatch.example.com/v1/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get alerts
curl https://api.aquawatch.example.com/v1/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"

# Acknowledge alert remotely
curl -X POST https://api.aquawatch.example.com/v1/alerts/alert_001/acknowledge \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Crew dispatched from remote"}'
```

## 📬 Notification Setup

### SMS (Works Globally)

1. Create Twilio account: https://www.twilio.com
2. Get phone number with SMS capability
3. Add credentials to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxx
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### WhatsApp

1. Enable WhatsApp in Twilio Console
2. Register your WhatsApp Business number
3. Set in `.env`:
   ```
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

### Email (SendGrid)

1. Create SendGrid account: https://sendgrid.com
2. Create API key with Mail Send permission
3. Add to `.env`:
   ```
   SENDGRID_API_KEY=SG.xxxxxxxxxx
   EMAIL_FROM=alerts@aquawatch.example.com
   ```

### Telegram Bot

1. Create bot with @BotFather on Telegram
2. Get bot token
3. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

## 🔐 Security Best Practices

### 1. Strong Passwords
```bash
# Generate secure password
openssl rand -base64 32
```

### 2. Enable 2FA
Two-factor authentication available in user settings.

### 3. IP Whitelisting (Optional)
```nginx
# In nginx.conf
location /v1/ {
    allow 102.x.x.x;  # Your IP
    deny all;
    proxy_pass http://api;
}
```

### 4. VPN Access
For extra security, access via WireGuard VPN:
```bash
# Install WireGuard
apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey
```

### 5. Audit Logs
All API actions are logged with:
- User ID
- IP address
- Timestamp
- Action performed

## 🔧 ESP32 Configuration for Cloud

Update your ESP32 firmware:

```cpp
// In esp32_sensor_node.ino

// Point to your cloud MQTT broker
#define MQTT_BROKER     "mqtt.aquawatch.example.com"
#define MQTT_PORT       8883  // TLS
#define MQTT_USER       "esp32_device"
#define MQTT_PASSWORD   "your_api_key_here"

// Enable TLS
WiFiClientSecure wifiClient;
wifiClient.setCACert(root_ca);  // Add your CA certificate
```

## 📊 Monitoring Your System Remotely

### Dashboard URL
```
https://app.aquawatch.example.com
```

### API Documentation
```
https://api.aquawatch.example.com/docs
```

### Health Check
```bash
curl https://api.aquawatch.example.com/v1/health
```

### View Logs
```bash
# SSH to server
ssh root@your-server-ip

# View logs
docker-compose logs -f api
docker-compose logs -f dashboard
docker-compose logs -f mosquitto
```

## 🆘 Troubleshooting Remote Access

### Can't Connect?
1. Check server is running: `docker-compose ps`
2. Check firewall: `ufw status`
3. Check DNS: `nslookup api.aquawatch.example.com`
4. Check SSL: `openssl s_client -connect api.aquawatch.example.com:443`

### Slow Response?
1. Check server resources: `htop`
2. Check database: `docker-compose exec timescaledb pg_stat_activity`
3. Consider upgrading server or adding CDN

### Not Receiving Notifications?
1. Check credentials in `.env`
2. Check Twilio/SendGrid dashboards for errors
3. Test notification: 
   ```bash
   curl -X POST https://api.aquawatch.example.com/v1/notifications/test?channel=sms \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
