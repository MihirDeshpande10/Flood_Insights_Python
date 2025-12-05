import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
import httpx
import statistics
import pandas as pd
import tempfile
from typing import List
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI(title="Flood & Weather Insights Backend")

# Allow frontend apps (Streamlit) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Helper Functions ------------------ #

async def geocode_city(city: str):
    """Get latitude/longitude for a city."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params={"name": city, "count": 1, "language": "en"})
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Geocoding API error")
        j = r.json()
        results = j.get("results")
        if not results:
            raise HTTPException(status_code=404, detail="Location not found")
        res = results[0]
        return {
            "name": res.get("name"),
            "country": res.get("country"),
            "lat": res.get("latitude"),
            "lon": res.get("longitude")
        }

async def fetch_weather(lat: float, lon: float):
    """Fetch hourly forecast data from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,relativehumidity_2m,windspeed_10m",
        "timezone": "auto"
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="Forecast API error")
        return r.json()

def compute_rolling(values: List[float], hours: int):
    """Sum of last n hours (rolling window)."""
    if not values:
        return 0.0
    if len(values) < hours:
        return round(sum(values), 2)
    return round(sum(values[-hours:]), 2)

def compute_std(values: List[float]):
    """Standard deviation of rainfall."""
    if not values:
        return 0.0
    return statistics.pstdev(values)

def summarize_risks(rolling_24: float, temps_24: List[float], winds_24: List[float]):
    """Summarize Flood / Heat / Storm risk levels."""
    flood_threshold = 50.0
    if rolling_24 >= flood_threshold:
        flood = "High"
    elif rolling_24 >= flood_threshold * 0.6:
        flood = "Medium"
    else:
        flood = "Low"

    max_temp = max(temps_24) if temps_24 else -999
    if max_temp >= 40:
        heat = "High"
    elif max_temp >= 35:
        heat = "Medium"
    else:
        heat = "Low"

    max_wind = max(winds_24) if winds_24 else 0.0
    if max_wind >= 15:
        storm = "High"
    elif max_wind >= 8:
        storm = "Medium"
    else:
        storm = "Low"

    return {"flood": flood, "heat": heat, "storm": storm,
            "max_temp": round(max_temp,1), "max_wind": round(max_wind,1)}

def build_bilingual_advisories(risks: dict):
    """Return advisories in English, Hindi, Marathi."""
    flood = risks["flood"]
    heat = risks["heat"]
    storm = risks["storm"]

    advisory_en = []
    advisory_hi = []
    advisory_mr = []

    if flood == "High":
        advisory_en.append("High flood risk — move livestock/equipment to higher ground.")
        advisory_hi.append("उच्च बाढ़ जोखिम — पशुधन और उपकरण सुरक्षित स्थान पर ले जाएं।")
        advisory_mr.append("उच्च पूर धोका — जनावरे व उपकरणे उंच जागी हलवा.")
    elif flood == "Medium":
        advisory_en.append("Medium flood risk — inspect low-lying fields and secure valuables.")
        advisory_hi.append("मध्यम बाढ़ जोखिम — निचले क्षेत्रों की जाँच करें और सामान सुरक्षित रखें।")
        advisory_mr.append("मध्यम पूर धोका — खालच्या शेतांची तपासणी करा व वस्तू सुरक्षित ठेवा.")
    else:
        advisory_en.append("Flood risk is low — normal conditions.")

    if heat == "High":
        advisory_en.append("High heat — avoid field work during midday; stay hydrated.")
        advisory_hi.append("उच्च तापमान — दोपहर के दौरान खेत का काम न करें; पानी पिएं।")
        advisory_mr.append("उच्च ताप — दुपारच्या वेळी काम टाळा; पाणी प्या.")
    elif heat == "Medium":
        advisory_en.append("Moderate heat — take precautions during hot hours.")
        advisory_hi.append("मध्यम तापमान — गर्मी के समय सावधानी रखें।")
        advisory_mr.append("मध्यम ताप — गरम वेळेत खबरदारी घ्या.")

    if storm == "High":
        advisory_en.append("High wind risk — secure shade nets and loose equipment.")
        advisory_hi.append("उच्च हवा जोखिम — नेट और ढीले उपकरण सुरक्षित रखें।")
        advisory_mr.append("उच्च वारा धोका — जाळी आणि ढीले उपकरण सुरक्षित ठेवा.")
    elif storm == "Medium":
        advisory_en.append("Moderate winds — be cautious while working at heights.")

    return {
        "advisory_en": " ".join(advisory_en),
        "advisory_hi": " ".join(advisory_hi) if advisory_hi else " ".join(advisory_en),
        "advisory_mr": " ".join(advisory_mr) if advisory_mr else " ".join(advisory_en)
    }

async def get_full_forecast(city: str):
    """Fetch forecast + risks + advisories for a city."""
    g = await geocode_city(city)
    lat = g["lat"]; lon = g["lon"]; pretty = f"{g['name']}, {g['country']}"
    w = await fetch_weather(lat, lon)
    hourly = w.get("hourly", {})

    times = hourly.get("time", [])
    temps = [float(x) for x in hourly.get("temperature_2m", [])]
    precip = [float(x) for x in hourly.get("precipitation", [])]
    humidity = [float(x) for x in hourly.get("relativehumidity_2m", [])]
    wind = [float(x) for x in hourly.get("windspeed_10m", [])]

    rolling_24 = compute_rolling(precip, 24)
    rolling_72 = compute_rolling(precip, 72)
    std_precip = compute_std(precip)

    temps_24 = temps[-24:] if len(temps) >= 24 else temps
    winds_24 = wind[-24:] if len(wind) >= 24 else wind

    risk_summary = summarize_risks(rolling_24, temps_24, winds_24)
    advisories = build_bilingual_advisories(risk_summary)

    return {
        "location": pretty,
        "lat": lat, "lon": lon,
        "times": times,
        "temperature": temps,
        "precip": precip,
        "humidity": humidity,
        "wind": wind,
        "rolling_24": rolling_24,
        "rolling_72": rolling_72,
        "precip_std": round(std_precip, 2),
        "risk": risk_summary,
        "advisory_en": advisories["advisory_en"],
        "advisory_hi": advisories["advisory_hi"],
        "advisory_mr": advisories["advisory_mr"]
    }

# ------------------ API Endpoints ------------------ #

@app.get("/city_forecast")
async def city_forecast(city: str):
    """Get forecast + risk + advisories for a city."""
    if not city:
        raise HTTPException(status_code=400, detail="city param required")
    data = await get_full_forecast(city)
    return data

@app.get("/export_csv")
async def export_csv(city: str):
    """Export weather data as CSV for NGOs/researchers."""
    data = await get_full_forecast(city)
    df = pd.DataFrame({
        "time": data["times"],
        "temperature_C": data["temperature"],
        "precip_mm": data["precip"],
        "humidity_%": data["humidity"],
        "wind_m_s": data["wind"]
    })
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp.name, index=False)
    return FileResponse(tmp.name, filename=f"{city.replace(' ','_')}_weather.csv")

 

 