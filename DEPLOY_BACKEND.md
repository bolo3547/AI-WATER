# Deploy LWSC NRW Backend API

## Quick Deploy to Render.com (Free)

### Step 1: Create MongoDB Atlas Database (Free)

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Sign up/Login
3. Create a **FREE** cluster (M0 Sandbox)
4. Click "Connect" → "Drivers" → Copy the connection string
5. Replace `<password>` with your actual password

Example: `mongodb+srv://lwscadmin:YourPassword@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Step 2: Deploy to Render.com

1. Go to [Render.com](https://render.com)
2. Sign up with GitHub
3. Click **New** → **Web Service**
4. Connect your GitHub repo containing this project
5. Configure:
   - **Name**: `lwsc-nrw-api`
   - **Root Directory**: `nrw-detection-system`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements-api.txt`
   - **Start Command**: `gunicorn api_server:app --bind 0.0.0.0:$PORT --workers 2`

6. Add Environment Variables:
   - `USE_MONGODB` = `true`
   - `MONGODB_URI` = `your-mongodb-connection-string`
   - `SECRET_KEY` = `your-secret-key-here`

7. Click **Create Web Service**

### Step 3: Update Dashboard to Use Backend

After deployment, Render gives you a URL like: `https://lwsc-nrw-api.onrender.com`

Update your Vercel dashboard environment:
- `NEXT_PUBLIC_API_URL` = `https://lwsc-nrw-api.onrender.com`

---

## Alternative: Keep Current Setup

The dashboard already works with built-in Next.js API routes on Vercel.
The Python backend is optional for:
- Persistent data storage
- Integration with IoT sensors
- Advanced AI processing
