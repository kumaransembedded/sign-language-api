# # 🤟 IoT Sign Language Recognition System

**Real-time sign language recognition using ESP32-CAM + Cloud AI (YOLOv8)**

```
ESP32-CAM → HTTP POST → Cloud Server (YOLOv8) → JSON Response → ESP32 → LCD Display
```

---

## 📁 Project Structure

```
project_AG/
├── server/
│   ├── main.py              # FastAPI server with YOLOv8
│   ├── requirements.txt     # Python dependencies
│   ├── render.yaml          # Render deployment blueprint
│   └── best.pt              # ← YOUR trained YOLOv8 model (add this)
├── esp32/
│   └── sign_language_esp32.ino   # Arduino sketch
└── docs/
    └── README.md             # This file
```

---

## 🔌 Hardware Wiring

### Components Needed
| Component | Qty | Notes |
|-----------|-----|-------|
| ESP32-CAM (AI-Thinker) | 1 | With OV2640 camera |
| I2C LCD 16×2 | 1 | PCF8574 backpack (0x27 or 0x3F) |
| FTDI USB-to-Serial | 1 | For programming ESP32-CAM |
| Jumper wires | ~8 | Female-to-female |
| 5V power supply | 1 | USB or external |

### ESP32-CAM ↔ I2C LCD Wiring

```
ESP32-CAM          I2C LCD Module
─────────          ──────────────
GPIO 14  -------→  SDA
GPIO 15  -------→  SCL
5V       -------→  VCC
GND      -------→  GND
```

### ESP32-CAM ↔ FTDI Programmer (for flashing)

```
ESP32-CAM          FTDI Adapter
─────────          ────────────
U0R (GPIO 3) ---→  TX
U0T (GPIO 1) ---→  RX
GND          ---→  GND
5V           ---→  VCC (5V)
GPIO 0       ---→  GND  (only during upload, remove after)
```

> **Important:** Connect GPIO 0 to GND to enter flash mode. Remove the connection and press RST after uploading.

---

## ☁️ Cloud Server Deployment (Render)

### Option A: Deploy via Render Dashboard

1. Push your project to a **GitHub/GitLab** repository
2. Place your trained **`best.pt`** model inside the `server/` folder
3. Go to [render.com](https://render.com) → **New → Web Service**
4. Connect your repository
5. Configure:
   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `server` |
   | **Runtime** | Python |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
6. Click **Deploy** → wait for build to complete
7. Your API will be live at: `https://your-app-name.onrender.com`

### Option B: Deploy with render.yaml Blueprint

1. Ensure `render.yaml` is in the repo root (or `server/` folder)
2. Go to [render.com](https://render.com) → **Blueprints → New Blueprint Instance**
3. Connect your repo → Render auto-detects the config
4. Click **Apply** to deploy

### Test the deployment

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Prediction test
curl -X POST https://your-app-name.onrender.com/predict \
  -F "file=@test_image.jpg"
```

---

## 🔧 Local Server Testing

```bash
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Place your best.pt model in this directory

# Start server
python main.py
# → Server runs at http://localhost:8000

# Test health endpoint
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/predict \
  -F "file=@test_hand_image.jpg"
```

---

## 📱 ESP32 Arduino Setup

### 1. Install Arduino IDE
Download from [arduino.cc](https://www.arduino.cc/en/software)

### 2. Add ESP32 Board Support
1. Open **File → Preferences**
2. In **Additional Board Manager URLs**, add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Go to **Tools → Board → Board Manager**
4. Search **"esp32"** → Install **"esp32 by Espressif Systems"**

### 3. Install Required Libraries
Go to **Sketch → Include Library → Manage Libraries** and install:

| Library | Author | Version |
|---------|--------|---------|
| ArduinoJson | Benoit Blanchon | v7+ |
| LiquidCrystal I2C | Frank de Brabander | Latest |

### 4. Configure the Sketch
Open `esp32/sign_language_esp32.ino` and update these lines:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_SSID";      // ← Your WiFi name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // ← Your WiFi password
const char* SERVER_URL    = "https://YOUR-APP.onrender.com/predict";  // ← Your server URL
```

### 5. Upload to ESP32-CAM
1. Connect FTDI adapter (see wiring above)
2. **GPIO 0 → GND** to enter flash mode
3. **Tools → Board** → Select **"AI Thinker ESP32-CAM"**
4. **Tools → Port** → Select the correct COM port
5. Click **Upload**
6. After upload: disconnect GPIO 0 from GND, press **RST**

### 6. Monitor Output
**Tools → Serial Monitor** → Set baud rate to **115200**

---

## 🧪 Testing Checklist

### Server Tests

| # | Test | Command / Action | Expected Result |
|---|------|-----------------|-----------------|
| 1 | Health check | `GET /health` | `{"status": "ok", "model_loaded": true}` |
| 2 | Valid image | `POST /predict` with `.jpg` | `{"prediction": "A", "confidence": 0.95, ...}` |
| 3 | Invalid file | `POST /predict` with `.txt` | `400` error |
| 4 | No file | `POST /predict` (empty) | `422` error |
| 5 | CORS | Request from browser JS | Headers present |

### ESP32 Tests

| # | Test | Action | Expected Result |
|---|------|--------|-----------------|
| 1 | WiFi | Power on | LCD shows "WiFi OK" + IP |
| 2 | Camera | After WiFi | Serial shows "Camera initialised OK" |
| 3 | Capture | Wait for interval | Serial shows "Captured image: XXXX bytes" |
| 4 | Prediction | After capture | LCD shows "Sign:" + predicted letter |
| 5 | Retry | Disconnect server | Serial shows retry attempts |
| 6 | Reconnect | Disconnect WiFi | LCD shows "Reconnecting…" then reconnects |

### End-to-End Test

1. ✅ Deploy server to Render and verify `/health` returns OK
2. ✅ Flash ESP32-CAM with correct WiFi + server URL
3. ✅ Wire LCD to ESP32-CAM
4. ✅ Power on and observe Serial Monitor
5. ✅ Show a hand sign to the camera
6. ✅ Verify LCD displays the recognized letter with confidence

---

## 🏗️ System Architecture

```
┌─────────────┐    JPEG     ┌──────────────────┐    YOLOv8    ┌──────────┐
│  ESP32-CAM  │ ──────────→ │  Cloud Server    │ ───────────→ │  Model   │
│  (OV2640)   │   HTTP POST │  (FastAPI)       │   Inference  │ (best.pt)│
└──────┬──────┘             └────────┬─────────┘              └──────────┘
       │                             │
       │ I2C                         │ JSON Response
       ▼                             │ {"prediction":"A",
┌──────────────┐                     │  "confidence":0.95}
│  LCD 16×2    │ ←───────────────────┘
│  Sign: A     │
└──────────────┘
```

---

## ⚡ Performance Notes

- **Image size:** QVGA (320×240) JPEG ≈ 10–20 KB → fast upload
- **Target response time:** < 2 seconds end-to-end
- **Retry logic:** Up to 3 attempts with 1s delay between retries
- **Capture interval:** Configurable (default 3 seconds)
- **Free tier note:** Render free tier may cold-start (first request ~30s); subsequent requests are fast

---

## 📝 Notes

- **Model file:** You must provide your own `best.pt` YOLOv8 model trained on sign language gestures
- **LCD address:** Most I2C LCD modules use address `0x27`. If your LCD doesn't work, try `0x3F` — run an I2C scanner sketch to find the correct address
- **Power:** ESP32-CAM draws significant current during WiFi + camera use. Use a stable 5V supply (not just USB from laptop)
