"""
FastAPI Weather Microservice v2
- Live weather + 7-day forecast + 24-hour hourly
- Weather alerts engine
- Activity recommender
- Dynamic background theme
- MySQL (XAMPP) caching via pymysql
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import httpx
import pymysql
import pymysql.cursors
import json
import os
from datetime import datetime, timedelta

app = FastAPI(title="Rudra's Weather API v2", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MySQL Config (XAMPP locally, managed MySQL in production) ─
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),        # XAMPP default = no password
    "database": os.getenv("DB_NAME", "rudras_weather"),
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

# Managed MySQL hosts (e.g. Aiven) require SSL. Set DB_SSL=true to enable.
if os.getenv("DB_SSL", "false").lower() == "true":
    DB_CONFIG["ssl"] = {"ca": os.getenv("DB_SSL_CA")} if os.getenv("DB_SSL_CA") else {"ssl": {}}

def get_db():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return None

CACHE_TTL_MINUTES = 10

# ── WMO Weather Codes ────────────────────────────────────────
WMO_CODES = {
    0: ("Clear Sky", "sunny"),         1: ("Mainly Clear", "sunny"),
    2: ("Partly Cloudy", "cloudy"),    3: ("Overcast", "cloudy"),
    45: ("Foggy", "fog"),              48: ("Icy Fog", "fog"),
    51: ("Light Drizzle", "rain"),     53: ("Moderate Drizzle", "rain"),
    55: ("Dense Drizzle", "rain"),     61: ("Slight Rain", "rain"),
    63: ("Moderate Rain", "rain"),     65: ("Heavy Rain", "rain"),
    71: ("Slight Snow", "snow"),       73: ("Moderate Snow", "snow"),
    75: ("Heavy Snow", "snow"),        77: ("Snow Grains", "snow"),
    80: ("Rain Showers", "rain"),      81: ("Moderate Showers", "rain"),
    82: ("Violent Showers", "storm"),  85: ("Snow Showers", "snow"),
    86: ("Heavy Snow Showers", "snow"),95: ("Thunderstorm", "storm"),
    96: ("Storm + Hail", "storm"),     99: ("Storm + Heavy Hail", "storm"),
}

WMO_ICONS = {
    "sunny": "☀️", "cloudy": "⛅", "rain": "🌧️",
    "storm": "⛈️", "snow": "❄️", "fog": "🌫️",
}

# ── Safety Data ──────────────────────────────────────────────
SAFETY_DATA = {
    "sunny":  {"level": "low",      "precautions": ["Apply SPF 30+ sunscreen every 2 hours","Wear UV-protective sunglasses and a wide-brim hat","Stay hydrated — drink at least 8–10 glasses of water","Avoid direct sun exposure between 11 AM and 3 PM","Wear lightweight, light-colored, breathable clothing"]},
    "cloudy": {"level": "low",      "precautions": ["UV rays still penetrate clouds — consider sunscreen","Carry a light jacket as temperatures may drop","Good visibility — safe for outdoor activities","Watch for sudden weather changes"]},
    "rain":   {"level": "moderate", "precautions": ["Carry a waterproof umbrella or rain jacket","Wear waterproof footwear to avoid slipping","Drive cautiously — roads may be wet and slippery","Avoid open areas during heavy rain","Check for local flood warnings before travel","Keep electronics in waterproof bags"]},
    "storm":  {"level": "high",     "precautions": ["🚨 STAY INDOORS — severe weather in effect","Unplug electrical appliances to prevent surge damage","Keep away from windows and open doors","Never shelter under isolated trees or in open fields","Prepare emergency kit: flashlight, water, first aid","Monitor official weather alerts and evacuation orders","If driving, pull over safely and wait for storm to pass"]},
    "snow":   {"level": "high",     "precautions": ["Dress in thermal layers — inner moisture-wicking, outer windproof","Wear insulated, waterproof boots with good grip","Drive slowly — increase following distance on icy roads","Clear snow from vehicle roof and windows before driving","Watch for black ice on roads and walkways","Protect pipes from freezing — let faucets drip slightly"]},
    "fog":    {"level": "moderate", "precautions": ["Use low-beam headlights and fog lights while driving","Reduce speed and increase following distance significantly","Avoid overtaking in low visibility conditions","Use hazard lights if visibility drops below 100m","Pedestrians should wear reflective clothing"]},
}

# ── Activity Recommender ─────────────────────────────────────
ACTIVITIES = {
    "sunny":  {"emoji": "🏃", "title": "Perfect for Outdoors!", "suggestions": ["Morning jog or cycling","Picnic in the park","Outdoor sports & games","Photography walk","Gardening"]},
    "cloudy": {"emoji": "🚶", "title": "Good for Light Activities", "suggestions": ["Comfortable walking weather","Sightseeing & tourism","Outdoor markets","Light hiking","Photography (great diffused light!)"]},
    "rain":   {"emoji": "☕", "title": "Indoor Day Recommended", "suggestions": ["Visit a museum or gallery","Cozy café with a book","Movie marathon at home","Cook a new recipe","Board games with family"]},
    "storm":  {"emoji": "🏠", "title": "Stay Safe Indoors", "suggestions": ["Work from home if possible","Read or learn something new","Online gaming or streaming","Home workout","Call and check on loved ones"]},
    "snow":   {"emoji": "⛷️", "title": "Winter Wonderland", "suggestions": ["Snowball fights & snowman building","Skiing or sledding (if nearby)","Hot chocolate & cozy reading","Indoor cooking & baking","Winter photography"]},
    "fog":    {"emoji": "🌫️", "title": "Low Visibility — Be Careful", "suggestions": ["Delay non-essential travel","Indoor exercise or yoga","Work from home if possible","Fog photography (stunning results!)","Home projects"]},
}

# ── Alert Thresholds ─────────────────────────────────────────
def get_alerts(condition_type: str, temp_c: float, wind_kmh: float, uv: float) -> list:
    alerts = []
    if condition_type == "storm":
        alerts.append({"type": "storm", "icon": "⛈️", "color": "red", "msg": "SEVERE STORM WARNING — Seek shelter immediately!"})
    if temp_c >= 42:
        alerts.append({"type": "extreme_heat", "icon": "🔴", "color": "red", "msg": f"EXTREME HEAT ALERT — {temp_c}°C is dangerously hot!"})
    elif temp_c >= 37:
        alerts.append({"type": "heat", "icon": "🟠", "color": "orange", "msg": f"HEAT ADVISORY — Stay hydrated, limit outdoor exposure"})
    if temp_c <= 0:
        alerts.append({"type": "freeze", "icon": "🔵", "color": "blue", "msg": f"FREEZE WARNING — {temp_c}°C — Risk of frostbite on exposed skin"})
    if wind_kmh >= 60:
        alerts.append({"type": "wind", "icon": "💨", "color": "orange", "msg": f"HIGH WIND WARNING — {wind_kmh} km/h gusts expected"})
    if uv and uv >= 8:
        alerts.append({"type": "uv", "icon": "☀️", "color": "orange", "msg": f"HIGH UV INDEX ({uv}) — Sun protection essential"})
    return alerts

def get_temp_precautions(temp_c: float) -> list:
    if temp_c >= 40:
        return ["🔴 EXTREME HEAT — Minimize all outdoor activity","Drink water every 15–20 minutes","Watch for heat stroke: confusion, no sweating, hot skin","Never leave children or pets in parked vehicles"]
    elif temp_c >= 35:
        return ["Very hot — limit outdoor exertion to early morning or evening","Drink 2–3 litres of water throughout the day"]
    elif temp_c <= 0:
        return ["🔵 FREEZING — Risk of frostbite on exposed skin","Cover all exposed skin — face, hands, ears","Watch for hypothermia signs: shivering, confusion, slurred speech"]
    elif temp_c <= 5:
        return ["Very cold — dress in warm, windproof layers"]
    return []

# ── Background Theme ─────────────────────────────────────────
BG_THEMES = {
    "sunny":  {"from": "#1a0a00", "mid": "#3d1f00", "to": "#0a0500", "accent": "#ff9d00", "particle": "sun"},
    "cloudy": {"from": "#0d1117", "mid": "#1c2333", "to": "#0d1117", "accent": "#8ba3c7", "particle": "cloud"},
    "rain":   {"from": "#030d1a", "mid": "#071a33", "to": "#030d1a", "accent": "#4facfe", "particle": "rain"},
    "storm":  {"from": "#08000f", "mid": "#1a0028", "to": "#08000f", "accent": "#b44fff", "particle": "lightning"},
    "snow":   {"from": "#050d1a", "mid": "#0d1f33", "to": "#050d1a", "accent": "#a8d8ff", "particle": "snow"},
    "fog":    {"from": "#0d0d0d", "mid": "#1a1a1a", "to": "#0d0d0d", "accent": "#c0c0c0", "particle": "fog"},
}

# ── DB Helpers ───────────────────────────────────────────────
def cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)}_{round(lon, 2)}"

def read_cache(key: str) -> Optional[dict]:
    db = get_db()
    if not db: return None
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM weather_cache WHERE cache_key=%s", (key,))
            row = cur.fetchone()
            if not row: return None
            age = datetime.now() - row["cached_at"]
            if age > timedelta(minutes=CACHE_TTL_MINUTES): return None
            row["precautions"]   = json.loads(row["precautions"] or "[]")
            row["forecast_json"] = json.loads(row["forecast_json"] or "[]")
            row["hourly_json"]   = json.loads(row["hourly_json"] or "[]")
            return row
    except: return None
    finally: db.close()

def write_cache(key: str, data: dict):
    db = get_db()
    if not db: return
    try:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO weather_cache
                  (cache_key,city,country,temperature_c,temperature_f,feels_like_c,
                   humidity,wind_speed_kmh,condition_text,condition_type,weather_icon,
                   safety_level,uv_index,precautions,forecast_json,hourly_json,cached_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON DUPLICATE KEY UPDATE
                  city=VALUES(city), country=VALUES(country),
                  temperature_c=VALUES(temperature_c), temperature_f=VALUES(temperature_f),
                  feels_like_c=VALUES(feels_like_c), humidity=VALUES(humidity),
                  wind_speed_kmh=VALUES(wind_speed_kmh), condition_text=VALUES(condition_text),
                  condition_type=VALUES(condition_type), weather_icon=VALUES(weather_icon),
                  safety_level=VALUES(safety_level), uv_index=VALUES(uv_index),
                  precautions=VALUES(precautions), forecast_json=VALUES(forecast_json),
                  hourly_json=VALUES(hourly_json), cached_at=NOW()
            """, (
                key, data["city"], data["country"],
                data["temperature_c"], data["temperature_f"], data["feels_like_c"],
                data["humidity"], data["wind_speed_kmh"],
                data["condition"], data["condition_type"], data["weather_icon"],
                data["safety_level"], data.get("uv_index"),
                json.dumps(data["precautions"]),
                json.dumps(data["forecast"]),
                json.dumps(data["hourly"]),
            ))
    except Exception as e:
        print(f"[DB] Cache write failed: {e}")
    finally:
        db.close()

def log_search(city, country, lat, lon):
    db = get_db()
    if not db: return
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO search_history (city,country,latitude,longitude) VALUES (%s,%s,%s,%s)",
                (city, country, lat, lon)
            )
    except: pass
    finally: db.close()

def log_alert(city, alert_type, msg, level):
    db = get_db()
    if not db: return
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO weather_alerts (city,alert_type,alert_msg,safety_level) VALUES (%s,%s,%s,%s)",
                (city, alert_type, msg, level)
            )
    except: pass
    finally: db.close()

# ── Parse forecast from Open-Meteo ──────────────────────────
def parse_forecast(daily: dict) -> list:
    days = []
    dates      = daily.get("time", [])
    tmax       = daily.get("temperature_2m_max", [])
    tmin       = daily.get("temperature_2m_min", [])
    codes      = daily.get("weather_code", [])
    precip     = daily.get("precipitation_sum", [])
    sunrise    = daily.get("sunrise", [])
    sunset     = daily.get("sunset", [])
    for i in range(min(7, len(dates))):
        wmo = codes[i] if i < len(codes) else 0
        ct  = WMO_CODES.get(wmo, ("Clear Sky","sunny"))
        days.append({
            "date":      dates[i],
            "tmax":      round(tmax[i], 1) if i < len(tmax) else None,
            "tmin":      round(tmin[i], 1) if i < len(tmin) else None,
            "condition": ct[0],
            "type":      ct[1],
            "icon":      WMO_ICONS.get(ct[1], "🌤️"),
            "precip_mm": round(precip[i], 1) if i < len(precip) else 0,
            "sunrise":   sunrise[i][-5:] if i < len(sunrise) else "—",
            "sunset":    sunset[i][-5:]  if i < len(sunset)  else "—",
        })
    return days

def parse_hourly(hourly: dict) -> list:
    hours = []
    times  = hourly.get("time", [])[:24]
    temps  = hourly.get("temperature_2m", [])[:24]
    codes  = hourly.get("weather_code", [])[:24]
    humid  = hourly.get("relative_humidity_2m", [])[:24]
    for i, t in enumerate(times):
        wmo = codes[i] if i < len(codes) else 0
        ct  = WMO_CODES.get(wmo, ("Clear Sky","sunny"))
        hours.append({
            "time": t[11:16],
            "temp": round(temps[i], 1) if i < len(temps) else None,
            "icon": WMO_ICONS.get(ct[1], "🌤️"),
            "type": ct[1],
            "humidity": humid[i] if i < len(humid) else None,
        })
    return hours

# ── Main Weather Endpoint ────────────────────────────────────
@app.get("/weather")
async def get_weather(lat: float, lon: float, city: str = "Unknown", country: str = ""):
    ck = cache_key(lat, lon)
    cached = read_cache(ck)
    if cached:
        # Re-attach computed fields not stored
        ct = cached["condition_type"]
        cached["alerts"]     = get_alerts(ct, float(cached["temperature_c"]), float(cached["wind_speed_kmh"]), cached.get("uv_index") or 0)
        cached["activity"]   = ACTIVITIES.get(ct, ACTIVITIES["cloudy"])
        cached["bg_theme"]   = BG_THEMES.get(ct, BG_THEMES["cloudy"])
        cached["from_cache"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
                f"weather_code,wind_speed_10m,uv_index"
                f"&hourly=temperature_2m,weather_code,relative_humidity_2m"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
                f"precipitation_sum,sunrise,sunset"
                f"&wind_speed_unit=kmh&timezone=auto&forecast_days=7"
            )
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}")

    cur  = data["current"]
    tc   = round(cur["temperature_2m"], 1)
    tf   = round(tc * 9/5 + 32, 1)
    fc   = round(cur["apparent_temperature"], 1)
    hum  = cur["relative_humidity_2m"]
    wind = round(cur["wind_speed_10m"], 1)
    wmo  = cur["weather_code"]
    uv   = cur.get("uv_index") or 0

    condition_label, condition_type = WMO_CODES.get(wmo, ("Clear Sky", "sunny"))
    safety = SAFETY_DATA.get(condition_type, SAFETY_DATA["cloudy"])
    precs  = get_temp_precautions(tc) + safety["precautions"]
    alerts = get_alerts(condition_type, tc, wind, uv)
    forecast = parse_forecast(data.get("daily", {}))
    hourly   = parse_hourly(data.get("hourly", {}))

    result = {
        "city":           city,
        "country":        country,
        "latitude":       lat,
        "longitude":      lon,
        "temperature_c":  tc,
        "temperature_f":  tf,
        "feels_like_c":   fc,
        "humidity":       hum,
        "wind_speed_kmh": wind,
        "condition":      condition_label,
        "condition_type": condition_type,
        "weather_icon":   WMO_ICONS.get(condition_type, "🌤️"),
        "safety_level":   safety["level"],
        "precautions":    precs,
        "uv_index":       uv,
        "alerts":         alerts,
        "activity":       ACTIVITIES.get(condition_type, ACTIVITIES["cloudy"]),
        "bg_theme":       BG_THEMES.get(condition_type, BG_THEMES["cloudy"]),
        "forecast":       forecast,
        "hourly":         hourly,
        "from_cache":     False,
    }

    write_cache(ck, result)
    log_search(city, country, lat, lon)
    for a in alerts:
        log_alert(city, a["type"], a["msg"], safety["level"])

    return result


@app.get("/geocode")
async def geocode(q: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json"
            )
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results", [])
        if not results:
            raise HTTPException(status_code=404, detail="City not found")
        return {"results": [{"name": r["name"], "country": r.get("country",""), "admin1": r.get("admin1",""), "latitude": r["latitude"], "longitude": r["longitude"]} for r in results[:5]]}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(limit: int = 5):
    db = get_db()
    if not db: return {"history": []}
    try:
        with db.cursor() as cur:
            cur.execute("SELECT city, country, latitude, longitude FROM search_history ORDER BY searched_at DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            # deduplicate by city
            seen, unique = set(), []
            for r in rows:
                if r["city"] not in seen:
                    seen.add(r["city"])
                    unique.append(r)
            return {"history": unique[:5]}
    except: return {"history": []}
    finally: db.close()


@app.get("/pinned")
async def get_pinned():
    db = get_db()
    if not db: return {"pinned": []}
    try:
        with db.cursor() as cur:
            cur.execute("SELECT city, country, latitude, longitude FROM pinned_cities ORDER BY pinned_at DESC")
            return {"pinned": cur.fetchall()}
    except: return {"pinned": []}
    finally: db.close()


@app.post("/pinned")
async def pin_city(city: str, country: str, lat: float, lon: float):
    db = get_db()
    if not db: raise HTTPException(status_code=503, detail="DB unavailable")
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT IGNORE INTO pinned_cities (city,country,latitude,longitude) VALUES (%s,%s,%s,%s)",
                (city, country, lat, lon)
            )
        return {"status": "pinned"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: db.close()


@app.delete("/pinned")
async def unpin_city(lat: float, lon: float):
    db = get_db()
    if not db: raise HTTPException(status_code=503, detail="DB unavailable")
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM pinned_cities WHERE latitude=%s AND longitude=%s", (round(lat,4), round(lon,4)))
        return {"status": "unpinned"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: db.close()


@app.get("/alerts/recent")
async def recent_alerts(limit: int = 10):
    db = get_db()
    if not db: return {"alerts": []}
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM weather_alerts ORDER BY triggered_at DESC LIMIT %s", (limit,))
            return {"alerts": cur.fetchall()}
    except: return {"alerts": []}
    finally: db.close()


@app.get("/health")
async def health():
    db_ok = get_db() is not None
    return {"status": "ok", "version": "2.0", "db_connected": db_ok}
