"""
Flask Frontend v2 — Rudra's Weather App
"""
from flask import Flask, render_template, request, jsonify
import httpx, os

app = Flask(__name__)
FASTAPI_BASE = os.getenv("FASTAPI_URL", "http://127.0.0.1:8001")

def proxy(path, params=None, method="GET", **kwargs):
    try:
        if method == "POST":
            r = httpx.post(f"{FASTAPI_BASE}{path}", params=params, timeout=15)
        elif method == "DELETE":
            r = httpx.delete(f"{FASTAPI_BASE}{path}", params=params, timeout=10)
        else:
            r = httpx.get(f"{FASTAPI_BASE}{path}", params=params, timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/geocode")
def geocode():
    return proxy("/geocode", {"q": request.args.get("q", "")})

@app.route("/api/weather")
def weather():
    return proxy("/weather", {
        "lat":     request.args.get("lat"),
        "lon":     request.args.get("lon"),
        "city":    request.args.get("city", "Unknown"),
        "country": request.args.get("country", ""),
    })

@app.route("/api/history")
def history():
    return proxy("/history")

@app.route("/api/pinned", methods=["GET"])
def get_pinned():
    return proxy("/pinned")

@app.route("/api/pinned", methods=["POST"])
def pin_city():
    return proxy("/pinned", {
        "city":    request.args.get("city"),
        "country": request.args.get("country",""),
        "lat":     request.args.get("lat"),
        "lon":     request.args.get("lon"),
    }, method="POST")

@app.route("/api/pinned", methods=["DELETE"])
def unpin_city():
    return proxy("/pinned", {
        "lat": request.args.get("lat"),
        "lon": request.args.get("lon"),
    }, method="DELETE")

@app.route("/api/alerts")
def alerts():
    return proxy("/alerts/recent")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
