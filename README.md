# ☁️ Rudra's Weather App — v2 Advanced

Full-stack weather intelligence app with Flask + FastAPI + MySQL (XAMPP).

---

## 🆕 What's New in v2

| Phase | Feature | Status |
|---|---|---|
| Phase 1 | 7-Day Forecast | ✅ |
| Phase 1 | 24-Hour Hourly Chart (Chart.js) | ✅ |
| Phase 1 | Search History (quick-access chips) | ✅ |
| Phase 2 | Weather Alert Banners (storm/heat/freeze/wind/UV) | ✅ |
| Phase 2 | Activity Recommender | ✅ |
| Phase 2 | Dynamic Animated Backgrounds (per weather type) | ✅ |
| Phase 2 | Particle Engine (rain/snow/lightning/fog/sun/cloud) | ✅ |
| DB | MySQL Cache (10-min TTL via XAMPP) | ✅ |
| DB | Search History saved to DB | ✅ |
| DB | Pin Cities (save/remove) | ✅ |
| DB | Weather Alerts Log | ✅ |

---

## 🗄️ XAMPP Database Setup (Do This First!)

1. Open **XAMPP Control Panel** → Start **Apache** + **MySQL**
2. Open browser → go to `http://localhost/phpmyadmin`
3. Click **SQL** tab at the top
4. Copy-paste the entire contents of `database.sql`
5. Click **Go** — database and tables are created!

---

## 🚀 Run the App (Windows)

### Option A — Double-click (easiest)
```
Double-click START.bat
```
Two terminal windows open automatically + browser launches.

### Option B — Manual (two PowerShell windows)

**Window 1 — FastAPI:**
```powershell
cd "C:\path\to\rudras-app-v2"
uvicorn fastapi_weather:app --host 0.0.0.0 --port 8001 --reload
```

**Window 2 — Flask:**
```powershell
cd "C:\path\to\rudras-app-v2"
python flask_app.py
```

Then open: **http://localhost:5000**

---

## 📁 Project Structure

```
rudras-app-v2/
├── fastapi_weather.py    ← FastAPI backend (weather + DB logic)
├── flask_app.py          ← Flask frontend server + API proxy
├── templates/
│   └── index.html        ← Full UI (particles, charts, forecast)
├── database.sql          ← Run this in phpMyAdmin first!
├── requirements.txt
├── START.bat             ← Windows one-click launcher
└── README.md
```

---

## 🗄️ Database Tables

| Table | Purpose |
|---|---|
| `weather_cache` | Stores weather results for 10 min (avoids repeat API calls) |
| `search_history` | Every city searched is logged here |
| `pinned_cities` | Cities user has pinned (saved favourites) |
| `weather_alerts` | Log of every alert triggered (storm, heat, freeze etc.) |

---

## 🌐 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /weather` | Live weather + forecast + safety + alerts |
| `GET /geocode` | City search → coordinates |
| `GET /history` | Last 5 unique searches from DB |
| `GET /pinned` | All pinned cities from DB |
| `POST /pinned` | Pin a city |
| `DELETE /pinned` | Unpin a city |
| `GET /alerts/recent` | Recent alert log from DB |
| `GET /health` | Health check (shows DB status) |
| `GET /docs` | Swagger interactive API docs |

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---|---|
| `TemplateNotFound: index.html` | Make sure `index.html` is inside `templates/` folder |
| DB not connecting | Start MySQL in XAMPP first, run `database.sql` in phpMyAdmin |
| Port in use | Run `START.bat` — it auto-kills old processes |
| `ModuleNotFoundError: pymysql` | Run `pip install pymysql` |
| Weather not loading | Check internet — Open-Meteo needs connection |

---

## 📦 Install Dependencies

```powershell
pip install -r requirements.txt
```

---

Made with ❤️ by **Rudra** · Open-Meteo API · Chart.js · MySQL/XAMPP
